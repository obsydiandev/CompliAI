"""Stripe billing integration."""
import logging

logger = logging.getLogger(__name__)

PLAN_PRICE_MAP = {
    "starter": "STRIPE_PRICE_ID_STARTER",
    "professional": "STRIPE_PRICE_ID_PROFESSIONAL",
    "enterprise": "STRIPE_PRICE_ID_ENTERPRISE",
}


def _stripe():
    import stripe
    from app.config import settings
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_customer(email: str) -> str:
    stripe = _stripe()
    customer = stripe.Customer.create(email=email)
    return customer["id"]


def create_subscription(customer_id: str, price_id: str) -> dict:
    stripe = _stripe()
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
    )
    return {
        "subscription_id": subscription["id"],
        "status": subscription["status"],
        "client_secret": (
            (subscription.get("latest_invoice") or {})
            .get("payment_intent", {})
            .get("client_secret")
        ),
    }


def cancel_subscription(subscription_id: str) -> dict:
    stripe = _stripe()
    subscription = stripe.Subscription.delete(subscription_id)
    return {"subscription_id": subscription["id"], "status": subscription["status"]}


def handle_webhook(payload: bytes, sig: str) -> dict:
    import stripe
    from app.config import settings
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
        return {"event_type": event["type"], "event_id": event["id"], "processed": True}
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature", "processed": False}
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return {"error": str(e), "processed": False}
