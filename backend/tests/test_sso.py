"""Tests for SSO module (20+ tests)."""
import pytest
from unittest.mock import MagicMock, patch

from app.modules.auth_billing.sso import SSOProvider, SSOHandler


def test_sso_module_import():
    from app.modules.auth_billing import sso
    assert sso is not None


def test_sso_provider_enum():
    assert SSOProvider.GOOGLE == "google"
    assert SSOProvider.MICROSOFT == "microsoft"
    assert SSOProvider.OIDC == "oidc"


def test_google_provider():
    provider = SSOProvider("google")
    assert provider == SSOProvider.GOOGLE


def test_microsoft_provider():
    provider = SSOProvider("microsoft")
    assert provider == SSOProvider.MICROSOFT


def test_oidc_provider():
    provider = SSOProvider("oidc")
    assert provider == SSOProvider.OIDC


def test_sso_handler_init():
    handler = SSOHandler()
    assert handler is not None


def test_authorization_url_generation_google():
    handler = SSOHandler()
    url = handler.get_authorization_url(SSOProvider.GOOGLE)
    assert "accounts.google.com" in url
    assert "response_type=code" in url


def test_authorization_url_generation_microsoft():
    handler = SSOHandler()
    url = handler.get_authorization_url(SSOProvider.MICROSOFT)
    assert "microsoftonline.com" in url
    assert "response_type=code" in url


def test_google_auth_url_contains_client_id():
    handler = SSOHandler()
    url = handler.get_authorization_url(SSOProvider.GOOGLE)
    assert "client_id" in url


def test_microsoft_auth_url_contains_scope():
    handler = SSOHandler()
    url = handler.get_authorization_url(SSOProvider.MICROSOFT)
    assert "scope" in url


def test_provider_enum_values():
    values = [p.value for p in SSOProvider]
    assert "google" in values
    assert "microsoft" in values
    assert "oidc" in values


def test_sso_handler_with_settings():
    from app.config import settings
    handler = SSOHandler()
    # Should initialize without error regardless of settings
    assert handler is not None


def test_callback_handling_mock():
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "test_token", "id_token": "id_token"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_userinfo_resp = MagicMock()
    mock_userinfo_resp.json.return_value = {
        "sub": "12345",
        "email": "test@example.com",
        "name": "Test User",
    }
    mock_userinfo_resp.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_token_resp), \
         patch("httpx.get", return_value=mock_userinfo_resp):
        handler = SSOHandler()
        result = handler.handle_callback(SSOProvider.GOOGLE, "test_code")
        assert result["email"] == "test@example.com"
        assert result["provider"] == "google"


def test_sso_providers_list():
    providers = [p.value for p in SSOProvider]
    assert len(providers) == 3


def test_sso_module_structure():
    from app.modules.auth_billing.sso import SSOHandler, SSOProvider, PROVIDER_CONFIG
    assert isinstance(PROVIDER_CONFIG, dict)
    assert SSOProvider.GOOGLE in PROVIDER_CONFIG
    assert SSOProvider.MICROSOFT in PROVIDER_CONFIG


def test_handler_callback_structure():
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "tok"}
    mock_token_resp.raise_for_status = MagicMock()
    mock_userinfo_resp = MagicMock()
    mock_userinfo_resp.json.return_value = {"sub": "uid", "email": "u@test.com", "name": "User"}
    mock_userinfo_resp.raise_for_status = MagicMock()
    with patch("httpx.post", return_value=mock_token_resp), \
         patch("httpx.get", return_value=mock_userinfo_resp):
        handler = SSOHandler()
        result = handler.handle_callback(SSOProvider.MICROSOFT, "code123")
        assert "provider" in result
        assert "email" in result
        assert "sub" in result


def test_sso_error_handling():
    with patch("httpx.post", side_effect=Exception("Network error")):
        handler = SSOHandler()
        with pytest.raises(Exception):
            handler.handle_callback(SSOProvider.GOOGLE, "bad_code")


def test_provider_discovery():
    from app.modules.auth_billing.sso import PROVIDER_CONFIG, SSOProvider
    google_config = PROVIDER_CONFIG[SSOProvider.GOOGLE]
    assert "authorization_endpoint" in google_config
    assert "token_endpoint" in google_config
    assert "userinfo_endpoint" in google_config


def test_token_exchange_mock():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "at_123", "id_token": "it_456"}
    mock_resp.raise_for_status = MagicMock()
    mock_ui_resp = MagicMock()
    mock_ui_resp.json.return_value = {"sub": "abc", "email": "a@b.com", "name": "A B"}
    mock_ui_resp.raise_for_status = MagicMock()
    with patch("httpx.post", return_value=mock_resp), \
         patch("httpx.get", return_value=mock_ui_resp):
        handler = SSOHandler()
        result = handler.handle_callback(SSOProvider.GOOGLE, "exchange_code")
        assert result["access_token"] == "at_123"


def test_user_info_extraction():
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "tok_xyz"}
    mock_token_resp.raise_for_status = MagicMock()
    mock_ui = MagicMock()
    mock_ui.json.return_value = {
        "sub": "user_sub_123",
        "email": "extract@test.com",
        "name": "Extract User",
    }
    mock_ui.raise_for_status = MagicMock()
    with patch("httpx.post", return_value=mock_token_resp), \
         patch("httpx.get", return_value=mock_ui):
        handler = SSOHandler()
        info = handler.handle_callback(SSOProvider.GOOGLE, "some_code")
        assert info["sub"] == "user_sub_123"
        assert info["name"] == "Extract User"


def test_oidc_auth_url_fallback():
    handler = SSOHandler()
    # Without OIDC discovery URL configured, should handle gracefully
    url = handler.get_authorization_url(SSOProvider.OIDC)
    # URL may be empty but should not raise
    assert isinstance(url, str)
