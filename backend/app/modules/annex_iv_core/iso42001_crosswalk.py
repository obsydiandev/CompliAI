"""Crosswalk: Annex IV (AI Act) ↔ ISO/IEC 42001:2023 (T5.3 / Epic 6).

Each entry maps an ISO 42001 control clause to the Annex IV section(s)
it is evidenced by, plus a short description of the linkage.
"""

from __future__ import annotations

from typing import Any

# Format:
# {
#   "iso_clause": str,
#   "iso_title": str,
#   "annex_iv_sections": list[int],
#   "coverage": "full" | "partial" | "supplementary",
#   "notes": str,
# }

ISO_42001_CROSSWALK: list[dict[str, Any]] = [
    {
        "iso_clause": "4.1",
        "iso_title": "Understanding the organization and its context",
        "annex_iv_sections": [1],
        "coverage": "partial",
        "notes": (
            "Section 1 (General Description, Intended Purpose) addresses organizational "
            "context for the AI system. Supplement with organizational scope statement."
        ),
    },
    {
        "iso_clause": "4.2",
        "iso_title": "Understanding the needs of interested parties",
        "annex_iv_sections": [1, 8],
        "coverage": "partial",
        "notes": (
            "Section 1 identifies users and use cases; Section 8 addresses human oversight "
            "interfaces. Supplement with stakeholder register."
        ),
    },
    {
        "iso_clause": "5.2",
        "iso_title": "AI Policy",
        "annex_iv_sections": [7],
        "coverage": "supplementary",
        "notes": (
            "Section 7 (Standards & Norms) lists applicable standards. "
            "ISO 42001 requires a formal AI policy document at organizational level."
        ),
    },
    {
        "iso_clause": "6.1",
        "iso_title": "Actions to address risks and opportunities",
        "annex_iv_sections": [5],
        "coverage": "full",
        "notes": (
            "Section 5 (Risk Management) provides the risk register, controls, and "
            "residual risk — directly evidences this clause."
        ),
    },
    {
        "iso_clause": "6.1.2",
        "iso_title": "AI risk assessment",
        "annex_iv_sections": [5],
        "coverage": "full",
        "notes": "Section 5 risk register with impact/likelihood assessment.",
    },
    {
        "iso_clause": "6.1.3",
        "iso_title": "AI risk treatment",
        "annex_iv_sections": [5, 8],
        "coverage": "full",
        "notes": (
            "Section 5 mitigation measures + Section 8 human oversight as a risk control."
        ),
    },
    {
        "iso_clause": "8.4",
        "iso_title": "AI system impact assessment",
        "annex_iv_sections": [1, 5],
        "coverage": "partial",
        "notes": (
            "Annex IV Section 1 + 5 together provide input for an AI IA. "
            "Use AI Impact Assessment generator for a standalone report."
        ),
    },
    {
        "iso_clause": "8.5",
        "iso_title": "AI system life cycle",
        "annex_iv_sections": [2, 3, 4, 6],
        "coverage": "full",
        "notes": (
            "Section 2 (Design), Section 3 (Data), Section 4 (Validation), "
            "Section 6 (Lifecycle Changes) together cover the full AI lifecycle."
        ),
    },
    {
        "iso_clause": "8.6",
        "iso_title": "AI system operation and monitoring",
        "annex_iv_sections": [9],
        "coverage": "full",
        "notes": (
            "Section 9 (Post-Market Monitoring) covers operational monitoring, "
            "KPI tracking, and periodic reporting."
        ),
    },
    {
        "iso_clause": "8.7",
        "iso_title": "AI system review and improvement",
        "annex_iv_sections": [6, 9],
        "coverage": "full",
        "notes": (
            "Section 6 (Lifecycle Changes) documents revisions; "
            "Section 9 feeds improvement decisions."
        ),
    },
    {
        "iso_clause": "9.1",
        "iso_title": "Monitoring, measurement, analysis and evaluation",
        "annex_iv_sections": [4, 9],
        "coverage": "full",
        "notes": (
            "Section 4 (Validation metrics) and Section 9 (PMM plan) "
            "together satisfy monitoring and evaluation requirements."
        ),
    },
    {
        "iso_clause": "9.3",
        "iso_title": "Management review",
        "annex_iv_sections": [9],
        "coverage": "supplementary",
        "notes": (
            "Section 9 PMM plan can serve as management review input. "
            "A separate management review record is required for full compliance."
        ),
    },
    {
        "iso_clause": "10.1",
        "iso_title": "Continual improvement",
        "annex_iv_sections": [6, 9],
        "coverage": "partial",
        "notes": (
            "Section 6 changelog + Section 9 improvement actions. "
            "Supplement with formal PDCA documentation."
        ),
    },
    {
        "iso_clause": "A.2.2",
        "iso_title": "AI system categorization",
        "annex_iv_sections": [1],
        "coverage": "full",
        "notes": (
            "Section 1 intended purpose + Annex III classification flag directly "
            "satisfies AI system categorisation requirements."
        ),
    },
    {
        "iso_clause": "A.2.6",
        "iso_title": "Data for AI systems",
        "annex_iv_sections": [3],
        "coverage": "full",
        "notes": "Section 3 (Training, Validation & Test Data) / data sheets.",
    },
    {
        "iso_clause": "A.3.3",
        "iso_title": "Transparency and explainability",
        "annex_iv_sections": [1, 8],
        "coverage": "full",
        "notes": (
            "Section 1 (system description) + Section 8 (XAI interfaces, Art. 13 info) "
            "together address transparency obligations."
        ),
    },
    {
        "iso_clause": "A.6.1",
        "iso_title": "Human oversight",
        "annex_iv_sections": [8],
        "coverage": "full",
        "notes": (
            "Section 8 (Human Oversight) directly evidences human-in-the-loop "
            "procedures required by AI Act Art. 14 and ISO 42001 A.6.1."
        ),
    },
    {
        "iso_clause": "A.6.2",
        "iso_title": "Accountability",
        "annex_iv_sections": [1, 6],
        "coverage": "partial",
        "notes": (
            "System ownership in Section 1 + audit trail in Section 6. "
            "Supplement with formal RACI/accountability matrix."
        ),
    },
    {
        "iso_clause": "A.7.1",
        "iso_title": "Addressing AI risks related to fairness",
        "annex_iv_sections": [3, 4, 5],
        "coverage": "full",
        "notes": (
            "Section 3 (dataset demographics), Section 4 (subgroup performance metrics), "
            "Section 5 (bias risk controls) together evidence fairness management."
        ),
    },
    {
        "iso_clause": "A.8.3",
        "iso_title": "Robustness",
        "annex_iv_sections": [4, 5],
        "coverage": "partial",
        "notes": (
            "Section 4 stress-testing results + Section 5 adversarial risk controls. "
            "Add dedicated robustness test report as evidence."
        ),
    },
]

