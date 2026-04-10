"""SSO / OIDC API endpoints (Epic 7 — E7-US1).

GET  /sso/providers                        — list enabled SSO providers
GET  /sso/{provider}/authorize             — get authorization URL (pass redirect_uri)
POST /sso/{provider}/callback              — exchange code → JWT

Supports: google | microsoft | oidc (generic, e.g. Okta)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.config import settings
from app.database import get_db
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.modules.auth_billing.auth import create_access_token
from app.modules.auth_billing.sso import (
    build_auth_url,
    exchange_code_for_tokens,
    extract_user_claims,
    fetch_oidc_config,
    fetch_userinfo,
    generate_state,
    parse_state,
)

router = APIRouter()

# ── Helpers ───────────────────────────────────────────────────────────────────

_SUPPORTED = {"google", "microsoft", "oidc"}


def _provider_enabled(provider: str) -> bool:
    if provider == "google":
        return bool(settings.SSO_GOOGLE_CLIENT_ID)
    if provider == "microsoft":
        return bool(settings.SSO_MICROSOFT_CLIENT_ID)
    if provider == "oidc":
        return bool(settings.SSO_OIDC_CLIENT_ID and settings.SSO_OIDC_DISCOVERY_URL)
    return False


async def _get_endpoints(provider: str) -> dict[str, str]:
    from app.modules.auth_billing.sso import PROVIDER_ENDPOINTS, _provider_config

    if provider == "oidc":
        return await fetch_oidc_config(settings.SSO_OIDC_DISCOVERY_URL)
    return _provider_config(provider)


def _get_or_create_sso_user(
    db: Session,
    email: str,
    full_name: str,
    sub: str,
    provider: str,
) -> User:
    """Find existing user by SSO subject or email; create one if needed."""
    # 1. Lookup by SSO subject (most reliable)
    user = (
        db.query(User)
        .filter(User.sso_provider == provider, User.sso_subject == sub)
        .first()
    )
    if user:
        return user

    # 2. Lookup by email (link existing password-based account)
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.sso_provider = provider
        user.sso_subject = sub
        db.commit()
        db.refresh(user)
        return user

    # 3. Create new user + personal org
    from slugify import slugify

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=None,
        full_name=full_name,
        sso_provider=provider,
        sso_subject=sub,
        is_active=True,
    )
    db.add(user)
    db.flush()

    base_slug = slugify(full_name or email.split("@")[0])
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        id=uuid.uuid4(),
        name=f"{full_name or email.split('@')[0]}'s Workspace",
        slug=slug,
        plan="starter",
        trial_ends_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=14),
    )
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=user.id,
        role="admin",
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────


class SSOProviderInfo(BaseModel):
    provider: str
    label: str
    enabled: bool


class AuthorizeResponse(BaseModel):
    auth_url: str
    state: str


class CallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class CallbackResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    redirect_to: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/providers", response_model=list[SSOProviderInfo])
def list_providers():
    """List all configured SSO providers (enabled / disabled)."""
    return [
        SSOProviderInfo(provider="google", label="Google", enabled=_provider_enabled("google")),
        SSOProviderInfo(
            provider="microsoft", label="Microsoft / Azure AD", enabled=_provider_enabled("microsoft")
        ),
        SSOProviderInfo(
            provider="oidc",
            label="OIDC (Okta / Auth0 / custom)",
            enabled=_provider_enabled("oidc"),
        ),
    ]


@router.get("/{provider}/authorize", response_model=AuthorizeResponse)
async def authorize(
    provider: str,
    redirect_uri: str = Query(..., description="Frontend callback URL"),
    redirect_after: str = Query("/dashboard", description="Where to redirect after login"),
):
    """Return the OAuth2 authorization URL for the requested provider."""
    if provider not in _SUPPORTED:
        raise HTTPException(status_code=404, detail=f"Unknown SSO provider: {provider}")
    if not _provider_enabled(provider):
        raise HTTPException(
            status_code=400,
            detail=f"SSO provider '{provider}' is not configured on this instance.",
        )

    endpoints = await _get_endpoints(provider)
    state = generate_state(redirect_after)
    auth_url = build_auth_url(provider, redirect_uri, state, endpoints=endpoints)
    return AuthorizeResponse(auth_url=auth_url, state=state)


@router.post("/{provider}/callback", response_model=CallbackResponse)
async def callback(
    provider: str,
    body: CallbackRequest,
    db: Session = Depends(get_db),
):
    """Exchange an authorization code for a CompliAI JWT."""
    if provider not in _SUPPORTED:
        raise HTTPException(status_code=404, detail=f"Unknown SSO provider: {provider}")
    if not _provider_enabled(provider):
        raise HTTPException(
            status_code=400,
            detail=f"SSO provider '{provider}' is not configured on this instance.",
        )

    endpoints = await _get_endpoints(provider)

    try:
        token_response = await exchange_code_for_tokens(
            provider, body.code, body.redirect_uri, endpoints=endpoints
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {exc}"
        ) from exc

    access_token_provider = token_response.get("access_token", "")
    try:
        userinfo = await fetch_userinfo(access_token_provider, provider, endpoints=endpoints)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch user info: {exc}"
        ) from exc

    claims = extract_user_claims(userinfo, provider)
    if not claims["email"]:
        raise HTTPException(
            status_code=400,
            detail="Provider did not return an email address. "
            "Ensure the 'email' scope is granted.",
        )

    user = _get_or_create_sso_user(
        db,
        email=claims["email"],
        full_name=claims["full_name"],
        sub=claims["sub"],
        provider=provider,
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    jwt_token = create_access_token(data={"sub": str(user.id)})
    _, redirect_to = parse_state(body.state)

    return CallbackResponse(access_token=jwt_token, redirect_to=redirect_to)
