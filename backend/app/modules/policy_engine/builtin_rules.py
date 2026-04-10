"""Default built-in policy rule definitions (T4.3).

Call `seed_builtin_rules(org_id, db)` once per organisation to install
the 5 standard rules.  The function is idempotent — it skips rules that
already exist (matched by name + org_id).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.policy import PolicyRule

# ── Default rule catalogue ────────────────────────────────────────────────────

BUILTIN_RULE_CATALOGUE: list[dict[str, Any]] = [
    {
        "name": "TF revision overdue (30 days)",
        "description": (
            "Triggers when the Technical File has not been revised in the last 30 days."
        ),
        "condition": {"type": "days_without_revision", "threshold": 30},
        "severity": "warning",
    },
    {
        "name": "Missing PMM plan",
        "description": (
            "Triggers when Section 9 (Post-Market Monitoring) is missing key fields: "
            "pmm_plan, monitoring_sources, or monitoring_metrics."
        ),
        "condition": {"type": "missing_pmm_plan"},
        "severity": "warning",
    },
    {
        "name": "Missing validation evidence",
        "description": (
            "Triggers when Section 4 (Validation & Testing) has fewer than 1 evidence item."
        ),
        "condition": {"type": "missing_evidence", "section": 4, "threshold": 1},
        "severity": "info",
    },
    {
        "name": "Unlinked deployments",
        "description": (
            "Triggers when one or more production deployments are not linked to a "
            "TF revision within the last 30 days."
        ),
        "condition": {"type": "unlinked_deployments", "threshold": 30},
        "severity": "blocking",
    },
    {
        "name": "Risk section overdue (30 days)",
        "description": (
            "Triggers when Section 5 (Risk Management) has not been updated in 30 days."
        ),
        "condition": {"type": "section_overdue", "section": 5, "threshold": 30},
        "severity": "warning",
    },
]


def seed_builtin_rules(org_id: uuid.UUID, db: Session) -> list[PolicyRule]:
    """Install default built-in rules for an organisation (idempotent)."""
    created: list[PolicyRule] = []
    for defn in BUILTIN_RULE_CATALOGUE:
        existing = (
            db.query(PolicyRule)
            .filter(PolicyRule.org_id == org_id, PolicyRule.name == defn["name"])
            .first()
        )
        if existing:
            continue
        rule = PolicyRule(
            id=uuid.uuid4(),
            org_id=org_id,
            name=defn["name"],
            description=defn.get("description"),
            rule_type="builtin",
            condition=defn["condition"],
            severity=defn["severity"],
            is_active=True,
        )
        db.add(rule)
        created.append(rule)
    db.flush()
    return created
