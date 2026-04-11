"""Annex IV intended purpose validator with deterministic keyword detection
and optional LLM-assisted over-scoping analysis (T_p10).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

HIGH_RISK_TRIGGERS: dict[str, list[str]] = {
    "biometric": [
        "biometric",
        "facial recognition",
        "fingerprint",
        "voice recognition",
        "iris scan",
        "emotion recognition",
    ],
    "critical_infrastructure": [
        "critical infrastructure",
        "energy grid",
        "water supply",
        "traffic management",
        "power plant",
    ],
    "education": [
        "educational assessment",
        "student evaluation",
        "admission",
        "exam scoring",
        "learning assessment",
    ],
    "employment": [
        "recruitment",
        "cv screening",
        "job application",
        "employment decision",
        "worker monitoring",
        "performance evaluation",
    ],
    "essential_services": [
        "credit scoring",
        "creditworthiness",
        "insurance",
        "benefit eligibility",
        "social assistance",
    ],
    "law_enforcement": [
        "law enforcement",
        "criminal",
        "border control",
        "crime prediction",
        "risk assessment for crime",
    ],
    "justice": [
        "judicial",
        "democratic process",
        "court decision",
        "legal",
    ],
    "medical": [
        "medical device",
        "clinical decision",
        "diagnostic",
        "patient triage",
        "health risk",
    ],
}

WARNING_MESSAGES: dict[str, str] = {
    "biometric": (
        "System may involve biometric identification — falls under Annex III §1. "
        "Real-time remote biometric identification in public spaces requires special authorisation."
    ),
    "critical_infrastructure": (
        "System may be used in critical infrastructure management — falls under Annex III §2. "
        "Requires rigorous safety and resilience assessment."
    ),
    "education": (
        "System may be used in education or vocational training — falls under Annex III §3. "
        "AI-driven assessment of students is subject to strict transparency requirements."
    ),
    "employment": (
        "System may affect employment or worker management — falls under Annex III §4. "
        "Automated HR decisions require human oversight and explainability."
    ),
    "essential_services": (
        "System may be used in access to essential private or public services — falls under Annex III §5. "
        "Credit scoring and benefit eligibility decisions require transparency."
    ),
    "law_enforcement": (
        "System may be used in law enforcement — falls under Annex III §6. "
        "Predictive policing and criminal risk assessment are highly regulated."
    ),
    "justice": (
        "System may be used in justice, democratic processes, or legal proceedings — falls under Annex III §8. "
        "Court-supporting AI systems face strict requirements."
    ),
    "medical": (
        "System may be a medical device or used in healthcare — falls under Annex III §5b or MDR. "
        "Requires clinical validation and may need notified body involvement."
    ),
}


def validate_intended_purpose(text: str) -> dict:
    """
    Returns {"is_high_risk": bool, "triggers": list[str], "warnings": list[str]}.
    """
    text_lower = text.lower()
    triggered_categories: list[str] = []
    warnings: list[str] = []

    for category, keywords in HIGH_RISK_TRIGGERS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                if category not in triggered_categories:
                    triggered_categories.append(category)
                    warnings.append(WARNING_MESSAGES[category])
                break

    return {
        "is_high_risk": len(triggered_categories) > 0,
        "triggers": triggered_categories,
        "warnings": warnings,
    }


def check_intended_purpose_overscoping(
    intended_purpose_text: str,
    declared_risk_category: str,
) -> dict:
    """LLM-assisted over-scoping analysis (T_p10).

    Analyses the 'intended purpose' field to detect if the text inadvertently
    describes a use case broader than the declared risk category — which would
    pull the system into a more restrictive Annex III classification.

    Args:
        intended_purpose_text: the free-text intended purpose from the technical file
        declared_risk_category: "high_risk" | "limited_risk" | "minimal_risk"

    Returns dict with:
        overscoping_detected (bool)
        suggested_risk_level (str)
        explanation (str)
        recommendations (list[str])
    """
    # First run deterministic check
    det_result = validate_intended_purpose(intended_purpose_text)

    # If deterministic check finds high risk but system declared lower, flag it
    if det_result["is_high_risk"] and declared_risk_category != "high_risk":
        return {
            "overscoping_detected": True,
            "suggested_risk_level": "high_risk",
            "explanation": (
                "The intended purpose description contains terms associated with Annex III "
                "high-risk categories, but the system is declared as non-high-risk. "
                "This discrepancy should be resolved before submitting the Technical File."
            ),
            "triggered_categories": det_result["triggers"],
            "recommendations": det_result["warnings"],
            "source": "deterministic",
        }

    # LLM analysis for deeper context
    try:
        from app.config import settings

        if not settings.OPENAI_API_KEY:
            return {
                "overscoping_detected": False,
                "suggested_risk_level": declared_risk_category,
                "explanation": "LLM analysis skipped — OPENAI_API_KEY not configured.",
                "recommendations": [],
                "source": "skipped",
            }

        import json

        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = f"""Analyse this AI system intended purpose for EU AI Act Annex III over-scoping risk.

Intended purpose: "{intended_purpose_text}"
Declared risk level: {declared_risk_category}

Determine if the intended purpose text is broader than the declared risk level suggests,
or if it inadvertently describes an Annex III high-risk use case.

Respond with JSON:
{{
  "overscoping_detected": true/false,
  "suggested_risk_level": "high_risk" | "limited_risk" | "minimal_risk",
  "explanation": "2-3 sentence analysis",
  "recommendations": ["action 1", "action 2"]
}}"""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an EU AI Act compliance expert specialising in risk classification.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content or "{}")
        data["source"] = "llm"
        return data

    except Exception as exc:
        logger.warning("LLM over-scoping check failed: %s", exc)
        return {
            "overscoping_detected": False,
            "suggested_risk_level": declared_risk_category,
            "explanation": f"LLM analysis failed: {exc}",
            "recommendations": [],
            "source": "error",
        }
