"""Quick-Start Lite Wizard endpoints (Epic 0).

Public endpoints — no authentication required for session creation and most operations.
Payment verification gates the PDF export.

  POST   /wizard/sessions                     → create new session
  GET    /wizard/sessions/{token}             → load session state
  PUT    /wizard/sessions/{token}/blocks/{id} → save block answers
  POST   /wizard/sessions/{token}/generate-paragraph  → stream AI paragraph
  POST   /wizard/sessions/{token}/classify-risk       → inline Annex III classification
  POST   /wizard/sessions/{token}/checkout            → create Stripe checkout (299 EUR)
  POST   /wizard/sessions/{token}/export-pdf          → export PDF (payment required)
  GET    /wizard/sessions/{token}/resume-email        → send resume link
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.wizard_session import WizardSession
from app.modules.wizard.blocks import (
    WIZARD_BLOCKS,
    WIZARD_BLOCKS_BY_ID,
    calculate_completion_percent,
)
from app.modules.wizard.prompt_chain import generate_block_paragraph, stream_block_paragraph

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_LOGO_MIMES = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
_MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB


# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_session(token: str, db: Session) -> WizardSession:
    session = db.query(WizardSession).filter(WizardSession.session_token == token).first()
    if not session:
        raise HTTPException(status_code=404, detail="Wizard session not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if session.expires_at and session.expires_at < now:
        raise HTTPException(status_code=410, detail="Wizard session has expired")
    return session


def _session_to_dict(session: WizardSession, include_paragraphs: bool = True) -> dict:
    completion = calculate_completion_percent(session.answers or {})
    result = {
        "session_token": session.session_token,
        "email": session.email,
        "org_name": session.org_name,
        "system_name": session.system_name,
        "current_block": session.current_block,
        "answers": session.answers or {},
        "risk_result": session.risk_result,
        "payment_confirmed": session.payment_confirmed,
        "completion_percent": completion,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
    if include_paragraphs:
        result["generated_paragraphs"] = session.generated_paragraphs or {}
    return result


# ── Request / Response models ─────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    email: str | None = None
    org_name: str | None = None
    system_name: str | None = None


class SaveBlockRequest(BaseModel):
    answers: dict[str, object]  # {question_id: answer}
    advance: bool = False        # if True, set current_block to next block


class GenerateParagraphRequest(BaseModel):
    block_id: str


class ClassifyRiskRequest(BaseModel):
    pass  # uses B1/B2 answers already in session


class CheckoutRequest(BaseModel):
    email: str | None = None


class ExportPdfRequest(BaseModel):
    disclaimer_accepted: bool
    partner_name: str | None = None


class ResumeEmailRequest(BaseModel):
    email: EmailStr


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/blocks")
def get_wizard_blocks():
    """Return all wizard block and question definitions."""
    return {
        "blocks": [
            {
                "id": b.id,
                "number": b.number,
                "title": b.title,
                "description": b.description,
                "annex_iv_sections": b.annex_iv_sections,
                "questions": [
                    {
                        "id": q.id,
                        "text": q.text,
                        "type": q.type,
                        "options": q.options,
                        "placeholder": q.placeholder,
                        "why_asking": q.why_asking,
                        "article_ref": q.article_ref,
                        "required": q.required,
                    }
                    for q in b.questions
                ],
            }
            for b in WIZARD_BLOCKS
        ],
        "disclaimer": "Technical File Completion % means structural completeness only — "
                      "this document requires legal and ML Lead review before submission "
                      "to any supervisory authority.",
    }


@router.post("/sessions")
def create_session(body: CreateSessionRequest, db: Session = Depends(get_db)):
    """Create a new anonymous wizard session."""
    session = WizardSession(
        id=uuid.uuid4(),
        email=body.email,
        org_name=body.org_name,
        system_name=body.system_name,
        current_block="B1",
        answers={},
        generated_paragraphs={},
        payment_confirmed=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_to_dict(session)


@router.get("/sessions/{token}")
def get_session(token: str, db: Session = Depends(get_db)):
    """Load a wizard session by session token."""
    session = _get_session(token, db)
    return _session_to_dict(session)


@router.put("/sessions/{token}/blocks/{block_id}")
def save_block(
    token: str,
    block_id: str,
    body: SaveBlockRequest,
    db: Session = Depends(get_db),
):
    """Save answers for a wizard block and optionally advance to next block."""
    if block_id not in WIZARD_BLOCKS_BY_ID:
        raise HTTPException(status_code=422, detail=f"Unknown block: {block_id}")

    session = _get_session(token, db)

    # Merge answers
    current_answers = dict(session.answers or {})
    current_answers[block_id] = body.answers
    session.answers = current_answers

    # Advance block if requested
    if body.advance:
        block_numbers = [b.id for b in WIZARD_BLOCKS]
        try:
            idx = block_numbers.index(block_id)
            if idx + 1 < len(block_numbers):
                session.current_block = block_numbers[idx + 1]
        except ValueError:
            pass

    # Persist system_name / org_name from B1 answers
    if block_id == "B1":
        b1 = body.answers
        if b1.get("B1Q1") and not session.system_name:
            session.system_name = str(b1["B1Q1"])

    db.commit()
    db.refresh(session)
    return _session_to_dict(session)


@router.post("/sessions/{token}/generate-paragraph")
def generate_paragraph(
    token: str,
    body: GenerateParagraphRequest,
    db: Session = Depends(get_db),
):
    """Generate an AI paragraph for a specific wizard block (non-streaming).

    Saves the result in the session and returns it.
    """
    if body.block_id not in WIZARD_BLOCKS_BY_ID:
        raise HTTPException(status_code=422, detail=f"Unknown block: {body.block_id}")

    session = _get_session(token, db)
    block_answers = (session.answers or {}).get(body.block_id, {})

    paragraph = generate_block_paragraph(body.block_id, block_answers)

    paragraphs = dict(session.generated_paragraphs or {})
    paragraphs[body.block_id] = paragraph
    session.generated_paragraphs = paragraphs
    db.commit()

    return {
        "block_id": body.block_id,
        "paragraph": paragraph,
        "completion_percent": calculate_completion_percent(session.answers or {}),
    }


@router.post("/sessions/{token}/generate-paragraph/stream")
def stream_paragraph(
    token: str,
    body: GenerateParagraphRequest,
    db: Session = Depends(get_db),
):
    """Stream an AI paragraph for a wizard block as SSE."""
    if body.block_id not in WIZARD_BLOCKS_BY_ID:
        raise HTTPException(status_code=422, detail=f"Unknown block: {body.block_id}")

    session = _get_session(token, db)
    block_answers = (session.answers or {}).get(body.block_id, {})

    def event_stream():
        accumulated = []
        for chunk in stream_block_paragraph(body.block_id, block_answers):
            accumulated.append(chunk)
            yield chunk
        # Persist the full paragraph after streaming completes
        try:
            import json as _json
            full_text = "".join(
                _json.loads(c[6:].strip()).get("delta", "")
                for c in accumulated
                if c.startswith("data: {")
            )
            if full_text:
                s = db.query(WizardSession).filter(WizardSession.session_token == token).first()
                if s:
                    paragraphs = dict(s.generated_paragraphs or {})
                    paragraphs[body.block_id] = full_text
                    s.generated_paragraphs = paragraphs
                    db.commit()
        except Exception as exc:
            logger.warning("Failed to persist streamed paragraph: %s", exc)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{token}/classify-risk")
def classify_risk(
    token: str,
    db: Session = Depends(get_db),
):
    """Run inline Annex III risk classification based on B1/B2 answers."""
    session = _get_session(token, db)
    answers = session.answers or {}

    # Build flat answer dict for the classifier from B1/B2 answers
    b1 = answers.get("B1", {})
    b2 = answers.get("B2", {})
    classifier_answers = {
        "q1": b2.get("B2Q1", ""),
        "q2": "",
        "q3": False,
        "q4": False,
        "q5": False,
        "q6": False,
        "q7": False,
        "q8": True,
        "q9": "European Union / EEA",
        "q10": b1.get("B1Q3", ""),
    }

    try:
        from app.modules.classifier.annex3_rules import classify

        result = classify(classifier_answers)
        session.risk_result = result.risk_level
        db.commit()
        return {
            "risk_level": result.risk_level,
            "justification": result.justification,
            "article_citations": result.article_citations,
            "annex_iii_category": result.annex_iii_category,
        }
    except Exception as exc:
        logger.error("Risk classification failed: %s", exc)
        return {"risk_level": "high_risk", "justification": "Classification unavailable — treat as high-risk."}


@router.post("/sessions/{token}/checkout")
def create_checkout(
    token: str,
    body: CheckoutRequest,
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for the Lite plan (299 EUR one-time).

    Returns the Stripe checkout URL to redirect the user.
    """
    session = _get_session(token, db)

    if body.email:
        session.email = body.email
        db.commit()

    email = session.email

    success_url = (
        f"{settings.FRONTEND_URL}/wizard/{token}/export"
        "?payment=success&session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = f"{settings.FRONTEND_URL}/wizard/{token}"

    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        lite_price_id = getattr(settings, "STRIPE_PRICE_LITE", "")

        if not lite_price_id or not settings.STRIPE_SECRET_KEY:
            logger.warning("Stripe not configured — returning mock checkout URL")
            return {
                "checkout_url": f"{settings.FRONTEND_URL}/wizard/{token}/export?payment=mock",
                "mock": True,
            }

        # Create or reuse Stripe customer for anonymous sessions
        customer_params: dict = {"metadata": {"wizard_token": token}}
        if email:
            customer_params["email"] = email
        customer = stripe.Customer.create(**customer_params)

        checkout = stripe.checkout.Session.create(
            customer=customer["id"],
            mode="payment",
            line_items=[{"price": lite_price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"wizard_token": token},
        )
        session.stripe_checkout_session_id = checkout["id"]
        db.commit()
        return {"checkout_url": checkout["url"]}

    except Exception as exc:
        logger.error("Stripe checkout creation failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Payment system error: {exc}") from exc


@router.post("/sessions/{token}/export-pdf")
async def export_pdf(
    token: str,
    disclaimer_accepted: bool = False,
    partner_name: str | None = None,
    logo: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    """Generate and return the Lite Wizard PDF.

    Gated by payment_confirmed=True.
    Disclaimer must be accepted (non-skippable per PRD v1.15).
    """
    session = _get_session(token, db)

    if not session.payment_confirmed:
        raise HTTPException(
            status_code=402,
            detail="Payment required to export PDF. Please complete checkout first.",
        )

    if not disclaimer_accepted:
        raise HTTPException(
            status_code=422,
            detail="Disclaimer acceptance required before export. "
                   "Please confirm you have read and accepted the disclaimer.",
        )

    # Handle logo upload
    logo_bytes: bytes | None = None
    logo_mime: str | None = None
    if logo:
        if logo.content_type not in _ALLOWED_LOGO_MIMES:
            raise HTTPException(status_code=422, detail="Logo must be PNG, JPEG, WebP, or SVG.")
        raw = await logo.read()
        if len(raw) > _MAX_LOGO_BYTES:
            raise HTTPException(status_code=413, detail="Logo file too large (max 2 MB).")
        logo_bytes = raw
        logo_mime = logo.content_type

    try:
        from app.modules.wizard.pdf_builder import build_lite_pdf

        pdf_bytes = build_lite_pdf(
            session=session,
            disclaimer_accepted=disclaimer_accepted,
            logo_bytes=logo_bytes,
            logo_mime=logo_mime,
            partner_name=partner_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("PDF generation failed for session %s: %s", token, exc)
        raise HTTPException(status_code=500, detail="PDF generation failed") from exc

    # Optionally upload to S3
    _upload_pdf_to_s3(session, pdf_bytes, db)

    filename = f"annex-iv-{(session.system_name or 'draft').lower().replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{token}/resume-email")
def send_resume_email(
    token: str,
    email: str,
    db: Session = Depends(get_db),
):
    """Send a resume link to the given email address."""
    session = _get_session(token, db)

    if not email:
        raise HTTPException(status_code=422, detail="Email required")

    # Store email on session if not set
    if not session.email:
        session.email = email
        db.commit()

    resume_url = f"{settings.FRONTEND_URL}/wizard/{token}"
    _send_resume_link(email, resume_url)
    return {"ok": True}


# ── Internal helpers ───────────────────────────────────────────────────────────


def _upload_pdf_to_s3(session: WizardSession, pdf_bytes: bytes, db: Session) -> None:
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
        key = f"wizard-exports/{session.session_token}/annex-iv.pdf"
        s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=pdf_bytes, ContentType="application/pdf")
        session.pdf_s3_key = key
        db.commit()
    except Exception as exc:
        logger.warning("S3 upload failed (non-fatal): %s", exc)


def _send_resume_link(email: str, url: str) -> None:
    try:
        import httpx

        api_key = getattr(settings, "RESEND_API_KEY", "")
        from_email = getattr(settings, "RESEND_FROM_EMAIL", "noreply@compliai.io")
        if not api_key:
            logger.warning("RESEND_API_KEY not set — skipping resume email")
            return

        html = f"""
        <div style="font-family: sans-serif; max-width: 600px;">
          <h2>Continue your Annex IV Technical File</h2>
          <p>You started a Technical File for your AI system. Click below to continue:</p>
          <p><a href="{url}" style="background:#1a56db;color:white;padding:12px 24px;
             border-radius:6px;text-decoration:none;font-weight:bold;">
             Continue Technical File
          </a></p>
          <p style="color:#6b7280;font-size:12px;">Link expires in 7 days.</p>
        </div>
        """
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [email], "subject": "Continue your AI Act Technical File", "html": html},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("Resume email failed: %s", exc)
