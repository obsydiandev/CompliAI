"""Policy Engine API endpoints (Epic 5 / Faza 4).

System-scoped (mounted under /systems/{system_id}/compliance):
  GET    /health                        — Compliance Health dashboard
  POST   /run-checks                    — Evaluate all active rules
  POST   /shadow-validate               — Shadow Mode Validation
  POST   /bias-audit                    — Automated Bias Audit
  GET    /events                        — List compliance events
  PUT    /events/{event_id}/resolve     — Resolve a compliance event

Org-scoped (mounted under /organizations/{org_id}/policies):
  GET    /                              — List policy rules
  POST   /                             — Create custom rule
  GET    /{rule_id}                    — Get rule
  PUT    /{rule_id}                    — Update rule
  DELETE /{rule_id}                   — Delete rule
  POST   /seed-builtin                 — Install default built-in rules
  POST   /generate-rule                — LLM: natural language → condition (T4.4)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_active_user, get_org_context, require_role
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.deployment import DeploymentEvent
from app.models.evidence import EvidenceAttachment
from app.models.policy import Alert, ComplianceEvent, OrgAlertConfig, PolicyRule
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.annex_iv_core.completeness import (
    calculate_revision_completeness,
    calculate_section_completeness,
)
from app.modules.annex_iv_core.schemas import SECTION_NAMES
from app.modules.policy_engine import alert_dispatcher, bias_audit, shadow_validator
from app.modules.policy_engine.builtin_rules import seed_builtin_rules
from app.modules.policy_engine.rule_evaluator import build_system_snapshot, evaluate_rule
from app.modules.policy_engine.rule_generator import generate_rule_from_text, suggest_rule_name
from app.schemas.policy import (
    BiasAuditRequest,
    BiasAuditResponse,
    ComplianceEventRead,
    ComplianceHealthReport,
    GenerateRuleRequest,
    GenerateRuleResponse,
    PolicyRuleCreate,
    PolicyRuleRead,
    PolicyRuleUpdate,
    RunChecksResponse,
    SectionDebt,
    ShadowValidationRequest,
    ShadowValidationResponse,
)

# ── Routers ───────────────────────────────────────────────────────────────────

# Org-scoped (mounted under /organizations/{org_id}/policies)
org_router = APIRouter()

# System-scoped (mounted under /systems/{system_id}/compliance)
system_router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_system_or_404(system_id: uuid.UUID, db: Session) -> AISystem:
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    return system


def _get_rule_or_404(rule_id: uuid.UUID, org_id: uuid.UUID, db: Session) -> PolicyRule:
    rule = (
        db.query(PolicyRule)
        .filter(PolicyRule.id == rule_id, PolicyRule.org_id == org_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return rule


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
    # Fallback: latest revision
    return (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.tf_id == tf.id)
        .order_by(TechnicalFileRevision.created_at.desc())
        .first()
    )


def _sections_for_revision(revision_id: uuid.UUID, db: Session) -> list[Section]:
    return db.query(Section).filter(Section.revision_id == revision_id).all()


# ── Org-scoped policy rule endpoints ─────────────────────────────────────────


# ── Alert notification configuration (T4.8) ──────────────────────────────────


class _AlertConfigUpdate(BaseModel):
    email_enabled: bool = False
    email_recipients: list[str] = []
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    webhook_enabled: bool = False
    webhook_url: str = ""
    min_severity: str = "warning"


@org_router.get("/alert-config", tags=["policy"])
def get_alert_config(
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Return the alert notification configuration for this organisation."""
    cfg = (
        db.query(OrgAlertConfig)
        .filter(OrgAlertConfig.org_id == ctx.current_org.id)
        .first()
    )
    if not cfg:
        return {
            "email_enabled": False,
            "email_recipients": [],
            "slack_enabled": False,
            "slack_webhook_url": "",
            "webhook_enabled": False,
            "webhook_url": "",
            "min_severity": "warning",
        }
    return {
        "email_enabled": cfg.email_enabled,
        "email_recipients": cfg.email_recipients or [],
        "slack_enabled": cfg.slack_enabled,
        "slack_webhook_url": cfg.slack_webhook_url or "",
        "webhook_enabled": cfg.webhook_enabled,
        "webhook_url": cfg.webhook_url or "",
        "min_severity": cfg.min_severity,
    }


