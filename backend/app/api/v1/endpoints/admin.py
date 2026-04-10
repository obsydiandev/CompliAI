"""Internal admin / founder metrics endpoint (Epic 8 — E8-US3 / T5.7).

Accessible only to superusers (is_superuser=True).

GET /admin/metrics   — aggregate platform metrics
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


# ── Schema ────────────────────────────────────────────────────────────────────


class PlanBreakdown(BaseModel):
    starter: int
    pro: int
    enterprise: int


class OrgMetrics(BaseModel):
    total: int
    active_trials: int
    paid: int
    plan_breakdown: PlanBreakdown


class SystemMetrics(BaseModel):
    total: int
    high_risk: int
    limited_risk: int
    minimal_risk: int
    avg_completeness_pct: float


class ComplianceMetrics(BaseModel):
    total_open_violations: int
    systems_at_risk: int


class GrowthMetrics(BaseModel):
    new_orgs_last_30d: int
    new_systems_last_30d: int


class FounderMetrics(BaseModel):
    generated_at: str
    orgs: OrgMetrics
    systems: SystemMetrics
    compliance: ComplianceMetrics
    growth: GrowthMetrics


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.get("/metrics", response_model=FounderMetrics)
def get_founder_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return aggregate platform metrics. Superuser-only."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    from app.models.ai_system import AISystem
    from app.models.organization import Organization
    from app.models.policy import ComplianceEvent
    from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
    from app.modules.annex_iv_core.completeness import calculate_revision_completeness

    now = datetime.now(UTC).replace(tzinfo=None)
    cutoff_30d = now - timedelta(days=30)

    # ── Org metrics ───────────────────────────────────────────────────────────
    all_orgs = db.query(Organization).all()
    total_orgs = len(all_orgs)
    active_trials = sum(
        1
        for o in all_orgs
        if o.trial_ends_at and o.trial_ends_at > now and o.stripe_subscription_status != "active"
    )
    paid = sum(1 for o in all_orgs if o.stripe_subscription_status in ("active", "trialing"))
    plan_breakdown = PlanBreakdown(
        starter=sum(1 for o in all_orgs if o.plan == "starter"),
        pro=sum(1 for o in all_orgs if o.plan == "pro"),
        enterprise=sum(1 for o in all_orgs if o.plan == "enterprise"),
    )

    # ── System metrics ────────────────────────────────────────────────────────
    all_systems = db.query(AISystem).all()
    total_systems = len(all_systems)
    high_risk = sum(1 for s in all_systems if s.category == "high_risk")
    limited_risk = sum(1 for s in all_systems if s.category == "limited_risk")
    minimal_risk = sum(1 for s in all_systems if s.category == "minimal_risk")

    # Average completeness (only systems with a current revision)
    completeness_values: list[float] = []
    for system in all_systems:
        tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
        if tf and tf.current_revision_id:
            rev = (
                db.query(TechnicalFileRevision)
                .filter(TechnicalFileRevision.id == tf.current_revision_id)
                .first()
            )
            if rev:
                scores, _ = calculate_revision_completeness(rev)
                if scores:
                    avg = sum(scores.values()) / len(scores)
                    completeness_values.append(avg)

    avg_completeness_pct = (
        round(sum(completeness_values) / len(completeness_values) * 100, 1)
        if completeness_values
        else 0.0
    )

    # ── Compliance metrics ────────────────────────────────────────────────────
    total_open_violations = (
        db.query(ComplianceEvent)
        .filter(ComplianceEvent.status == "open")
        .count()
    )
    # Systems with at least one open violation
    systems_at_risk = (
        db.query(ComplianceEvent.ai_system_id)
        .filter(ComplianceEvent.status == "open")
        .distinct()
        .count()
    )

    # ── Growth metrics ────────────────────────────────────────────────────────
    new_orgs_last_30d = sum(1 for o in all_orgs if o.created_at and o.created_at >= cutoff_30d)
    new_systems_last_30d = sum(
        1 for s in all_systems if s.created_at and s.created_at >= cutoff_30d
    )

    return FounderMetrics(
        generated_at=now.isoformat(),
        orgs=OrgMetrics(
            total=total_orgs,
            active_trials=active_trials,
            paid=paid,
            plan_breakdown=plan_breakdown,
        ),
        systems=SystemMetrics(
            total=total_systems,
            high_risk=high_risk,
            limited_risk=limited_risk,
            minimal_risk=minimal_risk,
            avg_completeness_pct=avg_completeness_pct,
        ),
        compliance=ComplianceMetrics(
            total_open_violations=total_open_violations,
            systems_at_risk=systems_at_risk,
        ),
        growth=GrowthMetrics(
            new_orgs_last_30d=new_orgs_last_30d,
            new_systems_last_30d=new_systems_last_30d,
        ),
    )
