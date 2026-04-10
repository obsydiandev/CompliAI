"""Built-in rule evaluator for Continuous Compliance (T4.2, T4.3).

Each built-in rule is expressed as a condition dict:
  {
      "type": "<rule_type>",
      "threshold": <int|float>,   # optional
      "section": <int>,           # optional
  }

Supported rule types:
  days_without_revision  — TF not updated in N days
  missing_pmm_plan       — Section 9 has no PMM plan content
  missing_evidence       — Section has < N evidence attachments
  unlinked_deployments   — deployments with no TF revision in last N days
  section_overdue        — a specific section not updated in N days
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def evaluate_rule(
    condition: dict[str, Any],
    system_data: dict[str, Any],
) -> tuple[bool, str]:
    """
    Evaluate a rule condition against system snapshot data.

    Parameters
    ----------
    condition:
        Rule condition dict (stored as JSON on PolicyRule.condition).
    system_data:
        Snapshot dict with keys:
          - last_revision_at: datetime | None
          - sections: dict[int, dict]  — section_number → content dict
          - evidence_counts: dict[int, int]  — section_number → count
          - unlinked_deployment_count: int
          - last_section_updated_at: dict[int, datetime | None]

    Returns
    -------
    (violated: bool, detail: str)
    """
    rule_type = condition.get("type", "")
    threshold = condition.get("threshold", 30)  # default 30 days

    now = datetime.now(UTC)

    if rule_type == "days_without_revision":
        last = system_data.get("last_revision_at")
        if last is None:
            return True, "No TF revision has been created yet."
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        days = (now - last).days
        if days > threshold:
            return True, f"TF not updated for {days} days (threshold: {threshold})."
        return False, f"Last revision {days} days ago — within threshold."

    if rule_type == "missing_pmm_plan":
        section9 = system_data.get("sections", {}).get(9, {})
        pmm_fields = ["pmm_plan", "monitoring_sources", "monitoring_metrics"]
        missing = [f for f in pmm_fields if not section9.get(f)]
        if missing:
            return True, f"Section 9 (PMM) missing fields: {', '.join(missing)}."
        return False, "Section 9 PMM plan is complete."

    if rule_type == "missing_evidence":
        section_num = condition.get("section", 4)
        min_count = int(threshold)
        count = system_data.get("evidence_counts", {}).get(section_num, 0)
        if count < min_count:
            return True, (
                f"Section {section_num} has {count} evidence items "
                f"(minimum required: {min_count})."
            )
        return False, f"Section {section_num} has {count} evidence items — OK."

    if rule_type == "unlinked_deployments":
        count = system_data.get("unlinked_deployment_count", 0)
        if count > 0:
            return True, (
                f"{count} deployment(s) not linked to a TF revision in the last "
                f"{int(threshold)} days."
            )
        return False, "All recent deployments are linked to TF revisions."

    if rule_type == "section_overdue":
        section_num = condition.get("section", 5)
        updated_at = system_data.get("last_section_updated_at", {}).get(section_num)
        if updated_at is None:
            return True, f"Section {section_num} has never been updated."
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        days = (now - updated_at).days
        if days > threshold:
            return True, (
                f"Section {section_num} not updated for {days} days "
                f"(threshold: {threshold})."
            )
        return False, f"Section {section_num} updated {days} days ago — OK."

    return False, f"Unknown rule type: {rule_type}"


def build_system_snapshot(
    system,
    revision,
    sections: list,
    evidence_counts: dict[int, int],
    unlinked_deployment_count: int,
) -> dict[str, Any]:
    """Build the system_data dict from ORM objects."""
    last_revision_at = revision.created_at if revision else None

    section_contents: dict[int, dict] = {}
    last_section_updated: dict[int, datetime | None] = {}
    for sec in sections:
        section_contents[sec.section_number] = sec.content or {}
        last_section_updated[sec.section_number] = sec.updated_at

    return {
        "last_revision_at": last_revision_at,
        "sections": section_contents,
        "evidence_counts": evidence_counts,
        "unlinked_deployment_count": unlinked_deployment_count,
        "last_section_updated_at": last_section_updated,
    }
