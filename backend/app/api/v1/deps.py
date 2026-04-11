from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.modules.auth_billing.auth import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


class OrgContext:
    def __init__(self, current_user: User, current_org, membership: OrganizationMembership):
        self.current_user = current_user
        self.current_org = current_org
        self.membership = membership


def get_org_context(
    org_id: UUID,
    user: User = Depends(get_current_active_user),
    db=Depends(get_db),
) -> OrgContext:
    from app.models.organization import Organization

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == org_id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    return OrgContext(current_user=user, current_org=org, membership=membership)


def require_role(*roles: str):
    """Returns a dependency that checks the user's role in the org context."""

    def role_checker(ctx: OrgContext = Depends(get_org_context)) -> OrgContext:
        if ctx.membership.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return ctx

    return role_checker


def check_billing_access(org) -> None:
    """Raise 402 if the organisation's trial has expired and has no active subscription.

    Call this at the start of mutation endpoints that should be gated behind billing.
    """
    from datetime import UTC, datetime

    has_active_subscription = getattr(org, "stripe_subscription_status", None) in (
        "active",
        "trialing",
    )
    if has_active_subscription:
        return

    trial_ends_at = getattr(org, "trial_ends_at", None)
    if trial_ends_at and trial_ends_at > datetime.now(UTC).replace(tzinfo=None):
        return  # Still in trial

    raise HTTPException(
        status_code=402,
        detail=(
            "Your free trial has expired. Please upgrade your plan to continue "
            "editing your Technical File."
        ),
    )


# ── API key authentication (T6.4) ────────────────────────────────────────────

import hashlib
from datetime import UTC, datetime

from fastapi import Header
from fastapi.security.api_key import APIKeyHeader

_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_org_via_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db=Depends(get_db),
):
    """Authenticate a request via an ``X-API-Key`` header.

    Returns the Organization the key belongs to, or raises 401/403.
    Used for public API access without a user JWT.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required (X-API-Key header)",
        )

    from app.models.api_key import ApiKey

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    if not api_key or not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    if api_key.expires_at and api_key.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has expired",
        )

    # Update last_used_at (best-effort, non-blocking)
    try:
        api_key.last_used_at = now
        db.commit()
    except Exception:
        db.rollback()

    from app.models.organization import Organization

    org = db.query(Organization).filter(Organization.id == api_key.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
