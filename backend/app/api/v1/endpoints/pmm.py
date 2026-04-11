"""Post-Market Monitoring (PMM) endpoints (T4.9).

Mounted under /systems/{system_id}/pmm:
  GET    /           — Get current PMM plan (section 9 content + metrics)
  PUT    /           — Update PMM plan fields
  POST   /metrics    — Submit a monitoring metrics entry (event log)
  GET    /metrics    — List metrics history
  GET    /summary    — Aggregated PMM health summary
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.annex_iv_core.completeness import calculate_section_completeness
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS

router = APIRouter()

_PMM_SECTION = 9
_REQUIRED_PMM_FIELDS = ["pmm_plan", "monitoring_metrics", "incident_reporting_procedure"]
_ALL_PMM_FIELDS = list(ANNEX_IV_SECTIONS[_PMM_SECTION].keys())


# ── Schemas ───────────────────────────────────────────────────────────────────


class PMMPlanUpdate(BaseModel):
    pmm_plan: str | None = Field(None, description="Post-Market Monitoring plan narrative")
    monitoring_metrics: list[str] | None = Field(None, description="KPIs and metrics")
    data_collection_methods: str | None = Field(None, description="Data collection approach")
    reporting_frequency: str | None = Field(None, description="How often reports are produced")
    incident_reporting_procedure: str | None = Field(
        None, description="Procedure for reporting incidents to authorities"
    )
    feedback_mechanisms: str | None = Field(None, description="User feedback channels")
    monitoring_sources: list[str] | None = Field(
        None, description="Data sources used for monitoring"
    )
    review_schedule: str | None = Field(None, description="Schedule for PMM reviews")


class MetricEntry(BaseModel):
    metric_name: str
    value: float
    unit: str | None = None
    notes: str | None = None
    recorded_at: datetime | None = None


class MetricsSubmit(BaseModel):
    metrics: list[MetricEntry] = Field(..., min_length=1)


class PMMSummary(BaseModel):
    completeness: float
    missing_fields: list[str]
    has_plan: bool
    has_metrics: bool
    has_incident_procedure: bool
    last_section_updated_at: datetime | None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_system(system_id: uuid.UUID, user: User, db: Session) -> AISystem:
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
    return system


def _get_current_section9(system: AISystem, db: Session) -> Section | None:
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        return None
    revision = None
    if tf.current_revision_id:
        revision = (
            db.query(TechnicalFileRevision)
            .filter(TechnicalFileRevision.id == tf.current_revision_id)
            .first()
        )
    if not revision:
        revision = (
            db.query(TechnicalFileRevision)
            .filter(TechnicalFileRevision.tf_id == tf.id)
            .order_by(TechnicalFileRevision.created_at.desc())
            .first()
        )
    if not revision:
        return None
    return (
        db.query(Section)
        .filter(Section.revision_id == revision.id, Section.section_number == _PMM_SECTION)
        .first()
    )


def _get_current_revision(system: AISystem, db: Session) -> TechnicalFileRevision | None:
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        return None
    if tf.current_revision_id:
        rev = (
            db.query(TechnicalFileRevision)
            .filter(TechnicalFileRevision.id == tf.current_revision_id)
            .first()
        )
        if rev:
            return rev
    return (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.tf_id == tf.id)
        .order_by(TechnicalFileRevision.created_at.desc())
        .first()
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/")
def get_pmm_plan(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the current PMM plan (section 9 content) for the system."""
    system = _get_system(system_id, current_user, db)
    section = _get_current_section9(system, db)
    content = section.content if section else {}
    completeness = calculate_section_completeness(_PMM_SECTION, content)

    missing_fields = [
        f for f in _REQUIRED_PMM_FIELDS if not content.get(f)
    ]

    return {
        "system_id": str(system_id),
        "system_name": system.name,
        "content": content,
        "completeness": completeness,
        "missing_required_fields": missing_fields,
        "last_updated_at": section.last_updated_at if section else None,
        "all_fields": _ALL_PMM_FIELDS,
    }


