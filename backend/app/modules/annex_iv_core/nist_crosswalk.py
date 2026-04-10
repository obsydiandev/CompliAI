"""Regulatory crosswalk: Annex IV (AI Act) ↔ NIST AI RMF 1.0 + Colorado AI Act (T6.3).

NIST AI RMF 1.0 (January 2023) organises AI risk management into four
core functions: GOVERN, MAP, MEASURE, MANAGE — each subdivided into
categories and subcategories.

Colorado Artificial Intelligence Act (SB 24-205, eff. 1 Feb 2026) applies
to developers and deployers of "high-risk AI systems" affecting Colorado
consumers in consequential decisions.

Each entry maps a framework clause/section to the relevant Annex IV
section(s) and indicates coverage level.
"""

from __future__ import annotations

from typing import Any

# ── NIST AI RMF 1.0 crosswalk ────────────────────────────────────────────────

NIST_CROSSWALK: list[dict[str, Any]] = [
    # ── GOVERN ──────────────────────────────────────────────────────────────
    {
        "framework": "NIST AI RMF 1.0",
        "function": "GOVERN",
        "category": "GOVERN 1.1",
        "title": "AI risk policies and processes are documented",
        "annex_iv_sections": [7],
        "coverage": "full",
        "notes": (
            "Section 7 (Standards, Norms and Compliance) documents the applicable "
            "regulatory and standards framework, directly evidencing governance policies."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "GOVERN",
        "category": "GOVERN 1.2",
        "title": "Accountability and responsibility for AI risk is established",
        "annex_iv_sections": [1, 8],
        "coverage": "partial",
        "notes": (
            "Section 1 identifies the provider/deployer; Section 8 specifies human "
            "oversight roles. Supplement with an explicit RACI matrix."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "GOVERN",
        "category": "GOVERN 2.2",
        "title": "Personnel are trained on AI risk",
        "annex_iv_sections": [8],
        "coverage": "supplementary",
        "notes": (
            "Section 8 (Human Oversight) mentions operator training requirements. "
            "Supplement with training records and completion evidence."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "GOVERN",
        "category": "GOVERN 4.1",
        "title": "Organizational teams are committed to a culture of risk management",
        "annex_iv_sections": [5],
        "coverage": "partial",
        "notes": (
            "Section 5 (Risk Management) demonstrates process; culture evidence "
            "requires supplementary artifacts (meeting notes, sign-off logs)."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "GOVERN",
        "category": "GOVERN 6.1",
        "title": "Policies for third-party entities managing AI risks are documented",
        "annex_iv_sections": [1, 7],
        "coverage": "partial",
        "notes": (
            "Section 1 identifies third-party components; Section 7 lists applicable "
            "standards. Supplement with supply-chain risk management documentation."
        ),
    },
    # ── MAP ─────────────────────────────────────────────────────────────────
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MAP",
        "category": "MAP 1.1",
        "title": "Context — intended use and affected persons are identified",
        "annex_iv_sections": [1],
        "coverage": "full",
        "notes": (
            "Section 1 (General Description and Intended Purpose) directly evidences "
            "intended use, use cases, and categories of affected persons."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MAP",
        "category": "MAP 1.5",
        "title": "Organizational risk tolerance is documented",
        "annex_iv_sections": [5],
        "coverage": "partial",
        "notes": (
            "Section 5 captures risk thresholds and residual risk acceptance. "
            "Supplement with a formal risk appetite statement."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MAP",
        "category": "MAP 2.1",
        "title": "Scientific and technical basis of the AI system is characterised",
        "annex_iv_sections": [2, 3],
        "coverage": "full",
        "notes": (
            "Section 2 (Training & Validation Data) and Section 3 (Architecture, "
            "Algorithms) fully document the technical basis."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MAP",
        "category": "MAP 2.3",
        "title": "AI system impact on individuals and communities is identified",
        "annex_iv_sections": [1, 5],
        "coverage": "full",
        "notes": (
            "Section 1 identifies affected populations; Section 5 contains the "
            "impact risk analysis."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MAP",
        "category": "MAP 3.5",
        "title": "Impacts to critical infrastructure are documented",
        "annex_iv_sections": [5, 7],
        "coverage": "supplementary",
        "notes": (
            "Sections 5 and 7 partially cover infrastructure risk. Critical "
            "infrastructure-specific analysis requires supplementary documentation."
        ),
    },
    # ── MEASURE ─────────────────────────────────────────────────────────────
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MEASURE",
        "category": "MEASURE 1.1",
        "title": "AI risk measurement approaches are identified and prioritised",
        "annex_iv_sections": [4, 5],
        "coverage": "full",
        "notes": (
            "Section 4 (Performance Monitoring) and Section 5 (Risk Management) "
            "together establish measurement approaches and priority risks."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MEASURE",
        "category": "MEASURE 2.2",
        "title": "AI system is evaluated for trustworthiness characteristics",
        "annex_iv_sections": [3, 4, 6],
        "coverage": "full",
        "notes": (
            "Sections 3 (Architecture), 4 (Performance), and 6 (Cybersecurity) "
            "collectively address accuracy, robustness, and security."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MEASURE",
        "category": "MEASURE 2.5",
        "title": "Fairness and bias evaluations are performed",
        "annex_iv_sections": [3, 5],
        "coverage": "full",
        "notes": (
            "Section 3 documents algorithmic design choices for non-discrimination; "
            "Section 5 includes bias in the risk assessment."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MEASURE",
        "category": "MEASURE 2.8",
        "title": "Risks from third-party AI are documented and evaluated",
        "annex_iv_sections": [1, 2],
        "coverage": "partial",
        "notes": (
            "Section 1 identifies third-party components; Section 2 documents "
            "third-party data sources. Supplement with supply-chain risk register."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MEASURE",
        "category": "MEASURE 4.1",
        "title": "Post-deployment AI risk measurement is conducted",
        "annex_iv_sections": [4, 9],
        "coverage": "full",
        "notes": (
            "Section 4 defines ongoing performance monitoring KPIs; Section 9 "
            "(Post-Market Monitoring Plan) specifies the PMM programme."
        ),
    },
    # ── MANAGE ──────────────────────────────────────────────────────────────
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MANAGE",
        "category": "MANAGE 1.1",
        "title": "AI risks are prioritised based on impact and likelihood",
        "annex_iv_sections": [5],
        "coverage": "full",
        "notes": (
            "Section 5 (Risk Management) documents risk severity, likelihood, and "
            "prioritisation — directly evidencing this subcategory."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MANAGE",
        "category": "MANAGE 1.3",
        "title": "Responses to risks include options to shut down or retrain",
        "annex_iv_sections": [5, 8],
        "coverage": "full",
        "notes": (
            "Section 5 documents risk treatment options; Section 8 specifies "
            "human override and shut-down procedures."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MANAGE",
        "category": "MANAGE 2.2",
        "title": "Mechanisms for feedback on AI system performance exist",
        "annex_iv_sections": [4, 8, 9],
        "coverage": "full",
        "notes": (
            "Sections 4, 8, and 9 together describe feedback mechanisms, operator "
            "reporting, and post-market feedback loops."
        ),
    },
    {
        "framework": "NIST AI RMF 1.0",
        "function": "MANAGE",
        "category": "MANAGE 4.1",
        "title": "Post-deployment risks are tracked and residual risks are documented",
        "annex_iv_sections": [5, 9],
        "coverage": "full",
        "notes": (
            "Section 5 tracks residual risks; Section 9 (PMM Plan) documents "
            "post-deployment monitoring and incident handling."
        ),
    },
]

# ── Colorado AI Act (SB 24-205) crosswalk ─────────────────────────────────────

COLORADO_AIA_CROSSWALK: list[dict[str, Any]] = [
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1702",
        "title": "Disclosure — high-risk AI system use to consumers",
        "annex_iv_sections": [1],
        "coverage": "partial",
        "notes": (
            "Section 1 (General Description) documents intended use and deployment "
            "context. Supplement with consumer-facing disclosure statement and "
            "UI notice mechanisms."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1703(1)",
        "title": "Developer — provide deployers with documentation on known risks",
        "annex_iv_sections": [5, 7],
        "coverage": "full",
        "notes": (
            "Section 5 (Risk Management) and Section 7 (Standards) together document "
            "known risks and applicable safeguards for deployers."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1703(2)",
        "title": "Developer — provide documentation of training data sources and characteristics",
        "annex_iv_sections": [2],
        "coverage": "full",
        "notes": (
            "Section 2 (Training, Validation and Testing Data) directly documents "
            "data provenance, characteristics, and limitations."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1704(1)",
        "title": "Deployer — implement risk management programme",
        "annex_iv_sections": [5, 9],
        "coverage": "full",
        "notes": (
            "Section 5 (Risk Management) and Section 9 (Post-Market Monitoring) "
            "collectively constitute the required risk management programme."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1704(2)",
        "title": "Deployer — conduct impact assessment before and after deployment",
        "annex_iv_sections": [5],
        "coverage": "partial",
        "notes": (
            "Section 5 contains the core risk assessment. A formal pre/post-deployment "
            "Impact Assessment report (generated by CompliAI AI Impact Assessment feature) "
            "supplements this section."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1704(3)",
        "title": "Deployer — notify consumers when consequential decisions are made by AI",
        "annex_iv_sections": [1, 8],
        "coverage": "supplementary",
        "notes": (
            "Section 1 defines consequential use cases; Section 8 covers human oversight "
            "and review mechanisms. Consumer notification must be implemented at the "
            "application layer — supplement with UI disclosure evidence."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1704(4)",
        "title": "Deployer — provide opportunity to appeal or correct consequential decision",
        "annex_iv_sections": [8],
        "coverage": "supplementary",
        "notes": (
            "Section 8 (Human Oversight) specifies correction/override mechanisms. "
            "Appeal process must be documented and implemented at the application layer."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1705",
        "title": "Annual risk assessment and report",
        "annex_iv_sections": [5, 9],
        "coverage": "partial",
        "notes": (
            "Section 5 and Section 9 together provide the substance for an annual "
            "risk report. Generate the portfolio report (CSV/PDF) as the annual "
            "submission artifact."
        ),
    },
    {
        "framework": "Colorado AI Act (SB 24-205)",
        "section": "§ 6-1-1706",
        "title": "Non-discrimination — bias testing and mitigation",
        "annex_iv_sections": [3, 5],
        "coverage": "full",
        "notes": (
            "Section 3 documents algorithmic safeguards; Section 5 includes bias in "
            "the risk assessment. Use the Bias Audit feature to generate evidence."
        ),
    },
]


def get_nist_crosswalk(section_filter: list[int] | None = None) -> list[dict[str, Any]]:
    """Return NIST AI RMF crosswalk entries, optionally filtered by Annex IV section."""
    if not section_filter:
        return NIST_CROSSWALK
    return [e for e in NIST_CROSSWALK if any(s in e["annex_iv_sections"] for s in section_filter)]


def get_colorado_crosswalk(section_filter: list[int] | None = None) -> list[dict[str, Any]]:
    """Return Colorado AI Act crosswalk entries, optionally filtered by Annex IV section."""
    if not section_filter:
        return COLORADO_AIA_CROSSWALK
    return [
        e for e in COLORADO_AIA_CROSSWALK if any(s in e["annex_iv_sections"] for s in section_filter)
    ]
