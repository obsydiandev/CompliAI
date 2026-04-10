"""Alert dispatcher — in-app, email, Slack, webhook (T4.8).

Dispatches alerts for compliance violations.  Each channel is a no-op
when the relevant config is missing, making it safe to call in all
environments.
"""

from __future__ import annotations

import json
import logging
import smtplib
import urllib.request
from email.mime.text import MIMEText
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def dispatch_alert(
    channel: str,
    recipient: str | None,
    payload: dict[str, Any],
) -> bool:
    """
    Send an alert via the specified channel.

    Parameters
    ----------
    channel:
        "in_app" | "email" | "slack" | "webhook"
    recipient:
        Email address, Slack webhook URL, or generic webhook URL.
        Ignored for "in_app".
    payload:
        Dict with at least {"rule_name": str, "message": str, "severity": str}.

    Returns
    -------
    bool — True if dispatch succeeded (or was a no-op for in_app).
    """
    if channel == "in_app":
        logger.info(
            "[AlertDispatcher] in_app alert: rule=%s severity=%s",
            payload.get("rule_name"),
            payload.get("severity"),
        )
        return True

    if channel == "email":
        return _send_email(recipient, payload)

    if channel == "slack":
        return _send_slack(recipient, payload)

    if channel == "webhook":
        return _send_webhook(recipient, payload)

    logger.warning("[AlertDispatcher] Unknown channel: %s", channel)
    return False


# ── Channel implementations ───────────────────────────────────────────────────


def _send_email(recipient: str | None, payload: dict[str, Any]) -> bool:
    if not recipient:
        logger.warning("[AlertDispatcher] email: no recipient configured, skipping.")
        return False

    smtp_host = getattr(settings, "SMTP_HOST", "")
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASS", "")
    from_addr = getattr(settings, "EMAIL_FROM", smtp_user or "noreply@compliai.io")

    if not smtp_host:
        logger.info(
            "[AlertDispatcher] email: SMTP not configured, skipping email to %s.", recipient
        )
        return False

    subject = (
        f"[CompliAI] {payload.get('severity', 'warning').upper()} — "
        f"{payload.get('rule_name', 'Compliance Alert')}"
    )
    body = (
        f"Compliance rule violated:\n\n"
        f"Rule: {payload.get('rule_name')}\n"
        f"System: {payload.get('system_name', 'unknown')}\n"
        f"Severity: {payload.get('severity')}\n"
        f"Details: {payload.get('message')}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("[AlertDispatcher] email sent to %s", recipient)
        return True
    except Exception as exc:
        logger.error("[AlertDispatcher] email failed: %s", exc)
        return False


def _send_slack(webhook_url: str | None, payload: dict[str, Any]) -> bool:
    if not webhook_url:
        logger.warning("[AlertDispatcher] slack: no webhook URL, skipping.")
        return False

    severity_emoji = {
        "blocking": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
    }.get(payload.get("severity", "warning"), "⚠️")

    slack_payload = {
        "text": (
            f"{severity_emoji} *CompliAI Compliance Alert*\n"
            f"*Rule:* {payload.get('rule_name')}\n"
            f"*System:* {payload.get('system_name', 'unknown')}\n"
            f"*Severity:* {payload.get('severity')}\n"
            f"*Details:* {payload.get('message')}"
        )
    }
    return _post_json(webhook_url, slack_payload)


def _send_webhook(url: str | None, payload: dict[str, Any]) -> bool:
    if not url:
        logger.warning("[AlertDispatcher] webhook: no URL, skipping.")
        return False
    return _post_json(url, payload)


def _post_json(url: str, data: dict[str, Any]) -> bool:
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            logger.info("[AlertDispatcher] POST %s → %s", url, resp.status)
            return resp.status < 400
    except Exception as exc:
        logger.error("[AlertDispatcher] POST %s failed: %s", url, exc)
        return False
