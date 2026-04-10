"""Template library for Annex IV — 8 AI system types (T5.2 / Epic 6).

Each template pre-fills common fields for a system type, reducing
the documentation burden for standard patterns.
"""

from __future__ import annotations

from typing import Any

TEMPLATE_CATALOGUE: list[dict[str, Any]] = [
    {
        "id": "credit_scoring",
        "name": "Credit Scoring Model",
        "description": (
            "Automated credit-risk assessment using ML. "
            "High-risk under AI Act Annex III (Art. 6)."
        ),
        "system_type": "credit_scoring",
        "tags": ["fintech", "high_risk", "annex_iii"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Automated credit-risk assessment to support lending decisions for "
                    "retail and SME customers. The system assists human underwriters by "
                    "generating a credit score and risk tier."
                ),
                "use_cases": [
                    "Personal loan application scoring",
                    "Credit card limit assessment",
                    "SME loan pre-qualification",
                ],
                "intended_users": (
                    "Loan officers, underwriters, and credit risk analysts at financial "
                    "institutions. Final credit decisions are made or reviewed by a "
                    "qualified human."
                ),
            },
            2: {
                "architecture_description": (
                    "Gradient boosting model (XGBoost/LightGBM) trained on applicant "
                    "financial history, bureau data, and behavioural signals. "
                    "Feature engineering pipeline includes missing-value imputation, "
                    "target encoding, and monotone constraints for regulatory alignment."
                ),
                "algorithms_used": "Gradient Boosted Trees (XGBoost / LightGBM)",
            },
            5: {
                "risk_categories": [
                    "Discrimination against protected groups (gender, ethnicity)",
                    "Opaque scoring leading to inability to challenge decisions (Art. 13)",
                    "Model drift due to economic regime change",
                    "Data quality degradation in bureau feeds",
                ],
                "risk_mitigation_measures": (
                    "Fairness constraints in training, regular bias audits (demographic "
                    "parity ≤ 0.1), model monitoring with drift detection, SHAP-based "
                    "explanations for adverse action notices."
                ),
            },
            8: {
                "human_oversight_measures": (
                    "All credit decisions above €50,000 require human reviewer sign-off. "
                    "Adverse decisions trigger mandatory explanation to applicant (GDPR "
                    "Art. 22 + AI Act Art. 13). Loan officers can override system "
                    "recommendations with documented justification."
                ),
            },
        },
    },
    {
        "id": "cv_ranking",
        "name": "CV / Recruitment Ranking System",
        "description": (
            "AI-powered CV screening and candidate ranking. "
            "High-risk under AI Act Annex III."
        ),
        "system_type": "cv_ranking",
        "tags": ["hr_tech", "high_risk", "annex_iii"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Automated screening and ranking of job applications to reduce "
                    "recruiter workload and surface qualified candidates. The system "
                    "does not make final hiring decisions."
                ),
                "use_cases": [
                    "Initial CV screening for volume roles",
                    "Skills-match scoring against job descriptions",
                    "Shortlist generation for recruiter review",
                ],
                "intended_users": "HR recruiters, talent acquisition specialists.",
            },
            5: {
                "risk_categories": [
                    "Bias against protected characteristics (gender, age, ethnicity)",
                    "Perpetuation of historical hiring biases in training data",
                    "Lack of transparency in ranking criteria",
                ],
                "risk_mitigation_measures": (
                    "Regular bias audits with equal opportunity difference ≤ 0.1. "
                    "Training data audited for demographic balance. "
                    "Explainability layer providing top-5 ranking factors per candidate. "
                    "Human recruiter reviews all shortlists."
                ),
            },
            8: {
                "human_oversight_measures": (
                    "Recruiters review all system-generated shortlists. "
                    "Candidates ranked outside top-20 can trigger human review on request. "
                    "Final hiring decisions are always made by humans."
                ),
            },
        },
    },
    {
        "id": "medical_diagnostic",
        "name": "Medical Diagnostic Aid",
        "description": (
            "AI system assisting clinical diagnosis. High-risk under AI Act Annex III "
            "(medical devices)."
        ),
        "system_type": "medical_diagnostic",
        "tags": ["medtech", "high_risk", "annex_iii", "mdr"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Clinical decision support for diagnostic imaging analysis. "
                    "The system identifies potential anomalies and generates probability "
                    "scores to assist radiologists. It is not a standalone diagnostic "
                    "device and requires clinician validation."
                ),
                "intended_users": "Radiologists, referring physicians.",
            },
            5: {
                "risk_categories": [
                    "False negatives (missed diagnosis)",
                    "Over-reliance by clinicians (automation bias)",
                    "Performance degradation across demographic subgroups",
                    "Distribution shift from different imaging equipment",
                ],
                "risk_mitigation_measures": (
                    "Validated on diverse demographic and equipment cohorts. "
                    "Uncertainty quantification (calibrated confidence scores). "
                    "Mandatory clinician sign-off for all findings. "
                    "Continuous post-market monitoring with outcome tracking."
                ),
            },
            8: {
                "human_oversight_measures": (
                    "All AI findings require clinician review and sign-off before "
                    "clinical action. System provides confidence intervals. "
                    "Escalation pathway for low-confidence predictions."
                ),
            },
        },
    },
    {
        "id": "generative_content",
        "name": "Generative AI / LLM Application",
        "description": "General-purpose LLM-based application. Limited or minimal risk.",
        "system_type": "generative_content",
        "tags": ["genai", "llm", "limited_risk"],
        "sections": {
            1: {
                "intended_purpose": (
                    "AI-powered content generation assistant for enterprise users. "
                    "Generates text, summaries, and structured documents based on user "
                    "prompts and provided context."
                ),
                "use_cases": [
                    "Internal document drafting",
                    "Email and communication assistance",
                    "Knowledge base Q&A",
                ],
            },
            5: {
                "risk_categories": [
                    "Hallucination and factual inaccuracy",
                    "Prompt injection attacks",
                    "Generation of harmful or biased content",
                    "Data leakage from context window",
                ],
                "risk_mitigation_measures": (
                    "Output grounding with RAG (retrieval-augmented generation). "
                    "Content safety classifiers. System prompt hardening. "
                    "User awareness: AI-generated content is labelled as such (Art. 52)."
                ),
            },
            8: {
                "human_oversight_measures": (
                    "Users are informed they are interacting with AI (transparency, Art. 52). "
                    "Generated content is watermarked/labelled. "
                    "Feedback loop for reporting inappropriate outputs."
                ),
            },
        },
    },
    {
        "id": "fraud_detection",
        "name": "Fraud Detection System",
        "description": "Real-time transaction fraud detection. High-risk.",
        "system_type": "fraud_detection",
        "tags": ["fintech", "high_risk", "real_time"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Real-time detection of fraudulent payment transactions. "
                    "Generates risk scores to trigger holds, step-up authentication, "
                    "or human review queues."
                ),
                "use_cases": [
                    "Card payment fraud scoring",
                    "Account takeover detection",
                    "Suspicious activity reporting (SAR) support",
                ],
            },
            4: {
                "validation_metrics": {
                    "precision": 0.95,
                    "recall": 0.88,
                    "f1": 0.91,
                    "false_positive_rate": 0.02,
                },
                "performance_thresholds": {
                    "precision": 0.90,
                    "recall": 0.85,
                    "false_positive_rate": 0.05,
                },
            },
        },
    },
    {
        "id": "predictive_maintenance",
        "name": "Predictive Maintenance System",
        "description": "Industrial IoT predictive maintenance. Minimal risk.",
        "system_type": "predictive_maintenance",
        "tags": ["industrial", "iot", "minimal_risk"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Predictive maintenance for industrial equipment by analysing "
                    "sensor telemetry to forecast failure events and optimise "
                    "maintenance schedules."
                ),
                "use_cases": [
                    "Remaining useful life estimation",
                    "Anomaly detection in sensor streams",
                    "Maintenance schedule optimisation",
                ],
            },
        },
    },
    {
        "id": "nlp_text_classification",
        "name": "NLP Text Classification",
        "description": "Natural language processing for text categorisation tasks.",
        "system_type": "nlp_text_classification",
        "tags": ["nlp", "classification"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Automated text classification for routing, tagging, or moderation "
                    "of user-generated content or internal documents."
                ),
            },
            2: {
                "architecture_description": (
                    "Fine-tuned transformer model (BERT/RoBERTa family) for multi-class "
                    "text classification. Pre-trained on general corpus, fine-tuned on "
                    "domain-specific labelled dataset."
                ),
                "algorithms_used": "Transformer (BERT / RoBERTa fine-tuned)",
            },
        },
    },
    {
        "id": "recommendation_system",
        "name": "Recommendation System",
        "description": "Personalised content or product recommendations. Limited risk.",
        "system_type": "recommendation_system",
        "tags": ["recommender", "personalisation", "limited_risk"],
        "sections": {
            1: {
                "intended_purpose": (
                    "Personalised recommendation engine surfacing relevant products, "
                    "content, or services based on user behaviour and preferences."
                ),
                "use_cases": [
                    "Product recommendations (e-commerce)",
                    "Content personalisation (media)",
                    "Similar-item discovery",
                ],
            },
            5: {
                "risk_categories": [
                    "Filter bubble / echo chamber effects",
                    "Amplification of popularity bias",
                    "Recommending harmful or inappropriate content",
                ],
                "risk_mitigation_measures": (
                    "Diversity injection in recommendation lists (min 20% non-personalised). "
                    "Content safety filtering. Regular diversity audits."
                ),
            },
        },
    },
]

