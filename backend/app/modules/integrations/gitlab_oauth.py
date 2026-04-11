"""GitLab OAuth 2.0 Authorization Code flow helper (T3.2).

Complements the existing PAT-based ``gitlab_connector`` with a proper
OAuth 2.0 flow so users can connect their GitLab account without creating
a Personal Access Token manually.

Required settings
-----------------
GITLAB_OAUTH_CLIENT_ID     — Application ID from GitLab → User Settings → Applications
GITLAB_OAUTH_CLIENT_SECRET — Secret generated when creating the GitLab OAuth app
GITLAB_OAUTH_BASE_URL      — GitLab instance base URL (default: https://gitlab.com)
GITLAB_OAUTH_REDIRECT_URI  — Must match the URI registered in the GitLab application

Scopes requested: ``read_user read_api read_repository``
"""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

_DEFAULT_BASE = "https://gitlab.com"
_SCOPES = "read_user read_api read_repository"


def _base_url() -> str:
    return (getattr(settings, "GITLAB_OAUTH_BASE_URL", "") or _DEFAULT_BASE).rstrip("/")


def build_auth_url(state: str, redirect_uri: str | None = None) -> str:
    """Return the GitLab authorization URL the user should be redirected to."""
    client_id = getattr(settings, "GITLAB_OAUTH_CLIENT_ID", "")
    if not client_id:
        raise ValueError("GITLAB_OAUTH_CLIENT_ID is not configured")

    params: dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri or getattr(settings, "GITLAB_OAUTH_REDIRECT_URI", ""),
        "response_type": "code",
        "state": state,
        "scope": _SCOPES,
    }
    return f"{_base_url()}/oauth/authorize?{urlencode(params)}"


def generate_state() -> str:
    """Generate a cryptographically random OAuth state token."""
    return secrets.token_urlsafe(32)


async def exchange_code(code: str, redirect_uri: str | None = None) -> dict[str, Any]:
    """Exchange an authorization code for an access token.

    Returns the full token response dict (access_token, token_type, scope, …).
    """
    client_id = getattr(settings, "GITLAB_OAUTH_CLIENT_ID", "")
    client_secret = getattr(settings, "GITLAB_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("GITLAB_OAUTH_CLIENT_ID / GITLAB_OAUTH_CLIENT_SECRET not configured")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri or getattr(settings, "GITLAB_OAUTH_REDIRECT_URI", ""),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_base_url()}/oauth/token",
            data=payload,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_user(access_token: str) -> dict[str, Any]:
    """Return basic GitLab user info for the given access token."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base_url()}/api/v4/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()
    return {
        "id": data.get("id"),
        "username": data.get("username"),
        "name": data.get("name"),
        "email": data.get("email"),
        "avatar_url": data.get("avatar_url"),
        "web_url": data.get("web_url"),
    }
