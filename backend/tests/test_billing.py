"""Tests for billing module (all Stripe calls mocked)."""
import pytest
from unittest.mock import MagicMock, patch


def test_billing_module_import():
    from app.modules.auth_billing import billing
    assert billing is not None


def test_customer_creation():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Customer.create.return_value = {"id": "cus_test123"}
        from app.modules.auth_billing.billing import create_customer
        result = create_customer("test@example.com")
        assert result == "cus_test123"
        mock_stripe.Customer.create.assert_called_once_with(email="test@example.com")


def test_customer_id_returned():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Customer.create.return_value = {"id": "cus_abc456"}
        from app.modules.auth_billing.billing import create_customer
        customer_id = create_customer("user@test.com")
        assert customer_id.startswith("cus_")


def test_subscription_creation():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Subscription.create.return_value = {
            "id": "sub_test456",
            "status": "incomplete",
            "latest_invoice": {"payment_intent": {"client_secret": "secret_xyz"}},
        }
        from app.modules.auth_billing.billing import create_subscription
        result = create_subscription("cus_test123", "price_starter")
        assert result["subscription_id"] == "sub_test456"
        assert result["status"] == "incomplete"


def test_subscription_id_returned():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Subscription.create.return_value = {
            "id": "sub_abc",
            "status": "active",
            "latest_invoice": None,
        }
        from app.modules.auth_billing.billing import create_subscription
        result = create_subscription("cus_abc", "price_pro")
        assert "subscription_id" in result


def test_subscription_cancellation():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Subscription.delete.return_value = {"id": "sub_test456", "status": "canceled"}
        from app.modules.auth_billing.billing import cancel_subscription
        result = cancel_subscription("sub_test456")
        assert result["status"] == "canceled"


def test_webhook_handling_success():
    mock_event = {"type": "customer.subscription.updated", "id": "evt_123"}
    with patch("stripe.Webhook.construct_event", return_value=mock_event), \
         patch("stripe.api_key", "sk_test"):
        from app.modules.auth_billing.billing import handle_webhook
        result = handle_webhook(b"payload", "sig_header")
        assert result["processed"] is True
        assert result["event_type"] == "customer.subscription.updated"


def test_webhook_invalid_signature():
    import stripe
    with patch("stripe.Webhook.construct_event", side_effect=stripe.error.SignatureVerificationError("bad sig", "sig")):
        from app.modules.auth_billing.billing import handle_webhook
        result = handle_webhook(b"payload", "bad_sig")
        assert result["processed"] is False
        assert "error" in result


def test_plan_tiers():
    from app.modules.auth_billing.billing import PLAN_PRICE_MAP
    assert "starter" in PLAN_PRICE_MAP
    assert "professional" in PLAN_PRICE_MAP
    assert "enterprise" in PLAN_PRICE_MAP


def test_stripe_mock_behavior():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Customer.create.return_value = {"id": "cus_mock"}
        from app.modules.auth_billing.billing import create_customer
        _ = create_customer("mock@test.com")
        assert mock_stripe.Customer.create.called


def test_webhook_signature_field():
    mock_event = {"type": "invoice.paid", "id": "evt_456"}
    with patch("stripe.Webhook.construct_event", return_value=mock_event), \
         patch("stripe.api_key", "sk_test"):
        from app.modules.auth_billing.billing import handle_webhook
        result = handle_webhook(b"data", "t=123,v1=abc")
        assert result["event_id"] == "evt_456"


def test_cancel_subscription_calls_stripe():
    with patch("app.modules.auth_billing.billing._stripe") as mock_stripe_fn:
        mock_stripe = MagicMock()
        mock_stripe_fn.return_value = mock_stripe
        mock_stripe.Subscription.delete.return_value = {"id": "sub_xyz", "status": "canceled"}
        from app.modules.auth_billing.billing import cancel_subscription
        cancel_subscription("sub_xyz")
        mock_stripe.Subscription.delete.assert_called_once_with("sub_xyz")
