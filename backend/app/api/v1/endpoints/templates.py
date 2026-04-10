"""Templates, ISO 42001 Crosswalk and AI Impact Assessment endpoints (Epic 6 / Faza 5).

Endpoints:
  GET  /templates                              — list templates
  GET  /templates/{template_id}               — get template detail
  POST /systems/{system_id}/templates/apply   — apply template to current revision
  GET  /systems/{system_id}/iso42001          — ISO 42001 crosswalk for a system
  POST /systems/{system_id}/iso42001/package  — generate evidence package summary
  POST /systems/{system_id}/ai-ia             — generate AI Impact Assessment
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.ai_assistant.impact_assessment import build_ai_ia_report
from app.modules.annex_iv_core.iso42001_crosswalk import (
    ISO_42001_CROSSWALK,
    build_evidence_package,
)
from app.modules.annex_iv_core.nist_crosswalk import (
    get_colorado_crosswalk,
    get_nist_crosswalk,
)
from app.modules.annex_iv_core.templates import (
    apply_template_to_content,
    get_template,
    list_templates,
)
from app.schemas.template import (
    AIIARequest,
    AIIAResponse,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    CrosswalkEntry,
    EvidencePackage,
    TemplateDetail,
    TemplateSummary,
)

# ── Routers ───────────────────────────────────────────────────────────────────

# Global (no prefix needed — mounted at /templates)
templates_router = APIRouter()

# System-scoped (mounted under /systems/{system_id})
system_router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_system_or_404(system_id: uuid.UUID, db: Session) -> AISystem:
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    return system


def _current_revision(system: AISystem, db: Session) -> TechnicalFileRevision | None:
    if not system.technical_file:
        return None
    tf: TechnicalFile = system.technical_file
    if tf.current_revision_id:
        return (
            db.query(TechnicalFileRevision)
            .filter(TechnicalFileRevision.id == tf.current_revision_id)
            .first()
        )
    return (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.tf_id == tf.id)
        .order_by(TechnicalFileRevision.created_at.desc())
        .first()
    )


def _sections_for_revision(revision_id: uuid.UUID, db: Session) -> list[Section]:
    return db.query(Section).filter(Section.revision_id == revision_id).all()


# ── Template endpoints ────────────────────────────────────────────────────────


@templates_router.get("", response_model=list[TemplateSummary])
def list_template_catalogue(_: User = Depends(get_current_active_user)):
    return list_templates()


@templates_router.get("/{template_id}", response_model=TemplateDetail)
def get_template_detail(
    template_id: str, _: User = Depends(get_current_active_user)
):
    tpl = get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@system_router.post(
    "/templates/apply",
    response_model=ApplyTemplateResponse,
    status_code=status.HTTP_200_OK,
)
def apply_template(
    system_id: uuid.UUID,
    payload: ApplyTemplateRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Apply a template to a TechnicalFileRevision (T5.2)."""
    system = _get_system_or_404(system_id, db)
    revision = (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.id == payload.revision_id)
        .first()
    )
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")
    if not system.technical_file or revision.tf_id != system.technical_file.id:
        raise HTTPException(
            status_code=403, detail="Revision does not belong to this system"
        )

    # Build existing section content map
    sections = _sections_for_revision(revision.id, db)
    existing: dict[int, dict] = {s.section_number: s.content or {} for s in sections}

    # Apply template
    merged = apply_template_to_content(payload.template_id, existing, payload.overwrite)

    applied: list[int] = []
    skipped: list[int] = []

    for sec_num, content in merged.items():
        if content == existing.get(sec_num, {}):
            skipped.append(sec_num)
            continue

        sec_obj = next((s for s in sections if s.section_number == sec_num), None)
        if sec_obj:
            sec_obj.content = content
        else:
            db.add(
                Section(
                    id=uuid.uuid4(),
                    revision_id=revision.id,
                    section_number=sec_num,
                    content=content,
                )
            )
        applied.append(sec_num)

    db.commit()
    return ApplyTemplateResponse(applied_sections=sorted(applied), skipped_sections=sorted(skipped))


# ── ISO 42001 Crosswalk endpoints ─────────────────────────────────────────────


@system_router.get("/iso42001", response_model=list[CrosswalkEntry])
def get_iso42001_crosswalk(
    system_id: uuid.UUID,
    _: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Full Annex IV ↔ ISO 42001 crosswalk (T5.3)."""
    _get_system_or_404(system_id, db)
    return ISO_42001_CROSSWALK


@system_router.post("/iso42001/package", response_model=EvidencePackage)
def iso42001_evidence_package(
    system_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate ISO 42001 evidence package summary based on completed sections (T5.3)."""
    system = _get_system_or_404(system_id, db)
    revision = _current_revision(system, db)
    sections = _sections_for_revision(revision.id, db) if revision else []

    # A section is "completed" if it has any non-empty content
    completed = [s.section_number for s in sections if s.content]

    package = build_evidence_package(completed)
    return EvidencePackage(**package)


# ── AI Impact Assessment endpoint ─────────────────────────────────────────────


@system_router.post("/ai-ia", response_model=AIIAResponse)
def generate_ai_ia(
    system_id: uuid.UUID,
    payload: AIIARequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate AI Impact Assessment from TF section data (T5.4)."""
    system = _get_system_or_404(system_id, db)
    revision = _current_revision(system, db)
    sections_objs = _sections_for_revision(revision.id, db) if revision else []
    sections_dict: dict[int, dict] = {s.section_number: s.content or {} for s in sections_objs}

    report = build_ai_ia_report(
        system_name=system.name,
        system_description=system.description or "",
        category=system.category,
        annex_iii_flag=bool(system.annex_iii_classification),
        sections=sections_dict,
        use_llm=payload.use_llm,
    )
    return AIIAResponse(report=report)


# ── NIST AI RMF 1.0 crosswalk (T6.3) ─────────────────────────────────────────


@system_router.get("/nist-ai-rmf")
def get_nist_ai_rmf_crosswalk(
    system_id: uuid.UUID,
    section: list[int] | None = None,
    _: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the Annex IV ↔ NIST AI RMF 1.0 crosswalk (T6.3).

    Optionally filter by ``section`` query param (repeatable:
    ``?section=1&section=5``) to return only entries that reference
    those Annex IV sections.
    """
    _get_system_or_404(system_id, db)
    return get_nist_crosswalk(section_filter=section or None)


# ── Colorado AI Act (SB 24-205) crosswalk (T6.3) ──────────────────────────────


@system_router.get("/colorado-ai-act")
def get_colorado_ai_act_crosswalk(
    system_id: uuid.UUID,
    section: list[int] | None = None,
    _: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the Annex IV ↔ Colorado AI Act (SB 24-205) crosswalk (T6.3)."""
    _get_system_or_404(system_id, db)
    return get_colorado_crosswalk(section_filter=section or None)
