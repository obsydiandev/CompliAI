"""Email nurturing tasks for AI Act Risk Classifier leads (Epic 19).

Sends a 3-step email sequence (D+1, D+7, D+14) to high-risk classifier leads
who provide their email address.  Uses Resend for transactional email delivery.
"""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from app.config import settings

logger = logging.getLogger(__name__)

_FROM = settings.RESEND_FROM_EMAIL if hasattr(settings, "RESEND_FROM_EMAIL") else "noreply@compliai.io"


def _send_resend_email(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend API. Returns True on success."""
    try:
        import httpx  # type: ignore

        api_key = getattr(settings, "RESEND_API_KEY", "")
        if not api_key:
            logger.warning("RESEND_API_KEY not configured — skipping email to %s", to)
            return False

        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": _FROM, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        if response.status_code not in (200, 201):
            logger.warning("Resend API error %s: %s", response.status_code, response.text)
            return False
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def _mark_step_sent(lead_id: str, step: str) -> None:
    """Record that a nurturing step has been sent."""
    try:
        from app.database import SessionLocal
        from app.models.classifier_lead import ClassifierLead

        db = SessionLocal()
        try:
            lead = db.query(ClassifierLead).filter(ClassifierLead.id == lead_id).first()
            if lead:
                sent = list(lead.nurturing_sent or [])
                if step not in sent:
                    sent.append(step)
                    lead.nurturing_sent = sent
                    db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.error("Failed to mark nurturing step %s for lead %s: %s", step, lead_id, exc)


@shared_task(name="app.tasks.email_nurturing.send_nurturing_d1", bind=True, max_retries=3)
def send_nurturing_d1(self, lead_id: str, email: str) -> dict[str, Any]:
    """D+1: 'Your AI Act risk assessment — next steps'."""
    subject = "Your AI Act Risk Classification — What to do next"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #1a56db;">Your AI Act Risk Classification</h2>
      <p>Yesterday you classified your AI system as <strong>High-Risk</strong> under EU AI Act Annex III.</p>
      <p>This means your system will require:</p>
      <ul>
        <li><strong>Annex IV Technical File</strong> — complete documentation of your system</li>
        <li><strong>Conformity assessment</strong> — before placing on the EU market</li>
        <li><strong>Registration</strong> in the EU AI database</li>
      </ul>
      <p>The deadline for Annex III systems is <strong>August 2, 2026</strong>.</p>
      <p style="margin-top: 24px;">
        <a href="{settings.FRONTEND_URL}/wizard"
           style="background: #1a56db; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          Generate your Annex IV Technical File — €299
        </a>
      </p>
      <p style="color: #6b7280; font-size: 12px; margin-top: 32px;">
        CompliAI helps you prepare the required Annex IV Technical File in under 60 minutes.
        <br>Questions? Reply to this email.
      </p>
    </div>
    """
    _send_resend_email(email, subject, html)
    _mark_step_sent(lead_id, "d1")

    # Schedule D+7
    send_nurturing_d7.apply_async(args=[lead_id, email], countdown=86400 * 6)  # 6 more days
    return {"step": "d1", "sent_to": email}


@shared_task(name="app.tasks.email_nurturing.send_nurturing_d7", bind=True, max_retries=3)
def send_nurturing_d7(self, lead_id: str, email: str) -> dict[str, Any]:
    """D+7: 'What happens to companies without Annex IV on August 2, 2026?'"""
    subject = "AI Act deadline: what happens without documentation?"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #1a56db;">What happens without Annex IV?</h2>
      <p>One week ago you identified your AI system as High-Risk under the EU AI Act.</p>
      <p>From <strong>August 2, 2026</strong>, national supervisory authorities in EU member states
         will be able to request your Technical File at any time.</p>
      <p>Without documentation:</p>
      <ul>
        <li>Your system cannot legally be placed on or continue to operate in the EU market</li>
        <li>Penalties can reach <strong>€30 million or 6% of global annual turnover</strong></li>
        <li>Your clients face secondary liability if they deploy an undocumented high-risk system</li>
      </ul>
      <p><em>We want to be honest: supervisory bodies are not fully operational yet.
         But "documentation ready when the authority appears" is the right posture.</em></p>
      <p style="margin-top: 24px;">
        <a href="{settings.FRONTEND_URL}/wizard"
           style="background: #1a56db; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          Start your Annex IV Technical File
        </a>
      </p>
    </div>
    """
    _send_resend_email(email, subject, html)
    _mark_step_sent(lead_id, "d7")

    # Schedule D+14
    send_nurturing_d14.apply_async(args=[lead_id, email], countdown=86400 * 7)
    return {"step": "d7", "sent_to": email}


@shared_task(name="app.tasks.email_nurturing.send_nurturing_d14", bind=True, max_retries=3)
def send_nurturing_d14(self, lead_id: str, email: str) -> dict[str, Any]:
    """D+14: 'Last reminder — generate your Annex IV now'."""
    subject = "Final reminder: AI Act Technical File before the deadline"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #dc2626;">Time is running out</h2>
      <p>Two weeks ago you classified your AI system as High-Risk. August 2026 is approaching.</p>
      <p>CompliAI generates a complete <strong>Annex IV Technical File</strong> in under 60 minutes:</p>
      <ul>
        <li>7-step wizard with AI-assisted drafting</li>
        <li>Covers all 9 Annex IV sections required by the AI Act</li>
        <li>Exports a print-ready PDF with mandatory disclaimer</li>
        <li>One-time fee: <strong>€299</strong></li>
      </ul>
      <p style="margin-top: 24px;">
        <a href="{settings.FRONTEND_URL}/wizard"
           style="background: #dc2626; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          Generate Annex IV — €299
        </a>
      </p>
      <p style="color: #6b7280; font-size: 12px; margin-top: 32px;">
        This is our last automated reminder. If you've already prepared your documentation, great!
        <br>If not — we're here to help.
      </p>
    </div>
    """
    _send_resend_email(email, subject, html)
    _mark_step_sent(lead_id, "d14")
    return {"step": "d14", "sent_to": email}
