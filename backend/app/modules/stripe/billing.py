"""Stripe Billing integration.

Provides helpers for:
- Creating Stripe customers
- Creating checkout sessions (subscription or one-time)
- Creating customer portal sessions
- Processing webhook events
"""

from __future__ import annotations

import logging

import stripe
from app.config import settings

logger = logging.getLogger(__name__)

# Price IDs – set in Stripe dashboard and map to environment variables if needed.
# These are looked up from config or fall back to placeholder values for testing.
PLAN_PRICE_IDS: dict[str, str] = {
    "starter": getattr(settings, "STRIPE_PRICE_STARTER", "price_starter"),
    "pro": getattr(settings, "STRIPE_PRICE_PRO", "price_pro"),
}


def _client() -> stripe.Stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_or_get_customer(org_id: str, org_name: str, email: str | None = None) -> str:
    """Create a Stripe customer for the organisation and return the customer ID."""
    _client()
    customer = stripe.Customer.create(
        name=org_name,
        email=email,
        metadata={"org_id": org_id},
    )
    return customer["id"]


def create_checkout_session(
    customer_id: str,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout session and return the session URL."""
    _client()
    price_id = PLAN_PRICE_IDS.get(plan, PLAN_PRICE_IDS["starter"])
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        subscription_data={"trial_period_days": 14},
    )
    return session["url"]


def create_portal_session(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session and return the portal URL."""
    _client()
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session["url"]


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and construct a Stripe webhook event."""
    return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)


def parse_subscription_from_event(event: stripe.Event) -> dict | None:
    """
    Extract normalised subscription info from a webhook event.

    Returns a dict with keys:
        subscription_id, customer_id, status, plan
    or None if the event is not subscription-related.
    """
    event_type = event["type"]

    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        sub = event["data"]["object"]
        plan = _plan_from_subscription(sub)
        return {
            "subscription_id": sub["id"],
            "customer_id": sub["customer"],
            "status": sub["status"],
            "plan": plan,
        }

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") != "subscription":
            return None
        return {
            "subscription_id": session.get("subscription"),
            "customer_id": session.get("customer"),
            "status": "active",
            "plan": None,  # will be resolved later via subscription lookup
        }

    return None


def _plan_from_subscription(sub: dict) -> str:
    """Infer plan name from subscription line items."""
    items = sub.get("items", {}).get("data", [])
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        for plan, pid in PLAN_PRICE_IDS.items():
            if price_id == pid:
                return plan
    return "starter"
