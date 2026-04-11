"""Post-August upsell email sequence (T8.4).

Daily task: query WizardSession where payment_confirmed=True and
updated_at < now - 60 days → send re-engagement email.
"""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from app.config import settings

logger = logging.getLogger(__name__)


def _resend(to: str, subject: str, html: str) -> bool:
    try:
        import httpx

        api_key = getattr(settings, "RESEND_API_KEY", "")
        from_email = getattr(settings, "RESEND_FROM_EMAIL", "noreply@compliai.io")
        if not api_key:
            logger.warning("RESEND_API_KEY not set — skipping upsell email to %s", to)
            return False
        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception as exc:
        logger.error("Upsell email failed to %s: %s", to, exc)
        return False


@shared_task(name="app.tasks.upsell_sequence.send_upsell_emails_daily", bind=True)
def send_upsell_emails_daily(self) -> dict[str, Any]:
    """Daily task: send upsell/re-engagement emails to Lite clients >60 days post-purchase."""
    from datetime import datetime, timedelta, timezone

    from app.database import SessionLocal
    from app.models.wizard_session import WizardSession

    db = SessionLocal()
    sent = 0
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now - timedelta(days=60)

        sessions = (
            db.query(WizardSession)
            .filter(
                WizardSession.payment_confirmed.is_(True),
                WizardSession.email.isnot(None),
                WizardSession.updated_at < cutoff,
                WizardSession.data_purged_at.is_(None),  # not already purged
            )
            .all()
        )

        for session in sessions:
            try:
                system_name = session.system_name or "your AI system"
                update_url = f"{settings.FRONTEND_URL}/wizard"
                pro_url = f"{settings.FRONTEND_URL}/pricing"

                html = f"""
                <div style="font-family: sans-serif; max-width: 600px;">
                  <h2 style="color: #1a56db;">Your AI system may have changed</h2>
                  <p>Over 60 days ago you generated an Annex IV Technical File for
                     <strong>{system_name}</strong>.</p>
                  <p>Under <strong>Art. 11(2) of the EU AI Act</strong>, providers of high-risk AI
                     systems must update their Technical File whenever the system undergoes a
                     <em>substantial modification</em>.</p>
                  <p>Has your model been updated, retrained, or deployed in a new context?
                     If so, your Technical File may need updating.</p>

                  <div style="margin: 24px 0; display: flex; gap: 12px;">
                    <a href="{update_url}"
                       style="background:#1a56db;color:white;padding:12px 20px;border-radius:6px;
                              text-decoration:none;font-weight:bold;display:inline-block;margin-right:8px;">
                      Generate updated Technical File — €299
                    </a>
                    <a href="{pro_url}"
                       style="background:#f3f4f6;color:#374151;padding:12px 20px;border-radius:6px;
                              text-decoration:none;font-weight:bold;display:inline-block;border:1px solid #d1d5db;">
                      Upgrade to Pro (continuous monitoring)
                    </a>
                  </div>

                  <p style="color:#6b7280;font-size:11px;">
                    Pro plan includes automatic change detection and documentation updates
                    via GitHub/GitLab integration.
                  </p>
                </div>
                """
                if _resend(session.email, "Your AI Act Technical File may need updating", html):
                    sent += 1
            except Exception as exc:
                logger.error("Upsell email failed for session %s: %s", session.session_token, exc)

        logger.info("[UpsellSequence] Sent %d upsell emails", sent)
        return {"sent": sent}
    finally:
        db.close()
