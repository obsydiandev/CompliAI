"""Annex III AI Act risk classifier.

Implements a deterministic decision tree based on EU AI Act Annex III (high-risk
AI systems) plus the general-purpose / limited-risk / minimal-risk classification.

The classifier works with 10 structured yes/no/text answers collected from a public
questionnaire.  Where Annex III rules give an unambiguous result the tree is used
directly.  For genuinely edge-case inputs, ``llm_fallback.py`` provides an LLM-
assisted classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Question definitions — displayed in the frontend questionnaire
# ---------------------------------------------------------------------------

CLASSIFIER_QUESTIONS: list[dict] = [
    {
        "id": "q1",
        "text": "What is the primary function of your AI system?",
        "type": "select",
        "options": [
            "Automated decision-making that affects individuals",
            "Content generation or creative assistance",
            "Recommendation / ranking",
            "Predictive analytics",
            "Process automation (no individual decisions)",
            "Research / internal analysis",
            "Other",
        ],
        "article_ref": "Art. 3(1) AI Act",
    },
    {
        "id": "q2",
        "text": "In which sector / domain is the AI system deployed?",
        "type": "select",
        "options": [
            "Healthcare / medical devices",
            "Employment / HR / recruitment",
            "Education / vocational training",
            "Critical infrastructure (energy, water, transport, finance)",
            "Law enforcement / border control / justice",
            "Biometric identification or categorisation",
            "Access to essential private or public services (credit, insurance, social benefits)",
            "Safety component of a product (machinery, vehicles, lifts, toys…)",
            "Other / none of the above",
        ],
        "article_ref": "Annex III AI Act",
    },
    {
        "id": "q3",
        "text": "Does the system make or substantially influence final decisions about individual people "
        "(e.g. hiring, loan approval, medical diagnosis, school admission)?",
        "type": "boolean",
        "article_ref": "Art. 6(2) + Annex III",
    },
    {
        "id": "q4",
        "text": "Does the system perform real-time or post-time remote biometric identification of "
        "natural persons in publicly accessible spaces?",
        "type": "boolean",
        "article_ref": "Art. 3(36), Art. 5(1)(a)",
    },
    {
        "id": "q5",
        "text": "Does the system infer emotions, personal characteristics, or social scores from "
        "biometric data?",
        "type": "boolean",
        "article_ref": "Art. 3(35), Annex III §1",
    },
    {
        "id": "q6",
        "text": "Is the AI system a safety component of a product already regulated under EU product "
        "safety legislation (e.g. MDR, Machinery Directive, type-approval for vehicles)?",
        "type": "boolean",
        "article_ref": "Art. 6(1)",
    },
    {
        "id": "q7",
        "text": "Does the system interact directly with humans and could be mistaken for a human "
        "(chatbot / voice assistant without mandatory disclosure)?",
        "type": "boolean",
        "article_ref": "Art. 52 — transparency obligations",
    },
    {
        "id": "q8",
        "text": "Does your organisation have more than 10 employees and/or annual revenue above "
        "€2 million?",
        "type": "boolean",
        "article_ref": "Art. 11(3) — SME exemptions",
    },
    {
        "id": "q9",
        "text": "In which geographic region(s) is the system placed on the market or put into service?",
        "type": "select",
        "options": [
            "European Union / EEA",
            "United Kingdom",
            "United States / Canada",
            "Other non-EU",
            "EU + other regions",
        ],
        "article_ref": "Art. 2 — territorial scope",
    },
    {
        "id": "q10",
        "text": "Briefly describe what the AI system does and who the end-users are "
        "(free text — used for AI-assisted review of edge cases).",
        "type": "text",
        "article_ref": "Art. 3(1) + Annex III",
    },
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ClassificationResult:
    risk_level: str  # "high_risk" | "limited_risk" | "minimal_risk"
    justification: str
    article_citations: list[str] = field(default_factory=list)
    annex_iii_category: str | None = None  # e.g. "biometric_id", "employment", …
    is_edge_case: bool = False  # True when LLM fallback is needed


# ---------------------------------------------------------------------------
# High-risk sector mapping (Annex III)
# ---------------------------------------------------------------------------

_HIGH_RISK_SECTORS = {
    "Healthcare / medical devices",
    "Employment / HR / recruitment",
    "Education / vocational training",
    "Critical infrastructure (energy, water, transport, finance)",
    "Law enforcement / border control / justice",
    "Biometric identification or categorisation",
    "Access to essential private or public services (credit, insurance, social benefits)",
    "Safety component of a product (machinery, vehicles, lifts, toys…)",
}

_SECTOR_TO_ANNEX_CATEGORY: dict[str, str] = {
    "Healthcare / medical devices": "healthcare_medical",
    "Employment / HR / recruitment": "employment_hr",
    "Education / vocational training": "education",
    "Critical infrastructure (energy, water, transport, finance)": "critical_infrastructure",
    "Law enforcement / border control / justice": "law_enforcement",
    "Biometric identification or categorisation": "biometric_categorisation",
    "Access to essential private or public services (credit, insurance, social benefits)": "essential_services",
    "Safety component of a product (machinery, vehicles, lifts, toys…)": "product_safety",
}

_SECTOR_ARTICLE_REFS: dict[str, str] = {
    "Healthcare / medical devices": "Annex III §5 — AI in medical devices",
    "Employment / HR / recruitment": "Annex III §4 — Employment, worker management",
    "Education / vocational training": "Annex III §3 — Education and vocational training",
    "Critical infrastructure (energy, water, transport, finance)": "Annex III §2 — Critical infrastructure",
    "Law enforcement / border control / justice": "Annex III §6–7 — Law enforcement / border",
    "Biometric identification or categorisation": "Annex III §1 — Biometric systems",
    "Access to essential private or public services (credit, insurance, social benefits)": "Annex III §5 — Essential services",
    "Safety component of a product (machinery, vehicles, lifts, toys…)": "Art. 6(1) — Safety component",
}


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


def classify(answers: dict[str, str | bool]) -> ClassificationResult:
    """Run the deterministic Annex III decision tree.

    ``answers`` maps question IDs (q1–q10) to user responses.
    Returns a ClassificationResult.  Sets ``is_edge_case=True`` when the
    free-text answer (q10) should be forwarded to the LLM fallback.
    """

    q2 = str(answers.get("q2", ""))
    q3 = _to_bool(answers.get("q3", False))
    q4 = _to_bool(answers.get("q4", False))
    q5 = _to_bool(answers.get("q5", False))
    q6 = _to_bool(answers.get("q6", False))
    q7 = _to_bool(answers.get("q7", False))
    q9 = str(answers.get("q9", ""))

    # ── Not in EU scope ────────────────────────────────────────────────────
    eu_in_scope = "European Union" in q9 or "EU" in q9
    if not eu_in_scope and q9 and "Other non-EU" in q9:
        return ClassificationResult(
            risk_level="minimal_risk",
            justification=(
                "Your system is deployed exclusively outside the EU/EEA. "
                "The AI Act applies to systems placed on the EU market or affecting EU persons. "
                "Monitor regulatory developments in your jurisdiction."
            ),
            article_citations=["Art. 2(1) AI Act — territorial scope"],
        )

    # ── Real-time remote biometric identification ──────────────────────────
    if q4:
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                "Your system performs real-time remote biometric identification of natural "
                "persons in publicly accessible spaces. This is a prohibited practice under "
                "Art. 5(1)(a) unless a law-enforcement derogation applies, or constitutes "
                "a high-risk system under Annex III §1."
            ),
            article_citations=[
                "Art. 5(1)(a) — Prohibited AI practices",
                "Annex III §1 — Biometric identification and categorisation",
                "Art. 10 — Data governance",
            ],
            annex_iii_category="biometric_realtime",
        )

    # ── Emotion recognition / biometric categorisation ────────────────────
    if q5:
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                "Your system infers emotions or personal characteristics from biometric data. "
                "This falls under Annex III §1 (biometric categorisation) and triggers the full "
                "Annex IV documentation obligation."
            ),
            article_citations=[
                "Annex III §1(b) — Biometric categorisation",
                "Art. 3(35) — Definition of biometric categorisation system",
                "Art. 13 — Transparency and provision of information",
            ],
            annex_iii_category="biometric_categorisation",
        )

    # ── Safety component of a regulated product ───────────────────────────
    if q6:
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                "Your AI system is a safety component of a product already subject to EU "
                "product safety legislation. Art. 6(1) designates it as high-risk, requiring "
                "a conformity assessment and Annex IV Technical File."
            ),
            article_citations=[
                "Art. 6(1) — High-risk AI systems (safety components)",
                "Annex II — Union harmonisation legislation",
                "Art. 11 — Technical documentation",
            ],
            annex_iii_category="product_safety",
        )

    # ── High-risk sector + individual decision-making ─────────────────────
    if q2 in _HIGH_RISK_SECTORS and q3:
        annex_cat = _SECTOR_TO_ANNEX_CATEGORY.get(q2, "other_high_risk")
        article_ref = _SECTOR_ARTICLE_REFS.get(q2, "Annex III")
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                f"Your system operates in a high-risk sector ({q2}) and makes or "
                "substantially influences decisions about individuals. This places it in "
                f"the Annex III high-risk category. {article_ref} requires an Annex IV "
                "Technical File and conformity assessment before deployment."
            ),
            article_citations=[
                article_ref,
                "Art. 6(2) — High-risk AI systems listed in Annex III",
                "Art. 11 — Technical documentation (Annex IV)",
                "Art. 43 — Conformity assessment",
            ],
            annex_iii_category=annex_cat,
        )

    # ── High-risk sector without direct individual decisions ──────────────
    if q2 in _HIGH_RISK_SECTORS and not q3:
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                f"Your system operates in '{q2}', which is a high-risk sector under Annex III. "
                "Even without a direct individual-decision function, systems in this sector are "
                "considered high-risk when they materially influence outcomes in the sector. "
                "We recommend treating this as high-risk and preparing Annex IV documentation."
            ),
            article_citations=[
                _SECTOR_ARTICLE_REFS.get(q2, "Annex III"),
                "Art. 6(2) AI Act",
                "Recital 47 — Interpretation of high-risk classification",
            ],
            annex_iii_category=_SECTOR_TO_ANNEX_CATEGORY.get(q2),
            is_edge_case=True,
        )

    # ── Limited risk: transparency obligations ─────────────────────────────
    if q7:
        return ClassificationResult(
            risk_level="limited_risk",
            justification=(
                "Your system interacts directly with natural persons and could be perceived "
                "as human. Art. 52 requires clear disclosure that the user is interacting with "
                "an AI system. No Annex IV Technical File is required, but a transparency notice "
                "must be shown."
            ),
            article_citations=[
                "Art. 52(1) — Transparency obligations for certain AI systems",
                "Art. 52(2) — Emotion recognition / biometric categorisation disclosure",
            ],
        )

    # ── Minimal risk (default) ─────────────────────────────────────────────
    return ClassificationResult(
        risk_level="minimal_risk",
        justification=(
            "Based on your answers, your AI system does not fall into a high-risk Annex III "
            "category and does not trigger Art. 5 prohibitions or Art. 52 transparency "
            "obligations. It is classified as minimal-risk under the AI Act. "
            "No mandatory Annex IV documentation is required; voluntary codes of conduct apply."
        ),
        article_citations=[
            "Art. 95 — Codes of conduct for non-high-risk AI",
            "Recital 12 — Proportionate obligations",
        ],
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)
