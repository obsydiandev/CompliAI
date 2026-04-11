"""Celery tasks for Wizard session reminders (Epic 0).

- send_wizard_reminder: 24h after session creation if not completed, send resume link
- send_wizard_expiry_warning: 3 days before expiry (day 4 of 7) if not paid
- send_post_purchase_email: immediately after Stripe webhook confirms payment
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
            logger.warning("RESEND_API_KEY not set — skipping email to %s", to)
            return False

        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception as exc:
        logger.error("Email send failed to %s: %s", to, exc)
        return False


@shared_task(name="app.tasks.wizard_reminders.send_wizard_reminders_daily", bind=True)
def send_wizard_reminders_daily(self) -> dict[str, Any]:
    """Daily task: send resume reminders for incomplete wizard sessions.

    Finds sessions that are:
    - created >24h ago and <6 days ago
    - not paid
    - have an email address
    """
    from datetime import datetime, timedelta, timezone

    from app.database import SessionLocal
    from app.models.wizard_session import WizardSession

    db = SessionLocal()
    reminded = 0
    try:
        now = datetime.now(timezone.utc)
        reminder_window_start = now - timedelta(days=6)
        reminder_window_end = now - timedelta(hours=24)

        sessions = (
            db.query(WizardSession)
            .filter(
                WizardSession.payment_confirmed.is_(False),
                WizardSession.email.isnot(None),
                WizardSession.created_at >= reminder_window_start.replace(tzinfo=None),
                WizardSession.created_at <= reminder_window_end.replace(tzinfo=None),
                WizardSession.expires_at > now.replace(tzinfo=None),
            )
            .all()
        )

        for session in sessions:
            try:
                resume_url = f"{settings.FRONTEND_URL}/wizard/{session.session_token}"
                now_naive = now.replace(tzinfo=None)
                days_left = max(0, (session.expires_at - now_naive).days) if session.expires_at else 3
                html = f"""
                <div style="font-family: sans-serif; max-width: 600px;">
                  <h2>Your Annex IV Technical File is waiting</h2>
                  <p>You started a Technical File for <strong>{session.system_name or 'your AI system'}</strong>
                     but haven't finished yet.</p>
                  <p>Your session expires in <strong>{days_left} day(s)</strong>.</p>
                  <p><a href="{resume_url}"
                        style="background:#1a56db;color:white;padding:12px 24px;border-radius:6px;
                               text-decoration:none;font-weight:bold;">
                    Continue Technical File
                  </a></p>
                  <p style="color:#6b7280;font-size:11px;">
                    Generating your Annex IV Technical File takes under 60 minutes and costs €299.
                  </p>
                </div>
                """
                if _resend(session.email, "Your AI Act Technical File is waiting", html):
                    reminded += 1
            except Exception as exc:
                logger.error("Reminder failed for session %s: %s", session.session_token, exc)

        logger.info("[WizardReminders] Sent %d reminders", reminded)
        return {"reminded": reminded}
    finally:
        db.close()


@shared_task(name="app.tasks.wizard_reminders.send_post_purchase_email", bind=True)
def send_post_purchase_email(self, session_token: str) -> dict[str, Any]:
    """Send the post-purchase '3 next steps' email after Stripe payment confirmation."""
    from app.database import SessionLocal
    from app.models.wizard_session import WizardSession

    db = SessionLocal()
    try:
        session = db.query(WizardSession).filter(
            WizardSession.session_token == session_token
        ).first()

        if not session or not session.email:
            return {"skipped": True, "reason": "no email"}

        export_url = f"{settings.FRONTEND_URL}/wizard/{session_token}/export"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px;">
          <h2 style="color: #1a56db;">Your Annex IV Technical File is ready to export 🎉</h2>
          <p>Thank you for your purchase! Your Technical File for
             <strong>{session.system_name or 'your AI system'}</strong> is now ready to export.</p>

          <h3>3 next steps after downloading your PDF:</h3>
          <ol>
            <li><strong>Legal review</strong> — Have a lawyer specialising in AI/tech law review
                the documentation before submission to any authority.</li>
            <li><strong>ML Lead verification</strong> — Confirm all technical details with your
                ML engineer or data scientist who knows the model.</li>
            <li><strong>Keep it updated</strong> — Art. 11(2) requires updating the Technical File
                whenever your AI system undergoes a substantial modification.</li>
          </ol>

          <p style="margin-top: 24px;">
            <a href="{export_url}"
               style="background:#1a56db;color:white;padding:12px 24px;border-radius:6px;
                      text-decoration:none;font-weight:bold;">
              Download your PDF
            </a>
          </p>
          <p style="color:#6b7280;font-size:11px;margin-top:24px;">
            Questions about the AI Act? Reply to this email.
          </p>
        </div>
        """
        _resend(session.email, "Your Annex IV Technical File is ready", html)
        return {"sent_to": session.email}
    finally:
        db.close()
