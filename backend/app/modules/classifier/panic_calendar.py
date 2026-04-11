"""AI Act deadline calendar — computes days remaining to key enforcement milestones.

Key dates (based on Regulation (EU) 2024/1689):
  - 2024-08-01: Regulation entered into force
  - 2025-02-02: Chapter I (definitions) and Chapter II (prohibited AI) apply
  - 2025-08-02: GPAI model rules apply
  - 2026-08-02: High-Risk AI systems (Annex III) must comply — Annex IV mandatory
  - 2027-08-02: Annex I high-risk AI (safety components) must comply
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone


@dataclass
class Milestone:
    date: date
    label: str
    description: str
    article_ref: str


AI_ACT_MILESTONES: list[Milestone] = [
    Milestone(
        date=date(2025, 2, 2),
        label="Prohibited AI practices",
        description="Chapter II (Art. 5) prohibited AI practices apply — real-time biometric ID bans, social scoring prohibitions.",
        article_ref="Art. 5 AI Act",
    ),
    Milestone(
        date=date(2025, 8, 2),
        label="GPAI model rules",
        description="General-purpose AI model rules (Art. 51–56) apply. Providers of GPAI models must comply with transparency and copyright obligations.",
        article_ref="Art. 51–56 AI Act",
    ),
    Milestone(
        date=date(2026, 8, 2),
        label="High-Risk Annex III deadline",
        description="High-risk AI systems listed in Annex III must comply with all requirements including Annex IV Technical File, conformity assessment, and registration.",
        article_ref="Art. 6(2) + Annex III AI Act",
    ),
    Milestone(
        date=date(2027, 8, 2),
        label="High-Risk Annex I (safety components)",
        description="High-risk AI systems that are safety components of products covered by Annex I sector legislation must comply.",
        article_ref="Art. 6(1) + Annex I AI Act",
    ),
]


def get_panic_calendar(reference_date: date | None = None) -> list[dict]:
    """Return a list of milestone dicts with days_remaining and urgency colour.

    Args:
        reference_date: date to calculate from (defaults to today UTC).

    Returns list of dicts with keys:
        date, label, description, article_ref, days_remaining, urgency
        where urgency is "past" | "green" | "orange" | "red"
    """
    today = reference_date or datetime.now(timezone.utc).date()
    result = []
    for m in AI_ACT_MILESTONES:
        days = (m.date - today).days
        if days < 0:
            urgency = "past"
        elif days <= 60:
            urgency = "red"
        elif days <= 90:
            urgency = "orange"
        else:
            urgency = "green"

        result.append(
            {
                "date": m.date.isoformat(),
                "label": m.label,
                "description": m.description,
                "article_ref": m.article_ref,
                "days_remaining": max(0, days),
                "urgency": urgency,
            }
        )
    return result


def get_primary_deadline(risk_level: str, reference_date: date | None = None) -> dict:
    """Return the most relevant milestone for a given risk level."""
    calendar = get_panic_calendar(reference_date)
    if risk_level == "high_risk":
        # Primary deadline: Annex III 2026-08-02
        for m in calendar:
            if "Annex III" in m["label"]:
                return m
    # For limited/minimal: return the first future milestone
    today = reference_date or datetime.now(timezone.utc).date()
    for m in calendar:
        if m["days_remaining"] > 0:
            return m
    return calendar[-1]
