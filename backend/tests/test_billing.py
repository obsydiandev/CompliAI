"""Tests for the Stripe billing module."""

from __future__ import annotations

from unittest.mock import patch

# ── Billing status logic ──────────────────────────────────────────────────────


def test_plan_price_ids_defined():
    from app.modules.stripe.billing import PLAN_PRICE_IDS

    assert "starter" in PLAN_PRICE_IDS
    assert "pro" in PLAN_PRICE_IDS


def test_parse_subscription_created_event():
    from app.modules.stripe.billing import parse_subscription_from_event

    event = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_456",
                "status": "active",
                "items": {"data": [{"price": {"id": "price_starter"}}]},
            }
        },
    }
    result = parse_subscription_from_event(event)
    assert result is not None
    assert result["subscription_id"] == "sub_123"
    assert result["customer_id"] == "cus_456"
    assert result["status"] == "active"


def test_parse_subscription_deleted_event():
    from app.modules.stripe.billing import parse_subscription_from_event

    event = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_789",
                "customer": "cus_001",
                "status": "canceled",
                "items": {"data": []},
            }
        },
    }
    result = parse_subscription_from_event(event)
    assert result is not None
    assert result["status"] == "canceled"


def test_parse_unrelated_event_returns_none():
    from app.modules.stripe.billing import parse_subscription_from_event

    event = {"type": "payment_intent.succeeded", "data": {"object": {}}}
    result = parse_subscription_from_event(event)
    assert result is None


def test_parse_checkout_session_not_subscription_returns_none():
    from app.modules.stripe.billing import parse_subscription_from_event

    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"mode": "payment", "customer": "cus_1", "subscription": None}},
    }
    result = parse_subscription_from_event(event)
    assert result is None


def test_parse_checkout_session_subscription_mode():
    from app.modules.stripe.billing import parse_subscription_from_event

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "mode": "subscription",
                "customer": "cus_xyz",
                "subscription": "sub_new",
            }
        },
    }
    result = parse_subscription_from_event(event)
    assert result is not None
    assert result["customer_id"] == "cus_xyz"
    assert result["subscription_id"] == "sub_new"
    assert result["status"] == "active"


def test_plan_from_subscription_unknown_price():
    from app.modules.stripe.billing import _plan_from_subscription

    sub = {"items": {"data": [{"price": {"id": "price_unknown"}}]}}
    plan = _plan_from_subscription(sub)
    assert plan == "starter"  # fallback


def test_plan_from_subscription_empty_items():
    from app.modules.stripe.billing import _plan_from_subscription

    sub = {"items": {"data": []}}
    plan = _plan_from_subscription(sub)
    assert plan == "starter"


# ── create_or_get_customer ────────────────────────────────────────────────────


@patch("app.modules.stripe.billing.stripe")
def test_create_or_get_customer_calls_stripe(mock_stripe):
    from app.modules.stripe.billing import create_or_get_customer

    mock_stripe.Customer.create.return_value = {"id": "cus_new"}
    result = create_or_get_customer("org-1", "Test Org", "admin@test.com")
    assert result == "cus_new"
    mock_stripe.Customer.create.assert_called_once()


# ── create_checkout_session ───────────────────────────────────────────────────


@patch("app.modules.stripe.billing.stripe")
def test_create_checkout_session(mock_stripe):
    from app.modules.stripe.billing import create_checkout_session

    mock_stripe.checkout.Session.create.return_value = {"url": "https://checkout.stripe.com/pay/x"}
    url = create_checkout_session(
        customer_id="cus_1",
        plan="starter",
        success_url="http://localhost:3000/success",
        cancel_url="http://localhost:3000/cancel",
    )
    assert url == "https://checkout.stripe.com/pay/x"


# ── create_portal_session ─────────────────────────────────────────────────────


@patch("app.modules.stripe.billing.stripe")
def test_create_portal_session(mock_stripe):
    from app.modules.stripe.billing import create_portal_session

    mock_stripe.billing_portal.Session.create.return_value = {
        "url": "https://billing.stripe.com/p/x"
    }
    url = create_portal_session("cus_1", "http://localhost:3000/billing")
    assert "stripe.com" in url