@org_router.put("/alert-config", tags=["policy"])
def update_alert_config(
    body: _AlertConfigUpdate,
    ctx: OrgContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create or update the alert notification configuration for this organisation."""
    allowed_severities = {"info", "warning", "blocking"}
    if body.min_severity not in allowed_severities:
        raise HTTPException(
            status_code=400,
            detail=f"min_severity must be one of: {sorted(allowed_severities)}",
        )

    cfg = (
        db.query(OrgAlertConfig)
        .filter(OrgAlertConfig.org_id == ctx.current_org.id)
        .first()
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    if cfg is None:
        cfg = OrgAlertConfig(
            id=uuid.uuid4(),
            org_id=ctx.current_org.id,
            created_at=now,
        )
        db.add(cfg)

    cfg.email_enabled = body.email_enabled
    cfg.email_recipients = body.email_recipients or []
    cfg.slack_enabled = body.slack_enabled
    cfg.slack_webhook_url = body.slack_webhook_url or None
    cfg.webhook_enabled = body.webhook_enabled
    cfg.webhook_url = body.webhook_url or None
    cfg.min_severity = body.min_severity
    cfg.updated_at = now

    db.commit()
    db.refresh(cfg)
    return {
        "email_enabled": cfg.email_enabled,
        "email_recipients": cfg.email_recipients or [],
        "slack_enabled": cfg.slack_enabled,
        "slack_webhook_url": cfg.slack_webhook_url or "",
        "webhook_enabled": cfg.webhook_enabled,
        "webhook_url": cfg.webhook_url or "",
        "min_severity": cfg.min_severity,
    }


@org_router.get("", response_model=list[PolicyRuleRead])
def list_rules(
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    return (
        db.query(PolicyRule)
        .filter(PolicyRule.org_id == ctx.current_org.id)
        .order_by(PolicyRule.created_at)
        .all()
    )


@org_router.post("", response_model=PolicyRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: PolicyRuleCreate,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    rule = PolicyRule(
        id=uuid.uuid4(),
        org_id=ctx.current_org.id,
        ai_system_id=payload.ai_system_id,
        name=payload.name,
        description=payload.description,
        rule_type="custom",
        condition=payload.condition,
        severity=payload.severity,
        is_active=payload.is_active,
        created_by=ctx.current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@org_router.get("/{rule_id}", response_model=PolicyRuleRead)
def get_rule(
    rule_id: uuid.UUID,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    return _get_rule_or_404(rule_id, ctx.current_org.id, db)


@org_router.put("/{rule_id}", response_model=PolicyRuleRead)
def update_rule(
    rule_id: uuid.UUID,
    payload: PolicyRuleUpdate,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    rule = _get_rule_or_404(rule_id, ctx.current_org.id, db)
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(rule, field, val)
    db.commit()
    db.refresh(rule)
    return rule


@org_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    rule = _get_rule_or_404(rule_id, ctx.current_org.id, db)
    db.delete(rule)
    db.commit()


@org_router.post("/seed-builtin", response_model=list[PolicyRuleRead])
def seed_builtin(
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Install the 5 default built-in rules for this organisation (idempotent)."""
    created = seed_builtin_rules(ctx.current_org.id, db)
    db.commit()
    return created


@org_router.post("/generate-rule", response_model=GenerateRuleResponse)
def generate_rule(
    payload: GenerateRuleRequest,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Convert natural-language policy text to a structured rule condition (T4.4).

    Uses OpenAI to parse the description and returns a condition dict plus a
    suggested rule name, which the caller can then POST to ``/policies`` to
    persist as a custom rule.
    """
    from app.config import settings

    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI rule generation requires OPENAI_API_KEY to be configured.",
        )

    try:
        condition = generate_rule_from_text(
            payload.description,
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    suggested_name = suggest_rule_name(payload.description, condition)
    return GenerateRuleResponse(
        suggested_name=suggested_name,
        condition=condition,
        description=payload.description,
    )


# ── System-scoped compliance endpoints ───────────────────────────────────────


@system_router.get("/health", response_model=ComplianceHealthReport)
def compliance_health(
    system_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Compliance Health dashboard — debt metrics for a single AI system (T4.5)."""
    system = _get_system_or_404(system_id, db)
    revision = _current_revision(system, db)
    sections = _sections_for_revision(revision.id, db) if revision else []

    # Days since last revision
    days_since: int | None = None
    if revision:
        ts = revision.created_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        days_since = (datetime.now(UTC) - ts).days

    # Per-section completeness + debt
    section_debt: list[SectionDebt] = []
    overall_completeness = 0.0
    if sections:
        comp = calculate_revision_completeness(sections)
        scores: dict[int, float] = comp["section_scores"]
        missing_map: dict[int, list[str]] = comp["missing_by_section"]
        overall_completeness = comp["overall"]

        for num in range(1, 10):
            score = scores.get(num, 0.0)
            missing = missing_map.get(num, [])

            # Days since section updated
            sec_obj = next((s for s in sections if s.section_number == num), None)
            days_sec: int | None = None
            if sec_obj and sec_obj.updated_at:
                ts2 = sec_obj.updated_at
                if ts2.tzinfo is None:
                    ts2 = ts2.replace(tzinfo=UTC)
                days_sec = (datetime.now(UTC) - ts2).days

            section_debt.append(
                SectionDebt(
                    section_number=num,
                    section_name=SECTION_NAMES.get(num, f"Section {num}"),
                    completeness=round(score, 3),
                    missing_fields=missing,
                    days_since_update=days_sec,
                )
            )

    # Evidence counts per section
    evidence_counts: dict[int, int] = {}
    if revision:
        for sec in sections:
            count = (
                db.query(EvidenceAttachment)
                .filter(
                    EvidenceAttachment.ai_system_id == system_id,
                    EvidenceAttachment.section_number == sec.section_number,
                )
                .count()
            )
            evidence_counts[sec.section_number] = count
    missing_evidence_total = sum(1 for c in evidence_counts.values() if c == 0)

    # Unlinked deployments (significant deployments without TF revision)
    unlinked = (
        db.query(DeploymentEvent)
        .filter(
            DeploymentEvent.ai_system_id == system_id,
            DeploymentEvent.is_significant == True,  # noqa: E712
            DeploymentEvent.tf_revision_id.is_(None),
        )
        .count()
    )

    # Open compliance events
    open_events = (
        db.query(ComplianceEvent)
        .filter(
            ComplianceEvent.ai_system_id == system_id,
            ComplianceEvent.status == "open",
        )
        .order_by(ComplianceEvent.triggered_at.desc())
        .limit(20)
        .all()
    )

    return ComplianceHealthReport(
        ai_system_id=system_id,
        system_name=system.name,
        days_since_last_revision=days_since,
        overall_completeness=round(overall_completeness, 3),
        open_violations=len(open_events),
        unlinked_deployments=unlinked,
        missing_evidence_count=missing_evidence_total,
        section_debt=section_debt,
        open_events=[ComplianceEventRead.model_validate(e) for e in open_events],
    )


@system_router.post("/run-checks", response_model=RunChecksResponse)
def run_checks(
    system_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Evaluate all active policy rules for a system and create violation events (T4.2)."""
    system = _get_system_or_404(system_id, db)
    revision = _current_revision(system, db)
    sections = _sections_for_revision(revision.id, db) if revision else []

    evidence_counts: dict[int, int] = {}
    for sec in sections:
        evidence_counts[sec.section_number] = (
            db.query(EvidenceAttachment)
            .filter(
                EvidenceAttachment.ai_system_id == system_id,
                EvidenceAttachment.section_number == sec.section_number,
            )
            .count()
        )

    unlinked = (
        db.query(DeploymentEvent)
        .filter(
            DeploymentEvent.ai_system_id == system_id,
            DeploymentEvent.is_significant == True,  # noqa: E712
            DeploymentEvent.tf_revision_id.is_(None),
        )
        .count()
    )

    snapshot = build_system_snapshot(
        system, revision, sections, evidence_counts, unlinked
    )

    # Fetch applicable rules (org-wide + system-specific)
    rules = (
        db.query(PolicyRule)
        .filter(
            PolicyRule.org_id == system.org_id,
            PolicyRule.is_active == True,  # noqa: E712
        )
        .filter(
            (PolicyRule.ai_system_id == system_id) | (PolicyRule.ai_system_id.is_(None))
        )
        .all()
    )

    evaluated = 0
    violations = 0
    events_created = 0
    results: list[dict[str, Any]] = []

    for rule in rules:
        violated, detail = evaluate_rule(rule.condition, snapshot)
        evaluated += 1

        row: dict[str, Any] = {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "violated": violated,
            "detail": detail,
        }

        if violated:
            violations += 1
            # Create compliance event (deduplicate: only if no open event for this rule+system)
            existing = (
                db.query(ComplianceEvent)
                .filter(
                    ComplianceEvent.rule_id == rule.id,
                    ComplianceEvent.ai_system_id == system_id,
                    ComplianceEvent.status == "open",
                )
                .first()
            )
            if not existing:
                event = ComplianceEvent(
                    id=uuid.uuid4(),
                    rule_id=rule.id,
                    ai_system_id=system_id,
                    status="open",
                    details={"message": detail},
                )
                db.add(event)
                db.flush()

                # Create in-app alert
                alert = Alert(
                    id=uuid.uuid4(),
                    compliance_event_id=event.id,
                    channel="in_app",
                )
                db.add(alert)

                events_created += 1
                row["event_id"] = str(event.id)

                # Build alert payload once
                alert_payload = {
                    "rule_name": rule.name,
                    "message": detail,
                    "severity": rule.severity,
                    "system_name": system.name,
                }

                # Dispatch in-app alert (always)
                alert_dispatcher.dispatch_alert(
                    channel="in_app",
                    recipient=None,
                    payload=alert_payload,
                )

                # Dispatch via configured channels if alert config exists and
                # severity meets the minimum threshold
                _sev_order = {"info": 0, "warning": 1, "blocking": 2}
                alert_cfg = (
                    db.query(OrgAlertConfig)
                    .filter(OrgAlertConfig.org_id == system.org_id)
                    .first()
                )
                if alert_cfg:
                    rule_sev = _sev_order.get(rule.severity, 0)
                    min_sev = _sev_order.get(alert_cfg.min_severity, 1)
                    if rule_sev >= min_sev:
                        if alert_cfg.email_enabled:
                            for recipient in (alert_cfg.email_recipients or []):
                                alert_dispatcher.dispatch_alert(
                                    channel="email",
                                    recipient=recipient,
                                    payload=alert_payload,
                                )
                        if alert_cfg.slack_enabled and alert_cfg.slack_webhook_url:
                            alert_dispatcher.dispatch_alert(
                                channel="slack",
                                recipient=alert_cfg.slack_webhook_url,
                                payload=alert_payload,
                            )
                        if alert_cfg.webhook_enabled and alert_cfg.webhook_url:
                            alert_dispatcher.dispatch_alert(
                                channel="webhook",
                                recipient=alert_cfg.webhook_url,
                                payload=alert_payload,
                            )

        results.append(row)

    db.commit()

    return RunChecksResponse(
        evaluated=evaluated,
        violations=violations,
        events_created=events_created,
        results=results,
    )


@system_router.post("/shadow-validate", response_model=ShadowValidationResponse)
def shadow_validate(
    system_id: uuid.UUID,
    payload: ShadowValidationRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Shadow Mode Validation — compare new model metrics vs TF thresholds (T4.6)."""
    system = _get_system_or_404(system_id, db)
    revision = _current_revision(system, db)
    sections = _sections_for_revision(revision.id, db) if revision else []

    sec4 = next((s for s in sections if s.section_number == 4), None)
    sec5 = next((s for s in sections if s.section_number == 5), None)

    result = shadow_validator.validate_shadow(
        new_metrics=payload.new_metrics,
        tf_section4_content=sec4.content if sec4 else {},
        tf_section5_content=sec5.content if sec5 else {},
        threshold_pct=payload.threshold_pct,
    )
    return ShadowValidationResponse(
        ok=result.ok,
        summary=result.summary,
        sections_requiring_update=result.sections_requiring_update,
        details=result.details,
    )


@system_router.post("/bias-audit", response_model=BiasAuditResponse)
def run_bias_audit(
    system_id: uuid.UUID,
    payload: BiasAuditRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Automated Bias Audit — fairness metrics comparison (T4.7)."""
    _get_system_or_404(system_id, db)

    report = bias_audit.run_bias_audit(
        previous_metrics=payload.previous_metrics,
        current_metrics=payload.current_metrics,
        thresholds=payload.custom_thresholds,
    )
    return BiasAuditResponse(
        ok=report.ok,
        summary=report.summary,
        metrics=[
            {
                "metric": m.metric,
                "previous": m.previous,
                "current": m.current,
                "delta": m.delta,
                "status": m.status,
                "message": m.message,
            }
            for m in report.metrics
        ],
        section5_evidence=report.section5_evidence,
    )


@system_router.get("/events", response_model=list[ComplianceEventRead])
def list_events(
    system_id: uuid.UUID,
    status_filter: str | None = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _get_system_or_404(system_id, db)
    q = db.query(ComplianceEvent).filter(ComplianceEvent.ai_system_id == system_id)
    if status_filter:
        q = q.filter(ComplianceEvent.status == status_filter)
    return q.order_by(ComplianceEvent.triggered_at.desc()).limit(100).all()


@system_router.put("/events/{event_id}/resolve", response_model=ComplianceEventRead)
def resolve_event(
    system_id: uuid.UUID,
    event_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _get_system_or_404(system_id, db)
    event = (
        db.query(ComplianceEvent)
        .filter(
            ComplianceEvent.id == event_id,
            ComplianceEvent.ai_system_id == system_id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Compliance event not found")
    event.status = "resolved"
    event.resolved_at = datetime.now(UTC)
    event.resolved_by = user.id
    db.commit()
    db.refresh(event)
    return event
