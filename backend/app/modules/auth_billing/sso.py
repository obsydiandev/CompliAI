"""SSO / OIDC authentication handlers."""
import logging
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SSOProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OIDC = "oidc"


PROVIDER_CONFIG = {
    SSOProvider.GOOGLE: {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
        "scopes": "openid email profile",
    },
    SSOProvider.MICROSOFT: {
        "authorization_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me",
        "scopes": "openid email profile User.Read",
    },
}


class SSOHandler:
    def __init__(self):
        self._oidc_config: dict | None = None

    def get_authorization_url(self, provider: SSOProvider) -> str:
        config = self._get_provider_config(provider)
        client_id = self._get_client_id(provider)
        redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{provider.value}"
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": config["scopes"],
            "state": "compliai_sso",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{config['authorization_endpoint']}?{query}"

    def handle_callback(self, provider: SSOProvider, code: str) -> dict:
        config = self._get_provider_config(provider)
        client_id = self._get_client_id(provider)
        client_secret = self._get_client_secret(provider)
        redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{provider.value}"

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        resp = httpx.post(config["token_endpoint"], data=token_data, timeout=10)
        resp.raise_for_status()
        tokens = resp.json()
        access_token = tokens.get("access_token", "")

        userinfo_resp = httpx.get(
            config["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        userinfo_resp.raise_for_status()
        user_info = userinfo_resp.json()

        return {
            "provider": provider.value,
            "sub": user_info.get("sub") or user_info.get("id"),
            "email": user_info.get("email") or user_info.get("mail") or user_info.get("userPrincipalName"),
            "name": user_info.get("name") or user_info.get("displayName"),
            "access_token": access_token,
        }

    def _get_provider_config(self, provider: SSOProvider) -> dict:
        if provider == SSOProvider.OIDC:
            return self._fetch_oidc_config()
        return PROVIDER_CONFIG[provider]

    def _fetch_oidc_config(self) -> dict:
        if self._oidc_config:
            return self._oidc_config
        discovery_url = settings.OIDC_DISCOVERY_URL
        if discovery_url:
            try:
                resp = httpx.get(discovery_url, timeout=10)
                resp.raise_for_status()
                disc = resp.json()
                self._oidc_config = {
                    "authorization_endpoint": disc["authorization_endpoint"],
                    "token_endpoint": disc["token_endpoint"],
                    "userinfo_endpoint": disc.get("userinfo_endpoint", ""),
                    "scopes": "openid email profile",
                }
                return self._oidc_config
            except Exception as e:
                logger.error("OIDC discovery failed: %s", e)
        return {
            "authorization_endpoint": "",
            "token_endpoint": "",
            "userinfo_endpoint": "",
            "scopes": "openid email profile",
        }

    def _get_client_id(self, provider: SSOProvider) -> str:
        mapping = {
            SSOProvider.GOOGLE: settings.GOOGLE_CLIENT_ID,
            SSOProvider.MICROSOFT: settings.MICROSOFT_CLIENT_ID,
            SSOProvider.OIDC: settings.OIDC_CLIENT_ID,
        }
        return mapping[provider]

    def _get_client_secret(self, provider: SSOProvider) -> str:
        mapping = {
            SSOProvider.GOOGLE: settings.GOOGLE_CLIENT_SECRET,
            SSOProvider.MICROSOFT: settings.MICROSOFT_CLIENT_SECRET,
            SSOProvider.OIDC: settings.OIDC_CLIENT_SECRET,
        }
        return mapping[provider]