# Index by id for fast lookup
_TEMPLATE_INDEX: dict[str, dict[str, Any]] = {t["id"]: t for t in TEMPLATE_CATALOGUE}


def list_templates() -> list[dict[str, Any]]:
    """Return the catalogue without full section content (for listing)."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "system_type": t["system_type"],
            "tags": t["tags"],
            "sections_count": len(t["sections"]),
        }
        for t in TEMPLATE_CATALOGUE
    ]


def get_template(template_id: str) -> dict[str, Any] | None:
    return _TEMPLATE_INDEX.get(template_id)


def apply_template_to_content(
    template_id: str,
    existing_sections: dict[int, dict],
    overwrite: bool = False,
) -> dict[int, dict]:
    """
    Merge template section content into existing section content.

    Parameters
    ----------
    template_id:
        Template identifier from TEMPLATE_CATALOGUE.
    existing_sections:
        Dict of section_number → current content dict.
    overwrite:
        If True, template fields overwrite existing values.
        If False (default), template fields only fill empty/missing values.

    Returns
    -------
    Updated sections dict (new dict, originals not mutated).
    """
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Unknown template: {template_id}")

    result: dict[int, dict] = {k: dict(v) for k, v in existing_sections.items()}

    for section_num, tpl_content in template["sections"].items():
        existing = result.get(section_num, {})
        merged: dict[str, Any] = dict(existing)

        for field, value in tpl_content.items():
            if overwrite or not merged.get(field):
                merged[field] = value

        result[section_num] = merged

    return result
