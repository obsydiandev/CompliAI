"""Celery tasks for periodic compliance checks (T4.2).

These tasks are executed by the Celery worker and beat scheduler.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


def _get_db_session():
    """Create a standalone database session for use inside tasks."""
    from app.database import SessionLocal

    return SessionLocal()


@shared_task(name="app.tasks.compliance.run_periodic_compliance_checks", bind=True, max_retries=3)
def run_periodic_compliance_checks(self) -> dict[str, Any]:
    """Run compliance checks for ALL active AI systems across all organisations.

    This task is scheduled by Celery Beat to run at a configurable interval
    (default: every hour). For each active system it:
      1. Evaluates all active policy rules.
      2. Creates ComplianceEvent records for new violations.
      3. Dispatches in-app alerts (and email/Slack if configured).

    Returns a summary dict with counts.
    """
    from app.models.ai_system import AISystem
    from app.models.deployment import DeploymentEvent
    from app.models.evidence import EvidenceAttachment
    from app.models.policy import Alert, ComplianceEvent, PolicyRule
    from app.models.technical_file import TechnicalFile, TechnicalFileRevision, Section
    from app.modules.policy_engine import alert_dispatcher
    from app.modules.policy_engine.rule_evaluator import build_system_snapshot, evaluate_rule

    db = _get_db_session()
    try:
        systems = (
            db.query(AISystem)
            .filter(AISystem.status == "active")
            .all()
        )

        total_systems = len(systems)
        total_violations = 0
        total_events_created = 0

        for system in systems:
            try:
                _check_system(system, db, alert_dispatcher, evaluate_rule, build_system_snapshot,
                              AISystem, TechnicalFile, TechnicalFileRevision, Section,
                              EvidenceAttachment, DeploymentEvent, PolicyRule,
                              ComplianceEvent, Alert)
                db.commit()
            except Exception as exc:
                logger.error(
                    "[PeriodicCheck] Error checking system %s: %s",
                    system.id,
                    exc,
                )
                db.rollback()

        logger.info(
            "[PeriodicCheck] Done — systems=%d violations=%d events_created=%d",
            total_systems,
            total_violations,
            total_events_created,
        )
        return {
            "total_systems": total_systems,
            "total_violations": total_violations,
            "total_events_created": total_events_created,
        }
    except Exception as exc:
        logger.error("[PeriodicCheck] Task failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


def _check_system(
    system,
    db,
    alert_dispatcher,
    evaluate_rule,
    build_system_snapshot,
    AISystem,
    TechnicalFile,
    TechnicalFileRevision,
    Section,
    EvidenceAttachment,
    DeploymentEvent,
    PolicyRule,
    ComplianceEvent,
    Alert,
) -> tuple[int, int]:
    """Run policy checks for a single system. Returns (violations, events_created)."""
    # Resolve current revision
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    revision = None
    if tf:
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

    sections = []
    if revision:
        sections = db.query(Section).filter(Section.revision_id == revision.id).all()

    evidence_counts: dict[int, int] = {}
    for sec in sections:
        evidence_counts[sec.section_number] = (
            db.query(EvidenceAttachment)
            .filter(
                EvidenceAttachment.ai_system_id == system.id,
                EvidenceAttachment.section_number == sec.section_number,
            )
            .count()
        )

    unlinked = (
        db.query(DeploymentEvent)
        .filter(
            DeploymentEvent.ai_system_id == system.id,
            DeploymentEvent.is_significant == True,  # noqa: E712
            DeploymentEvent.tf_revision_id.is_(None),
        )
        .count()
    )

    snapshot = build_system_snapshot(system, revision, sections, evidence_counts, unlinked)

    rules = (
        db.query(PolicyRule)
        .filter(
            PolicyRule.org_id == system.org_id,
            PolicyRule.is_active == True,  # noqa: E712
        )
        .filter(
            (PolicyRule.ai_system_id == system.id) | (PolicyRule.ai_system_id.is_(None))
        )
        .all()
    )

    violations = 0
    events_created = 0

    for rule in rules:
        violated, detail = evaluate_rule(rule.condition, snapshot)
        if not violated:
            continue

        violations += 1
        existing = (
            db.query(ComplianceEvent)
            .filter(
                ComplianceEvent.rule_id == rule.id,
                ComplianceEvent.ai_system_id == system.id,
                ComplianceEvent.status == "open",
            )
            .first()
        )
        if existing:
            continue

        event = ComplianceEvent(
            id=uuid.uuid4(),
            rule_id=rule.id,
            ai_system_id=system.id,
            status="open",
            details={"message": detail, "source": "periodic_check"},
        )
        db.add(event)
        db.flush()

        alert = Alert(
            id=uuid.uuid4(),
            compliance_event_id=event.id,
            channel="in_app",
        )
        db.add(alert)
        events_created += 1

        alert_dispatcher.dispatch_alert(
            channel="in_app",
            recipient=None,
            payload={
                "rule_name": rule.name,
                "message": detail,
                "severity": rule.severity,
                "system_name": system.name,
            },
        )

    return violations, events_created


@shared_task(name="app.tasks.compliance.send_pmm_reminders", bind=True)
def send_pmm_reminders(self) -> dict[str, Any]:
    """Send daily reminders for systems with missing or overdue PMM plans.

    Checks all active high-risk systems whose PMM section (section 9) is
    incomplete and dispatches email/in-app alerts if SMTP is configured.
    """
    from app.models.ai_system import AISystem
    from app.models.technical_file import TechnicalFile, TechnicalFileRevision, Section
    from app.modules.policy_engine import alert_dispatcher

    db = _get_db_session()
    try:
        systems = (
            db.query(AISystem)
            .filter(AISystem.status == "active", AISystem.category == "high_risk")
            .all()
        )

        reminded = 0
        for system in systems:
            try:
                tf = db.query(TechnicalFile).filter(
                    TechnicalFile.ai_system_id == system.id
                ).first()
                if not tf:
                    continue

                revision = (
                    db.query(TechnicalFileRevision)
                    .filter(TechnicalFileRevision.tf_id == tf.id)
                    .order_by(TechnicalFileRevision.created_at.desc())
                    .first()
                )
                if not revision:
                    continue

                section9 = (
                    db.query(Section)
                    .filter(
                        Section.revision_id == revision.id,
                        Section.section_number == 9,
                    )
                    .first()
                )
                content = section9.content if section9 else {}
                pmm_fields = ["pmm_plan", "monitoring_sources", "monitoring_metrics"]
                missing = [f for f in pmm_fields if not content.get(f)]
                if not missing:
                    continue

                alert_dispatcher.dispatch_alert(
                    channel="in_app",
                    recipient=None,
                    payload={
                        "rule_name": "PMM Plan Reminder",
                        "message": (
                            f"Section 9 (Post-Market Monitoring) is missing fields: "
                            f"{', '.join(missing)}. Please update to maintain compliance."
                        ),
                        "severity": "warning",
                        "system_name": system.name,
                    },
                )
                reminded += 1
            except Exception as exc:
                logger.error("[PMMReminder] System %s error: %s", system.id, exc)

        logger.info("[PMMReminder] Sent reminders for %d systems", reminded)
        return {"reminded": reminded}
    finally:
        db.close()
