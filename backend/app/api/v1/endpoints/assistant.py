"""AI Assistant endpoints.

Provides:
- POST /systems/{system_id}/assistant/draft/{section_number}  → JSON draft (non-streaming)
- GET  /systems/{system_id}/assistant/stream/{section_number} → SSE streaming draft
- POST /systems/{system_id}/assistant/suggestions/{section_number} → inline suggestions
- POST /systems/{system_id}/assistant/doc-diff               → documentation impact analysis
- POST /systems/{system_id}/assistant/user-instructions      → Art. 13 user manual
- POST /systems/{system_id}/assistant/qa                     → Q&A over Technical File
- POST /systems/{system_id}/assistant/index                  → index revision for RAG
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.config import settings
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFile
from app.models.user import User
from app.modules.ai_assistant import cache as _cache
from app.modules.ai_assistant.doc_diff import analyse_documentation_impact
from app.modules.ai_assistant.draft_generator import generate_section_draft, stream_section_draft
from app.modules.ai_assistant.rag import answer_question, index_revision_sections
from app.modules.ai_assistant.suggestions import get_section_suggestions
from app.modules.ai_assistant.user_instructions import generate_user_instructions
from app.modules.annex_iv_core.completeness import calculate_section_completeness

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_ai_system(
    system_id: uuid.UUID, user: User, db: Session
) -> tuple[AISystem, OrganizationMembership]:
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    return system, membership


def _check_openai() -> None:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI Copilot is not configured (OPENAI_API_KEY missing).",
        )


def _load_current_section(system: AISystem, section_number: int, db: Session) -> dict:
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf or not tf.current_revision_id:
        return {}
    section = (
        db.query(Section)
        .filter(
            Section.revision_id == tf.current_revision_id,
            Section.section_number == section_number,
        )
        .first()
    )
    return section.content or {} if section else {}


def _load_sections_by_number(system: AISystem, db: Session) -> dict[int, dict]:
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf or not tf.current_revision_id:
        return {}
    sections = (
        db.query(Section).filter(Section.revision_id == tf.current_revision_id).all()
    )
    return {s.section_number: s.content or {} for s in sections}


# ── Draft generation (non-streaming) ─────────────────────────────────────────

@router.post("/draft/{section_number}")
def generate_draft(
    system_id: uuid.UUID,
    section_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a JSON draft for the specified section."""
    _check_openai()
    if section_number < 1 or section_number > 9:
        raise HTTPException(status_code=400, detail="Section number must be between 1 and 9")

    system, _ = _check_ai_system(system_id, current_user, db)

    # Rate limit
    if not _cache.check_rate_limit(str(system.org_id)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

    existing = _load_current_section(system, section_number, db)

    draft = generate_section_draft(
        db,
        section_number=section_number,
        system_name=system.name,
        description=system.description or "",
        intended_purpose=system.intended_purpose or "",
        category=system.category,
        annex_iii=system.annex_iii_classification,
        existing_content=existing,
        org_id=str(system.org_id),
        user_id=str(current_user.id),
        ai_system_id=str(system.id),
    )
    return {"section_number": section_number, "draft": draft}


# ── Draft generation (streaming SSE) ─────────────────────────────────────────

@router.get("/stream/{section_number}")
def stream_draft(
    system_id: uuid.UUID,
    section_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Stream a section draft as Server-Sent Events."""
    _check_openai()
    if section_number < 1 or section_number > 9:
        raise HTTPException(status_code=400, detail="Section number must be between 1 and 9")

    system, _ = _check_ai_system(system_id, current_user, db)
    existing = _load_current_section(system, section_number, db)

    generator = stream_section_draft(
        section_number=section_number,
        system_name=system.name,
        description=system.description or "",
        intended_purpose=system.intended_purpose or "",
        category=system.category,
        annex_iii=system.annex_iii_classification,
        existing_content=existing,
        org_id=str(system.org_id),
    )
    return StreamingResponse(generator, media_type="text/event-stream")


# ── Inline suggestions ────────────────────────────────────────────────────────

@router.post("/suggestions/{section_number}")
def section_suggestions(
    system_id: uuid.UUID,
    section_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return AI suggestions for missing required fields in the section."""
    _check_openai()
    if section_number < 1 or section_number > 9:
        raise HTTPException(status_code=400, detail="Section number must be between 1 and 9")

    system, _ = _check_ai_system(system_id, current_user, db)
    content = _load_current_section(system, section_number, db)
    _, missing_fields = calculate_section_completeness(section_number, content)

    suggestions = get_section_suggestions(
        db,
        section_number=section_number,
        current_content=content,
        missing_fields=missing_fields,
        org_id=str(system.org_id),
        user_id=str(current_user.id),
    )
    return {
        "section_number": section_number,
        "missing_fields": missing_fields,
        "suggestions": suggestions,
    }


# ── Documentation diff ────────────────────────────────────────────────────────

class DocDiffRequest(BaseModel):
    previous_metadata: dict
    new_metadata: dict


@router.post("/doc-diff")
def doc_diff(
    system_id: uuid.UUID,
    body: DocDiffRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Analyse which sections need updating after a metadata change."""
    _check_openai()
    system, _ = _check_ai_system(system_id, current_user, db)

    affected = analyse_documentation_impact(
        db,
        system_name=system.name,
        previous_metadata=body.previous_metadata,
        new_metadata=body.new_metadata,
        org_id=str(system.org_id),
        user_id=str(current_user.id),
        ai_system_id=str(system.id),
    )
    return {"affected_sections": affected}


# ── User Instructions (Art. 13) ───────────────────────────────────────────────

@router.post("/user-instructions")
def user_instructions(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a plain-language Instructions for Use document (Art. 13)."""
    _check_openai()
    system, _ = _check_ai_system(system_id, current_user, db)
    sections = _load_sections_by_number(system, db)

    md = generate_user_instructions(
        db,
        system_name=system.name,
        intended_purpose=system.intended_purpose or "",
        category=system.category,
        section_5_content=sections.get(5, {}),
        section_6_content=sections.get(6, {}),
        section_7_content=sections.get(7, {}),
        org_id=str(system.org_id),
        user_id=str(current_user.id),
        ai_system_id=str(system.id),
    )
    return {"markdown": md}


# ── Q&A over Technical File ───────────────────────────────────────────────────

class QARequest(BaseModel):
    question: str
    revision_id: str | None = None


@router.post("/qa")
def qa(
    system_id: uuid.UUID,
    body: QARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Answer a question over the Technical File using RAG."""
    _check_openai()
    system, _ = _check_ai_system(system_id, current_user, db)

    # Resolve revision_id
    revision_id = body.revision_id
    if not revision_id:
        tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
        if not tf or not tf.current_revision_id:
            raise HTTPException(status_code=404, detail="No technical file revision found")
        revision_id = str(tf.current_revision_id)

    result = answer_question(
        db,
        question=body.question,
        revision_id=revision_id,
        ai_system_id=str(system.id),
        org_id=str(system.org_id),
        user_id=str(current_user.id),
    )
    return result


# ── Index revision for RAG ────────────────────────────────────────────────────

class IndexRequest(BaseModel):
    revision_id: str | None = None


@router.post("/index")
def index_for_rag(
    system_id: uuid.UUID,
    body: IndexRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Index the current (or specified) revision's sections for Q&A."""
    _check_openai()
    system, _ = _check_ai_system(system_id, current_user, db)

    revision_id = body.revision_id if body else None
    if not revision_id:
        tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
        if not tf or not tf.current_revision_id:
            raise HTTPException(status_code=404, detail="No technical file revision found")
        revision_id = str(tf.current_revision_id)

    count = index_revision_sections(
        db,
        revision_id=revision_id,
        ai_system_id=str(system.id),
        org_id=str(system.org_id),
    )
    return {"indexed_sections": count, "revision_id": revision_id}
