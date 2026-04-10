"""AI Impact Assessment generator (T5.4 / Epic 6).

Generates a structured AI Impact Assessment (AI IA / DPIA-style)
from TechnicalFile section data, optionally using LLM to enrich
the narrative.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def build_ai_ia_report(
    system_name: str,
    system_description: str,
    category: str,
    annex_iii_flag: bool,
    sections: dict[int, dict],
    use_llm: bool = True,
) -> dict[str, Any]:
    """
    Build an AI Impact Assessment from Annex IV section data.

    Parameters
    ----------
    system_name, system_description, category, annex_iii_flag:
        Basic system metadata.
    sections:
        Dict section_number → content dict.
    use_llm:
        If True and OPENAI_API_KEY is configured, use LLM to generate
        a narrative summary for each IA section.

    Returns
    -------
    dict — structured AI IA report suitable for PDF export.
    """
    sec1 = sections.get(1, {})
    sec2 = sections.get(2, {})
    sec3 = sections.get(3, {})
    sec4 = sections.get(4, {})
    sec5 = sections.get(5, {})
    sec8 = sections.get(8, {})
    sec9 = sections.get(9, {})

    report: dict[str, Any] = {
        "title": f"AI Impact Assessment — {system_name}",
        "system_name": system_name,
        "system_description": system_description,
        "risk_category": category,
        "annex_iii_applicable": annex_iii_flag,
        "sections": {
            "1_purpose_and_scope": {
                "title": "1. Purpose and Scope",
                "intended_purpose": sec1.get("intended_purpose", ""),
                "use_cases": sec1.get("use_cases", []),
                "intended_users": sec1.get("intended_users", ""),
                "geographic_scope": sec1.get("geographic_scope", ""),
                "operational_context": sec1.get("operational_context", ""),
            },
            "2_ai_system_description": {
                "title": "2. AI System Description",
                "architecture": sec2.get("architecture_description", ""),
                "algorithms": sec2.get("algorithms_used", ""),
                "training_approach": sec3.get("training_data_description", ""),
                "data_sources": sec3.get("data_sources", []),
            },
            "3_affected_persons_and_rights": {
                "title": "3. Affected Persons and Rights at Risk",
                "user_groups": sec1.get("intended_users", ""),
                "vulnerable_groups": sec5.get("vulnerable_groups", ""),
                "rights_at_risk": _derive_rights_at_risk(category, sec5),
            },
            "4_necessity_and_proportionality": {
                "title": "4. Necessity and Proportionality",
                "justification": sec1.get("intended_purpose", ""),
                "alternatives_considered": sec2.get("design_alternatives", ""),
                "proportionality_statement": (
                    f"The system is classified as {category}. "
                    + ("As an Annex III high-risk system, " if annex_iii_flag else "")
                    + "the level of automation is proportionate to the stated purpose "
                    "and subject to human oversight measures documented in Section 8."
                ),
            },
            "5_risks_and_mitigation": {
                "title": "5. Identified Risks and Mitigation Measures",
                "risk_categories": sec5.get("risk_categories", []),
                "mitigation_measures": sec5.get("risk_mitigation_measures", ""),
                "residual_risk": sec5.get("residual_risk_assessment", ""),
                "validation_results": sec4.get("validation_methodology", ""),
                "performance_thresholds": sec4.get("performance_thresholds", {}),
            },
            "6_human_oversight": {
                "title": "6. Human Oversight and Accountability",
                "oversight_measures": sec8.get("human_oversight_measures", ""),
                "explainability": sec8.get("explainability_approach", ""),
                "escalation_procedures": sec8.get("escalation_procedures", ""),
                "accountability_owner": "",
            },
            "7_post_market_monitoring": {
                "title": "7. Post-Market Monitoring and Review",
                "monitoring_plan": sec9.get("pmm_plan", ""),
                "monitoring_metrics": sec9.get("monitoring_metrics", []),
                "review_frequency": sec9.get("review_frequency", ""),
                "incident_reporting": sec9.get("incident_reporting_procedure", ""),
            },
            "8_conclusion": {
                "title": "8. Conclusion",
                "overall_assessment": "",
                "residual_risks_acceptable": None,
                "sign_off_required": annex_iii_flag,
            },
        },
    }

    # Optionally enrich with LLM narrative
    if use_llm and settings.OPENAI_API_KEY:
        try:
            _enrich_with_llm(report)
        except Exception as exc:
            logger.warning("LLM enrichment failed: %s", exc)

    return report


def _derive_rights_at_risk(category: str, sec5: dict) -> list[str]:
    """Derive fundamental rights at risk based on system category."""
    base_rights: list[str] = []
    if category == "high_risk":
        base_rights = [
            "Right to non-discrimination (Art. 21 EU Charter)",
            "Right to an effective remedy (Art. 47 EU Charter)",
            "Right to human review of automated decisions (GDPR Art. 22)",
        ]
    if sec5.get("risk_categories"):
        risk_cats = sec5["risk_categories"]
        risk_str = str(risk_cats).lower()
        if "bias" in risk_str or "discriminat" in risk_str or "fairness" in risk_str:
            if "Right to non-discrimination (Art. 21 EU Charter)" not in base_rights:
                base_rights.append("Right to non-discrimination (Art. 21 EU Charter)")
        if "health" in risk_str or "safety" in risk_str:
            base_rights.append("Right to life and physical integrity (Art. 2-3 EU Charter)")
        if "data" in risk_str or "privac" in risk_str:
            base_rights.append("Right to data protection (Art. 8 EU Charter / GDPR)")
    return base_rights or ["No specific fundamental rights at elevated risk identified."]


def _enrich_with_llm(report: dict) -> None:
    """Generate a concise overall assessment narrative using LLM."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    context = json.dumps(
        {
            "system": report["system_name"],
            "category": report["risk_category"],
            "purpose": report["sections"]["1_purpose_and_scope"]["intended_purpose"],
            "risks": report["sections"]["5_risks_and_mitigation"]["risk_categories"],
            "mitigation": report["sections"]["5_risks_and_mitigation"][
                "mitigation_measures"
            ],
        },
        indent=2,
    )

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an EU AI Act compliance expert writing AI Impact Assessments. "
                    "Write concisely in English. Max 200 words."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write a concise overall assessment conclusion for this AI system:\n"
                    f"{context}\n\n"
                    "Assess whether identified risks are acceptable given the mitigation "
                    "measures, and whether the system is ready for deployment under the "
                    "EU AI Act."
                ),
            },
        ],
        max_tokens=300,
        temperature=0.3,
    )
    conclusion = response.choices[0].message.content or ""
    report["sections"]["8_conclusion"]["overall_assessment"] = conclusion.strip()
    report["sections"]["8_conclusion"]["residual_risks_acceptable"] = (
        "unacceptable" not in conclusion.lower() and "not acceptable" not in conclusion.lower()
    )
