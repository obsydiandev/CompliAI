"""Stripe Billing endpoints.

Provides:
- POST /billing/checkout   → create checkout session
- POST /billing/portal     → create customer portal session
- POST /billing/webhook    → Stripe webhook handler
- GET  /billing/status     → current subscription status
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_active_user, get_org_context
from app.config import settings
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.modules.stripe import billing as stripe_billing

logger = logging.getLogger(__name__)
router = APIRouter()


class CheckoutRequest(BaseModel):
    org_id: str
    plan: str = "starter"


class PortalRequest(BaseModel):
    org_id: str


# ── Checkout ──────────────────────────────────────────────────────────────────


@router.post("/checkout")
def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session and return the redirect URL."""
    org = db.query(Organization).filter(Organization.id == body.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Ensure there's a Stripe customer for the org
    if not org.stripe_customer_id:
        customer_id = stripe_billing.create_or_get_customer(
            org_id=str(org.id),
            org_name=org.name,
            email=current_user.email,
        )
        org.stripe_customer_id = customer_id
        db.commit()

    success_url = f"{settings.FRONTEND_URL}/dashboard/billing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/dashboard/billing"

    url = stripe_billing.create_checkout_session(
        customer_id=org.stripe_customer_id,
        plan=body.plan,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"url": url}


# ── Portal ────────────────────────────────────────────────────────────────────


@router.post("/portal")
def create_portal(
    body: PortalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Customer Portal session."""
    org = db.query(Organization).filter(Organization.id == body.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if not org.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Please start a subscription first.",
        )

    return_url = f"{settings.FRONTEND_URL}/billing"
    url = stripe_billing.create_portal_session(
        customer_id=org.stripe_customer_id,
        return_url=return_url,
    )
    return {"url": url}


# ── Webhook ───────────────────────────────────────────────────────────────────


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()

    if not settings.STRIPE_WEBHOOK_SECRET:
        # In development without a webhook secret, skip verification
        logger.warning("STRIPE_WEBHOOK_SECRET not set — skipping webhook signature verification")
        import json as _json

        try:
            event = _json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payload") from None
    else:
        try:
            event = stripe_billing.construct_webhook_event(payload, stripe_signature or "")
        except Exception as exc:
            logger.warning("Webhook signature verification failed: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    sub_info = stripe_billing.parse_subscription_from_event(event)
    if sub_info:
        _process_subscription_event(db, sub_info)

    # Handle one-time Lite payment (checkout.session.completed with mode=payment)
    event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)
    if event_type == "checkout.session.completed":
        session_obj = (event.get("data", {}).get("object", {})
                       if isinstance(event, dict) else event["data"]["object"])
        if session_obj.get("mode") == "payment":
            _process_lite_payment(db, session_obj)

    return {"received": True}


def _process_subscription_event(db: Session, sub_info: dict) -> None:
    """Update organisation subscription status from a parsed webhook event."""
    org = (
        db.query(Organization)
        .filter(Organization.stripe_customer_id == sub_info["customer_id"])
        .first()
    )
    if not org:
        logger.warning("No org found for Stripe customer %s", sub_info["customer_id"])
        return

    org.stripe_subscription_id = sub_info["subscription_id"]
    org.stripe_subscription_status = sub_info["status"]
    if sub_info.get("plan"):
        org.plan = sub_info["plan"]

    # If subscription is active, clear the trial so the subscription takes effect
    if sub_info["status"] in ("active", "trialing"):
        org.trial_ends_at = None

    db.commit()
    logger.info(
        "Updated org %s subscription: %s / %s",
        org.id,
        sub_info["status"],
        sub_info.get("plan", "?"),
    )


def _process_lite_payment(db: Session, session_obj: dict) -> None:
    """Mark a WizardSession as paid after a one-time Stripe checkout.session.completed."""
    from app.models.wizard_session import WizardSession

    wizard_token = session_obj.get("metadata", {}).get("wizard_token")
    if not wizard_token:
        return

    wizard_session = (
        db.query(WizardSession)
        .filter(WizardSession.session_token == wizard_token)
        .first()
    )
    if not wizard_session:
        logger.warning("No wizard session found for token %s", wizard_token)
        return

    wizard_session.payment_confirmed = True
    wizard_session.stripe_checkout_session_id = session_obj.get("id")
    wizard_session.stripe_payment_intent_id = session_obj.get("payment_intent")
    db.commit()
    logger.info("Lite payment confirmed for wizard session %s", wizard_token)

    # Send post-purchase email
    if wizard_session.email:
        try:
            from app.tasks.wizard_reminders import send_post_purchase_email

            send_post_purchase_email.delay(wizard_token)
        except Exception as exc:
            logger.warning("Failed to schedule post-purchase email: %s", exc)


# ── Status ────────────────────────────────────────────────────────────────────


@router.get("/status/{org_id}")
def billing_status(
    org_id: uuid.UUID,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Return the billing status of an organisation."""
    from datetime import UTC, datetime

    org = ctx.current_org
    now = datetime.now(UTC).replace(tzinfo=None)

    has_active_subscription = org.stripe_subscription_status in ("active", "trialing")
    trial_active = bool(org.trial_ends_at and org.trial_ends_at > now)
    trial_days_remaining: int | None = None
    if org.trial_ends_at:
        delta = org.trial_ends_at - now
        trial_days_remaining = max(0, delta.days)

    return {
        "org_id": str(org.id),
        "plan": org.plan,
        "stripe_subscription_status": org.stripe_subscription_status,
        "has_active_subscription": has_active_subscription,
        "trial_active": trial_active,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        "trial_days_remaining": trial_days_remaining,
        "has_billing_access": has_active_subscription or trial_active,
    }
