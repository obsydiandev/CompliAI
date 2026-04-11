"""White-Label Partner endpoints (Epic 17).

  POST   /partners                                     → register partner
  GET    /partners/{partner_id}                        → get partner details
  GET    /partners/{partner_id}/clients               → list client sessions
  POST   /partners/{partner_id}/clients               → create client wizard session
  GET    /partners/{partner_id}/clients/{token}        → get client session
  PUT    /partners/{partner_id}/clients/{token}/status → update workflow status
  POST   /partners/{partner_id}/clients/{token}/export → branded PDF export
"""

from __future__ import annotations

import io
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.config import settings
from app.database import get_db
from app.models.partner import Partner
from app.models.wizard_session import WizardSession

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_LOGO_MIMES = {"image/png", "image/jpeg", "image/webp"}
_MAX_LOGO_BYTES = 2 * 1024 * 1024


# ── Schemas ───────────────────────────────────────────────────────────────────


class RegisterPartnerRequest(BaseModel):
    org_id: str
    name: str


class CreateClientRequest(BaseModel):
    client_name: str
    system_name: str | None = None
    email: str | None = None


class UpdateClientStatusRequest(BaseModel):
    status: str  # "in_review" | "approved" | "sent"


class BrandedExportRequest(BaseModel):
    disclaimer_accepted: bool


# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_partner(partner_id: str, db: Session) -> Partner:
    try:
        pid = uuid.UUID(partner_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid partner_id")
    p = db.query(Partner).filter(Partner.id == pid).first()
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    return p


def _require_partner_membership(partner: Partner, ctx: OrgContext) -> None:
    if str(partner.org_id) != str(ctx.current_org.id):
        raise HTTPException(status_code=403, detail="Not your partner account")


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("")
def register_partner(
    body: RegisterPartnerRequest,
    db: Session = Depends(get_db),
):
    """Register a new partner (maps to an existing org)."""
    try:
        org_id = uuid.UUID(body.org_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid org_id")

    existing = db.query(Partner).filter(Partner.org_id == org_id).first()
    if existing:
        return {"partner_id": str(existing.id), "name": existing.name, "already_exists": True}

    partner = Partner(id=uuid.uuid4(), org_id=org_id, name=body.name, client_sessions=[])
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return {"partner_id": str(partner.id), "name": partner.name}


@router.get("/{partner_id}")
def get_partner(
    partner_id: str,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)
    return {
        "partner_id": str(partner.id),
        "name": partner.name,
        "org_id": str(partner.org_id),
        "has_logo": bool(partner.logo_s3_key),
        "client_count": len(partner.client_sessions or []),
        "billing_plan": partner.billing_plan,
    }


@router.post("/{partner_id}/logo")
async def upload_logo(
    partner_id: str,
    logo: UploadFile,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Upload partner logo for branded PDF exports."""
    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)

    if logo.content_type not in _ALLOWED_LOGO_MIMES:
        raise HTTPException(status_code=422, detail="Logo must be PNG, JPEG, or WebP.")
    raw = await logo.read()
    if len(raw) > _MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="Logo too large (max 2 MB).")

    try:
        import re
        import boto3
        from botocore.client import Config

        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", logo.filename or "logo.png")
        key = f"partner-logos/{partner.id}/{uuid.uuid4()}/{safe_name}"

        s3_kwargs: dict = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        if settings.AWS_S3_ENDPOINT_URL:
            s3_kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
        s3_kwargs["config"] = Config(signature_version="s3v4")

        s3 = boto3.client("s3", **s3_kwargs)
        s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=raw, ContentType=logo.content_type)
        partner.logo_s3_key = key
        db.commit()
        return {"ok": True, "logo_s3_key": key}
    except Exception as exc:
        logger.error("Logo upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="Logo upload failed") from exc


@router.get("/{partner_id}/clients")
def list_clients(
    partner_id: str,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """List all client wizard sessions managed by this partner."""
    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)

    client_sessions = partner.client_sessions or []
    results = []
    for entry in client_sessions:
        token = entry.get("session_token")
        if not token:
            continue
        s = db.query(WizardSession).filter(WizardSession.session_token == token).first()
        if s:
            results.append(
                {
                    "session_token": s.session_token,
                    "client_name": entry.get("client_name", ""),
                    "system_name": s.system_name,
                    "email": s.email,
                    "status": entry.get("status", "generated"),
                    "payment_confirmed": s.payment_confirmed,
                    "completion_percent": _pct(s),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
            )
    return {"clients": results}


@router.post("/{partner_id}/clients")
def create_client(
    partner_id: str,
    body: CreateClientRequest,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Create a new wizard session for a partner client."""
    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)

    session = WizardSession(
        id=uuid.uuid4(),
        email=body.email,
        system_name=body.system_name,
        partner_id=partner.id,
        current_block="B1",
        answers={},
        generated_paragraphs={},
        payment_confirmed=True,  # partner handles billing separately
    )
    db.add(session)

    # Register in partner's client list
    clients = list(partner.client_sessions or [])
    clients.append(
        {
            "session_token": session.session_token,
            "client_name": body.client_name,
            "status": "generated",
        }
    )
    partner.client_sessions = clients
    db.commit()
    db.refresh(session)

    return {
        "session_token": session.session_token,
        "client_name": body.client_name,
        "wizard_url": f"{settings.FRONTEND_URL}/wizard/{session.session_token}",
    }


@router.put("/{partner_id}/clients/{session_token}/status")
def update_client_status(
    partner_id: str,
    session_token: str,
    body: UpdateClientStatusRequest,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Update the review workflow status of a client session."""
    valid_statuses = ("generated", "in_review", "approved", "sent")
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)

    clients = list(partner.client_sessions or [])
    for entry in clients:
        if entry.get("session_token") == session_token:
            entry["status"] = body.status
            break
    else:
        raise HTTPException(status_code=404, detail="Client session not found in this partner account")

    partner.client_sessions = clients
    db.commit()
    return {"ok": True, "status": body.status}


@router.post("/{partner_id}/clients/{session_token}/export")
async def export_branded_pdf(
    partner_id: str,
    session_token: str,
    disclaimer_accepted: bool = False,
    logo_override: UploadFile | None = None,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Generate a branded PDF for a partner client session."""
    partner = _get_partner(partner_id, db)
    _require_partner_membership(partner, ctx)

    if not disclaimer_accepted:
        raise HTTPException(
            status_code=422,
            detail="Disclaimer must be accepted before export.",
        )

    s = db.query(WizardSession).filter(WizardSession.session_token == session_token).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get partner logo bytes
    logo_bytes: bytes | None = None
    logo_mime: str | None = None

    if logo_override:
        raw = await logo_override.read()
        if len(raw) <= _MAX_LOGO_BYTES:
            logo_bytes = raw
            logo_mime = logo_override.content_type
    elif partner.logo_s3_key:
        try:
            import boto3
            from botocore.client import Config

            s3_kwargs: dict = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            }
            if settings.AWS_S3_ENDPOINT_URL:
                s3_kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
            s3_kwargs["config"] = Config(signature_version="s3v4")
            s3 = boto3.client("s3", **s3_kwargs)
            obj = s3.get_object(Bucket=settings.AWS_S3_BUCKET, Key=partner.logo_s3_key)
            logo_bytes = obj["Body"].read()
            logo_mime = obj.get("ContentType", "image/png")
        except Exception as exc:
            logger.warning("Could not fetch partner logo: %s", exc)

    try:
        from app.modules.wizard.pdf_builder import build_lite_pdf

        pdf_bytes = build_lite_pdf(
            session=s,
            disclaimer_accepted=True,
            logo_bytes=logo_bytes,
            logo_mime=logo_mime,
            partner_name=partner.name,
        )
    except Exception as exc:
        logger.error("Branded PDF generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="PDF generation failed") from exc

    filename = f"annex-iv-{(s.system_name or 'draft').lower().replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pct(session: WizardSession) -> float:
    from app.modules.wizard.blocks import calculate_completion_percent
    return calculate_completion_percent(session.answers or {})
