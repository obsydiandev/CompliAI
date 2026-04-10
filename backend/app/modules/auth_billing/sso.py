"""SSO / OIDC helper module (Epic 7 — E7-US1).

Supports three providers:
  - google      → accounts.google.com
  - microsoft   → login.microsoftonline.com/{tenant}/v2.0
  - oidc        → any provider with a discovery URL (Okta, Auth0, …)

Flow (Authorization Code):
  1. Frontend calls  GET /api/v1/sso/{provider}/authorize?redirect_uri=…
     → backend returns {"auth_url": "…"}
  2. Frontend redirects the browser to auth_url.
  3. Provider redirects back to the frontend callback page with ?code=…&state=…
  4. Frontend calls  POST /api/v1/sso/{provider}/callback  {"code": …, "redirect_uri": …}
     → backend exchanges code for tokens, creates/links user, returns JWT.
"""

from __future__ import annotations

import secrets
import uuid
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

# ── Provider metadata ─────────────────────────────────────────────────────────

_GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
_MICROSOFT_DISCOVERY = (
    "https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
)

# Static well-known endpoints (avoids a network call in tests)
PROVIDER_ENDPOINTS: dict[str, dict[str, str]] = {
    "google": {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
    },
    "microsoft": {
        "authorization_endpoint": (
            "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        ),
        "token_endpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "userinfo_endpoint": "https://graph.microsoft.com/oidc/userinfo",
    },
}


def _provider_config(provider: str) -> dict[str, str]:
    """Return endpoint config for the given provider, substituting tenant where needed."""
    if provider not in ("google", "microsoft", "oidc"):
        raise ValueError(f"Unsupported SSO provider: {provider}")

    if provider == "oidc":
        # For generic OIDC we need the discovery document at runtime.
        # In tests this will be mocked.
        raise NotImplementedError(
            "Generic OIDC discovery requires a runtime fetch — use fetch_oidc_config()."
        )

    cfg = dict(PROVIDER_ENDPOINTS[provider])
    if provider == "microsoft":
        tenant = settings.SSO_MICROSOFT_TENANT_ID or "common"
        cfg = {k: v.format(tenant=tenant) for k, v in cfg.items()}
    return cfg


async def fetch_oidc_config(discovery_url: str) -> dict[str, str]:
    """Fetch and return the OIDC discovery document (for generic/Okta providers)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        doc = resp.json()
    return {
        "authorization_endpoint": doc["authorization_endpoint"],
        "token_endpoint": doc["token_endpoint"],
        "userinfo_endpoint": doc.get("userinfo_endpoint", ""),
    }


def _client_credentials(provider: str) -> tuple[str, str]:
    """Return (client_id, client_secret) for the given provider."""
    if provider == "google":
        return settings.SSO_GOOGLE_CLIENT_ID, settings.SSO_GOOGLE_CLIENT_SECRET
    if provider == "microsoft":
        return settings.SSO_MICROSOFT_CLIENT_ID, settings.SSO_MICROSOFT_CLIENT_SECRET
    return settings.SSO_OIDC_CLIENT_ID, settings.SSO_OIDC_CLIENT_SECRET


def build_auth_url(
    provider: str,
    redirect_uri: str,
    state: str,
    endpoints: dict[str, str] | None = None,
) -> str:
    """Build the OAuth2 authorization URL for the given provider.

    ``endpoints`` can override the defaults (useful for generic OIDC / tests).
    """
    if endpoints is None:
        endpoints = _provider_config(provider)

    client_id, _ = _client_credentials(provider)
    scopes = "openid email profile"

    params: dict[str, str] = {
        "client_id": client_id,
        "response_type": "code",
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": state,
        "access_type": "online",
    }
    if provider == "microsoft":
        params["response_mode"] = "query"

    return endpoints["authorization_endpoint"] + "?" + urlencode(params)


async def exchange_code_for_tokens(
    provider: str,
    code: str,
    redirect_uri: str,
    endpoints: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Exchange an authorization code for access + id tokens.

    Returns the raw token response dict.
    """
    if endpoints is None:
        endpoints = _provider_config(provider)

    client_id, client_secret = _client_credentials(provider)

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            endpoints["token_endpoint"],
            data=payload,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_userinfo(
    access_token: str,
    provider: str,
    endpoints: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch the OIDC userinfo for the authenticated user."""
    if endpoints is None:
        endpoints = _provider_config(provider)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            endpoints["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def extract_user_claims(userinfo: dict[str, Any], provider: str) -> dict[str, str]:
    """Extract normalised user claims (email, name, subject) from a userinfo dict."""
    # All OIDC providers return "sub"; email and name vary slightly.
    email = userinfo.get("email") or ""
    name = (
        userinfo.get("name")
        or f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip()
        or email.split("@")[0]
    )
    sub = userinfo.get("sub") or ""
    return {"email": email.lower(), "full_name": name, "sub": sub}


def generate_state(redirect_after: str = "/dashboard") -> str:
    """Generate a random state string carrying the post-login redirect target."""
    token = secrets.token_urlsafe(32)
    # Encode redirect_after into the state so the callback knows where to go.
    # We keep it simple: base64url-encoded JSON is overkill; we use a separator.
    return f"{token}|{redirect_after}"


def parse_state(state: str) -> tuple[str, str]:
    """Split state back into (token, redirect_after)."""
    if "|" in state:
        token, redirect_after = state.split("|", 1)
        return token, redirect_after
    return state, "/dashboard"
