"""Public API key management endpoints (T6.4).

GET    /organizations/{org_id}/api-keys               — list keys
POST   /organizations/{org_id}/api-keys               — create key (returns plaintext ONCE)
DELETE /organizations/{org_id}/api-keys/{key_id}      — revoke key

Authentication with an API key is handled by the ``X-API-Key`` header.
The dependency ``get_current_via_api_key`` in ``deps.py`` validates it.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context, require_role
from app.database import get_db
from app.models.api_key import ApiKey

router = APIRouter()

_KEY_PREFIX = "caik"  # CompliAI API Key
_KEY_BYTES = 32       # 256 bits of entropy → 43-char base64url


# ── Schemas ───────────────────────────────────────────────────────────────────


class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: int | None = None  # None = never expires


class ApiKeyRead(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreated(ApiKeyRead):
    """Returned once on creation — contains the full plaintext key."""

    key: str  # Full key — shown only once


# ── Helpers ───────────────────────────────────────────────────────────────────


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns (full_key, prefix, hash).
    """
    token = secrets.token_urlsafe(_KEY_BYTES)
    full_key = f"{_KEY_PREFIX}_{token}"
    prefix = full_key[:12]  # "caik_Abcd123"
    key_hash = _hash_key(full_key)
    return full_key, prefix, key_hash


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ApiKeyRead])
def list_api_keys(
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """List all API keys for the organisation (plaintext never returned here)."""
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.org_id == ctx.current_org.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    body: ApiKeyCreate,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new API key.  The full key value is returned **once** — store it safely."""
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="API key name must not be empty")

    full_key, prefix, key_hash = _generate_key()
    now = datetime.now(UTC).replace(tzinfo=None)

    expires_at = None
    if body.expires_in_days is not None:
        from datetime import timedelta

        expires_at = now + timedelta(days=body.expires_in_days)

    api_key = ApiKey(
        id=uuid.uuid4(),
        org_id=ctx.current_org.id,
        created_by=ctx.current_user.id,
        name=body.name.strip(),
        key_prefix=prefix,
        key_hash=key_hash,
        is_active=True,
        expires_at=expires_at,
        created_at=now,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyCreated(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        key=full_key,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Permanently revoke (delete) an API key."""
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.org_id == ctx.current_org.id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(api_key)
    db.commit()