# Quick lookup by ISO clause
_CROSSWALK_INDEX: dict[str, dict[str, Any]] = {
    c["iso_clause"]: c for c in ISO_42001_CROSSWALK
}


def get_crosswalk() -> list[dict[str, Any]]:
    return ISO_42001_CROSSWALK


def get_covered_sections_for_clause(clause: str) -> list[int]:
    entry = _CROSSWALK_INDEX.get(clause)
    return entry["annex_iv_sections"] if entry else []


def get_coverage_for_section(section_number: int) -> list[dict[str, Any]]:
    """Return all ISO clauses that this Annex IV section evidences."""
    return [c for c in ISO_42001_CROSSWALK if section_number in c["annex_iv_sections"]]


def build_evidence_package(
    completed_sections: list[int],
) -> dict[str, Any]:
    """
    Build an ISO 42001 evidence package summary showing which controls are
    covered by the completed Annex IV sections.
    """
    covered: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    not_covered: list[dict[str, Any]] = []

    for entry in ISO_42001_CROSSWALK:
        required = set(entry["annex_iv_sections"])
        completed = set(completed_sections)
        overlap = required & completed

        if not overlap:
            not_covered.append(entry)
        elif overlap == required or entry["coverage"] == "full":
            covered.append(entry)
        else:
            partial.append(entry)

    return {
        "total_controls": len(ISO_42001_CROSSWALK),
        "fully_covered": len(covered),
        "partially_covered": len(partial),
        "not_covered": len(not_covered),
        "covered_clauses": [c["iso_clause"] for c in covered],
        "partial_clauses": [c["iso_clause"] for c in partial],
        "not_covered_clauses": [c["iso_clause"] for c in not_covered],
        "coverage_pct": round(
            (len(covered) + 0.5 * len(partial)) / len(ISO_42001_CROSSWALK) * 100, 1
        ),
    }
