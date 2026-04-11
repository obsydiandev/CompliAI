"""AI Act Risk Classifier endpoints (Epic 19).

Public endpoints — no authentication required:
  POST /classifier/evaluate        → classify answers, return result + panic calendar
  POST /classifier/capture-email   → attach email to lead for nurturing
  GET  /classifier/result/{token}  → retrieve shareable result by share_token
  GET  /classifier/questions       → return question definitions for the frontend
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classifier_lead import ClassifierLead
from app.modules.classifier.annex3_rules import (
    CLASSIFIER_QUESTIONS,
    ClassificationResult,
    classify,
)
from app.modules.classifier.panic_calendar import get_panic_calendar, get_primary_deadline

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────


class EvaluateRequest(BaseModel):
    answers: dict[str, str | bool]
    use_llm_fallback: bool = True


class EvaluateResponse(BaseModel):
    lead_id: str
    share_token: str
    risk_level: str
    justification: str
    article_citations: list[str]
    annex_iii_category: str | None
    is_edge_case: bool
    panic_calendar: list[dict]
    primary_deadline: dict


class CaptureEmailRequest(BaseModel):
    lead_id: str
    email: EmailStr


# ── Helpers ────────────────────────────────────────────────────────────────────


def _run_classification(answers: dict, use_llm_fallback: bool) -> ClassificationResult:
    result = classify(answers)
    if result.is_edge_case and use_llm_fallback:
        try:
            from app.modules.classifier.llm_fallback import classify_with_llm

            result = classify_with_llm(answers, preliminary_result=result)
        except Exception as exc:
            logger.warning("LLM fallback skipped: %s", exc)
    return result


def _persist_lead(db: Session, answers: dict, result: ClassificationResult) -> ClassifierLead:
    lead = ClassifierLead(
        id=uuid.uuid4(),
        answers=answers,
        result=result.risk_level,
        justification=result.justification,
        article_citations=result.article_citations,
        annex_iii_category=result.annex_iii_category,
        is_edge_case=str(result.is_edge_case),
        share_token=str(uuid.uuid4()).replace("-", ""),
        nurturing_sent=[],
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/questions")
def get_questions():
    """Return the 10 classifier questions for the frontend."""
    return {"questions": CLASSIFIER_QUESTIONS}


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(
    body: EvaluateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Classify an AI system based on 10 structured answers.

    No authentication required — public endpoint.
    """
    result = _run_classification(body.answers, body.use_llm_fallback)
    lead = _persist_lead(db, body.answers, result)
    calendar = get_panic_calendar()
    primary = get_primary_deadline(result.risk_level)

    return EvaluateResponse(
        lead_id=str(lead.id),
        share_token=lead.share_token,
        risk_level=result.risk_level,
        justification=result.justification,
        article_citations=result.article_citations,
        annex_iii_category=result.annex_iii_category,
        is_edge_case=result.is_edge_case,
        panic_calendar=calendar,
        primary_deadline=primary,
    )


@router.post("/capture-email")
def capture_email(
    body: CaptureEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Attach an email address to an existing classifier lead.

    Triggers the nurturing sequence (D+1, D+7, D+14) for high-risk results.
    """
    try:
        lead_id = uuid.UUID(body.lead_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid lead_id format")

    lead = db.query(ClassifierLead).filter(ClassifierLead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.email = str(body.email)
    db.commit()

    if lead.result == "high_risk":
        background_tasks.add_task(_schedule_nurturing, str(lead.id), str(body.email))

    return {"ok": True, "email": str(body.email)}


@router.get("/result/{share_token}")
def get_result(share_token: str, db: Session = Depends(get_db)):
    """Return a shareable classifier result by its share token.

    No authentication required — used for LinkedIn/public sharing.
    """
    lead = db.query(ClassifierLead).filter(ClassifierLead.share_token == share_token).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Result not found")

    calendar = get_panic_calendar()
    primary = get_primary_deadline(lead.result)

    return {
        "share_token": lead.share_token,
        "risk_level": lead.result,
        "justification": lead.justification,
        "article_citations": lead.article_citations or [],
        "annex_iii_category": lead.annex_iii_category,
        "panic_calendar": calendar,
        "primary_deadline": primary,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


# ── Background task helpers ────────────────────────────────────────────────────


def _schedule_nurturing(lead_id: str, email: str) -> None:
    """Schedule D+1/D+7/D+14 nurturing emails via Celery."""
    try:
        from app.tasks.email_nurturing import send_nurturing_d1

        send_nurturing_d1.apply_async(args=[lead_id, email], countdown=86400)  # 24h
    except Exception as exc:
        logger.warning("Failed to schedule nurturing for lead %s: %s", lead_id, exc)
