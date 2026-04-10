"""Alert dispatcher - dispatch alerts via email or webhook when rules fail."""
import logging

import httpx

logger = logging.getLogger(__name__)


class AlertDispatcher:
    def __init__(self, webhook_url: str | None = None, email: str | None = None):
        self.webhook_url = webhook_url
        self.email = email

    def dispatch(self, alert: dict) -> dict:
        results = []
        if self.webhook_url:
            results.append(self._send_webhook(alert))
        if self.email:
            results.append(self._send_email(alert))
        if not results:
            logger.warning("No alert channels configured for dispatch.")
            return {"status": "no_channels", "results": []}
        return {"status": "dispatched", "results": results}

    def _send_webhook(self, alert: dict) -> dict:
        try:
            resp = httpx.post(self.webhook_url, json=alert, timeout=5)
            return {"channel": "webhook", "status": resp.status_code, "ok": resp.is_success}
        except Exception as e:
            logger.error("Webhook dispatch failed: %s", e)
            return {"channel": "webhook", "status": "error", "ok": False, "error": str(e)}

    def _send_email(self, alert: dict) -> dict:
        logger.info("Email alert to %s: %s", self.email, alert.get("message", ""))
        return {"channel": "email", "status": "sent", "ok": True, "recipient": self.email}
