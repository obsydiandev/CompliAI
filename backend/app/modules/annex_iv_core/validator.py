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