@router.put("/", response_model=dict)
def update_pmm_plan(
    system_id: uuid.UUID,
    payload: PMMPlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Merge payload fields into the section 9 content of the current revision."""
    system = _get_system(system_id, current_user, db)
    revision = _get_current_revision(system, db)
    if not revision:
        raise HTTPException(
            status_code=404,
            detail="No technical file revision found. Create a revision first.",
        )

    section = (
        db.query(Section)
        .filter(Section.revision_id == revision.id, Section.section_number == _PMM_SECTION)
        .first()
    )
    if not section:
        section = Section(
            id=uuid.uuid4(),
            revision_id=revision.id,
            section_number=_PMM_SECTION,
            content={},
            completeness_score=0.0,
        )
        db.add(section)

    updates = payload.model_dump(exclude_none=True)
    content = dict(section.content or {})
    content.update(updates)
    section.content = content
    section.last_updated_at = datetime.now(UTC)
    section.completeness_score = calculate_section_completeness(_PMM_SECTION, content)

    db.commit()
    db.refresh(section)

    missing_fields = [f for f in _REQUIRED_PMM_FIELDS if not content.get(f)]
    return {
        "system_id": str(system_id),
        "content": content,
        "completeness": section.completeness_score,
        "missing_required_fields": missing_fields,
        "last_updated_at": section.last_updated_at,
    }


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def submit_metrics(
    system_id: uuid.UUID,
    payload: MetricsSubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Record a monitoring metrics snapshot for the system.

    Metrics are persisted as a JSON entry appended to the
    ``monitoring_metrics_log`` field inside section 9 content.
    """
    system = _get_system(system_id, current_user, db)
    revision = _get_current_revision(system, db)
    if not revision:
        raise HTTPException(
            status_code=404,
            detail="No technical file revision found. Create a revision first.",
        )

    section = (
        db.query(Section)
        .filter(Section.revision_id == revision.id, Section.section_number == _PMM_SECTION)
        .first()
    )
    if not section:
        section = Section(
            id=uuid.uuid4(),
            revision_id=revision.id,
            section_number=_PMM_SECTION,
            content={},
            completeness_score=0.0,
        )
        db.add(section)
        db.flush()

    content = dict(section.content or {})
    log: list[dict[str, Any]] = list(content.get("monitoring_metrics_log") or [])

    entry: dict[str, Any] = {
        "recorded_at": (
            payload.metrics[0].recorded_at or datetime.now(UTC)
        ).isoformat(),
        "submitted_by": str(current_user.id),
        "metrics": [
            {
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "notes": m.notes,
            }
            for m in payload.metrics
        ],
    }
    log.append(entry)
    content["monitoring_metrics_log"] = log
    section.content = content
    section.last_updated_at = datetime.now(UTC)
    section.completeness_score = calculate_section_completeness(_PMM_SECTION, content)

    db.commit()

    return {
        "recorded_entries": len(payload.metrics),
        "total_log_entries": len(log),
        "recorded_at": entry["recorded_at"],
    }


@router.get("/metrics")
def list_metrics(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the full monitoring metrics log for the system."""
    system = _get_system(system_id, current_user, db)
    section = _get_current_section9(system, db)
    content = section.content if section else {}
    log = content.get("monitoring_metrics_log") or []
    return {
        "system_id": str(system_id),
        "total_entries": len(log),
        "entries": log,
    }


@router.get("/summary", response_model=PMMSummary)
def pmm_summary(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PMMSummary:
    """Return a concise PMM health summary for the system."""
    system = _get_system(system_id, current_user, db)
    section = _get_current_section9(system, db)
    content = section.content if section else {}

    completeness = calculate_section_completeness(_PMM_SECTION, content)
    missing_fields = [f for f in _REQUIRED_PMM_FIELDS if not content.get(f)]

    return PMMSummary(
        completeness=completeness,
        missing_fields=missing_fields,
        has_plan=bool(content.get("pmm_plan")),
        has_metrics=bool(content.get("monitoring_metrics")),
        has_incident_procedure=bool(content.get("incident_reporting_procedure")),
        last_section_updated_at=section.last_updated_at if section else None,
    )
