"""BYOK and Stateless Mode endpoints (Phase 2, T18.2–T18.4).

  PUT  /organizations/{org_id}/byok/kms         → configure KMS provider + key ARN
  PUT  /organizations/{org_id}/byok/llm-key     → set own OpenAI/Anthropic API key
  POST /organizations/{org_id}/byok/test         → test KMS connectivity
  PUT  /organizations/{org_id}/byok/stateless    → toggle stateless/zero-knowledge mode
  GET  /organizations/{org_id}/byok/status       → current BYOK configuration status
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, require_role
from app.database import get_db
from app.models.organization import Organization

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class ConfigureKmsRequest(BaseModel):
    provider: str  # "aws" | "azure" | "gcp"
    key_arn: str


class SetLlmKeyRequest(BaseModel):
    api_key: str
    provider: str = "openai"  # "openai" | "anthropic" | "azure_openai"


class StatelessToggleRequest(BaseModel):
    enabled: bool


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_org(org_id: uuid.UUID, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/status")
def byok_status(
    org_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Return current BYOK configuration status for the org."""
    org = ctx.current_org
    return {
        "byok_kms_configured": bool(getattr(org, "byok_kms_provider", None)),
        "byok_kms_provider": getattr(org, "byok_kms_provider", None),
        "byok_llm_key_configured": bool(getattr(org, "byok_openai_key", None)),
        "stateless_mode": getattr(org, "stateless_mode", False),
    }


@router.put("/kms")
def configure_kms(
    org_id: uuid.UUID,
    body: ConfigureKmsRequest,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Configure KMS provider and key ARN for envelope encryption."""
    valid_providers = ("aws", "azure", "gcp")
    if body.provider not in valid_providers:
        raise HTTPException(
            status_code=422,
            detail=f"Provider must be one of: {', '.join(valid_providers)}",
        )

    if not body.key_arn.strip():
        raise HTTPException(status_code=422, detail="key_arn must not be empty")

    org = ctx.current_org
    org.byok_kms_provider = body.provider
    org.byok_kms_key_arn = body.key_arn.strip()
    db.commit()
    logger.info("BYOK KMS configured for org %s: provider=%s", org.id, body.provider)
    return {"ok": True, "provider": body.provider}


@router.put("/llm-key")
def set_llm_key(
    org_id: uuid.UUID,
    body: SetLlmKeyRequest,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Set the organisation's own LLM API key (BYOK LLM, T18.3).

    The key is stored as-is; in production environments it should be encrypted
    at rest using the BYOK KMS if configured.
    """
    if not body.api_key.strip():
        raise HTTPException(status_code=422, detail="api_key must not be empty")

    org = ctx.current_org

    # If BYOK KMS is configured, encrypt the LLM key with it
    if getattr(org, "byok_kms_provider", None) and getattr(org, "byok_kms_key_arn", None):
        try:
            from app.modules.auth_billing.byok import encrypt_field

            encrypted = encrypt_field(org.byok_kms_provider, org.byok_kms_key_arn, body.api_key)
            org.byok_openai_key = encrypted
        except Exception as exc:
            logger.error("Failed to encrypt LLM key with KMS: %s", exc)
            raise HTTPException(status_code=500, detail=f"KMS encryption failed: {exc}") from exc
    else:
        org.byok_openai_key = body.api_key.strip()

    db.commit()
    return {"ok": True, "provider": body.provider, "key_prefix": body.api_key[:8] + "..."}


@router.post("/test")
def test_kms(
    org_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Test KMS connectivity by performing a test encrypt/decrypt."""
    org = ctx.current_org
    provider = getattr(org, "byok_kms_provider", None)
    key_arn = getattr(org, "byok_kms_key_arn", None)

    if not provider or not key_arn:
        raise HTTPException(status_code=422, detail="KMS not configured. Call PUT /byok/kms first.")

    try:
        from app.modules.auth_billing.byok import test_kms_connectivity

        success = test_kms_connectivity(provider, key_arn)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"KMS test failed: {exc}") from exc

    if not success:
        raise HTTPException(
            status_code=502,
            detail="KMS connectivity test failed. Check your key ARN and IAM permissions.",
        )
    return {"ok": True, "provider": provider}


@router.put("/stateless")
def toggle_stateless(
    org_id: uuid.UUID,
    body: StatelessToggleRequest,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Enable or disable Stateless/Zero-Knowledge Mode (T18.4).

    When enabled: all wizard answers and generated paragraphs are purged from the
    database after PDF export. Once purged, the document cannot be regenerated.
    """
    org = ctx.current_org
    org.stateless_mode = body.enabled
    db.commit()

    return {
        "ok": True,
        "stateless_mode": body.enabled,
        "warning": (
            "Stateless mode is now ENABLED. After PDF export, all wizard data will be permanently "
            "deleted. Documents cannot be regenerated after purge."
        ) if body.enabled else None,
    }
