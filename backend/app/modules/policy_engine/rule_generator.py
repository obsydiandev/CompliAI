"""LLM-based policy rule generator (T4.4).

Converts a natural-language policy description into a structured
``PolicyRule`` condition dict that the rule evaluator can execute.

Supported rule types produced:
  days_without_revision  — "Plik techniczny nie może być starszy niż N dni"
  missing_pmm_plan       — "Każdy system musi mieć plan PMM"
  missing_evidence       — "Sekcja X wymaga co najmniej N dowodów"
  unlinked_deployments   — "Każde wdrożenie musi być powiązane z rewizją TF"
  section_overdue        — "Sekcja X musi być zaktualizowana w ciągu N dni"
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a compliance rule compiler for CompliAI, an EU AI Act compliance SaaS.
Your task: convert a natural-language compliance policy description into a structured
JSON condition object that can be evaluated by the CompliAI rule engine.

Supported condition types and their JSON schemas:

1. days_without_revision
   {"type": "days_without_revision", "threshold": <int days>}
   Use when the policy says the Technical File must be updated within N days.

2. missing_pmm_plan
   {"type": "missing_pmm_plan"}
   Use when the policy requires a Post-Market Monitoring plan in Section 9.

3. missing_evidence
   {"type": "missing_evidence", "section": <1-9>, "threshold": <int min items>}
   Use when the policy requires a minimum number of evidence items in a section.

4. unlinked_deployments
   {"type": "unlinked_deployments", "threshold": 30}
   Use when the policy requires every production deployment to be linked to a TF revision.

5. section_overdue
   {"type": "section_overdue", "section": <1-9>, "threshold": <int days>}
   Use when the policy says a specific section must be updated within N days.

Section numbers:
  1 = General Description, 2 = Architecture, 3 = Training Data,
  4 = Validation & Testing, 5 = Risk Management, 6 = Conformity Assessment,
  7 = Human Oversight, 8 = Accuracy & Robustness, 9 = Post-Market Monitoring.

Respond with ONLY a valid JSON object matching one of the schemas above.
Do not include any explanation or markdown fences.
"""


def generate_rule_from_text(
    natural_language: str,
    *,
    model: str = "gpt-4o",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Convert a natural-language policy description to a condition dict.

    Parameters
    ----------
    natural_language:
        Free-form description of the compliance rule, e.g.
        "Plik techniczny musi być zaktualizowany co najmniej raz na 14 dni."
    model:
        OpenAI model to use.
    api_key:
        Override the default API key (uses settings.OPENAI_API_KEY by default).

    Returns
    -------
    dict — a condition dict, e.g. {"type": "days_without_revision", "threshold": 14}

    Raises
    ------
    ValueError
        If the LLM response cannot be parsed as a valid condition.
    RuntimeError
        If the OpenAI API call fails.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required for rule generation") from exc

    from app.config import settings

    key = api_key or settings.OPENAI_API_KEY
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": natural_language.strip()},
            ],
            temperature=0,
            max_tokens=256,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    raw = (response.choices[0].message.content or "").strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()

    try:
        condition = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {raw!r}") from exc

    _validate_condition(condition)
    return condition


def _validate_condition(condition: dict[str, Any]) -> None:
    """Raise ValueError if the condition dict is not a recognised type."""
    known_types = {
        "days_without_revision",
        "missing_pmm_plan",
        "missing_evidence",
        "unlinked_deployments",
        "section_overdue",
    }
    rule_type = condition.get("type")
    if rule_type not in known_types:
        raise ValueError(
            f"Unknown rule type {rule_type!r}. "
            f"Must be one of: {', '.join(sorted(known_types))}"
        )

    if rule_type in {"days_without_revision", "section_overdue", "unlinked_deployments"}:
        threshold = condition.get("threshold")
        if threshold is None:
            raise ValueError(f"Rule type '{rule_type}' requires a 'threshold' field.")
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            raise ValueError(f"'threshold' must be a positive number, got {threshold!r}.")

    if rule_type in {"missing_evidence", "section_overdue"}:
        section = condition.get("section")
        if section is None:
            raise ValueError(f"Rule type '{rule_type}' requires a 'section' field.")
        if not isinstance(section, int) or not (1 <= section <= 9):
            raise ValueError(f"'section' must be an integer 1–9, got {section!r}.")


def suggest_rule_name(natural_language: str, condition: dict[str, Any]) -> str:
    """Generate a short human-readable rule name from the condition dict."""
    rule_type = condition.get("type", "")
    threshold = condition.get("threshold")
    section = condition.get("section")

    if rule_type == "days_without_revision":
        return f"TF revision overdue ({threshold} days)"
    if rule_type == "missing_pmm_plan":
        return "Missing PMM plan"
    if rule_type == "missing_evidence":
        return f"Missing validation evidence (section {section})"
    if rule_type == "unlinked_deployments":
        return "Unlinked deployments"
    if rule_type == "section_overdue":
        return f"Section {section} overdue ({threshold} days)"

    # Fallback: truncate natural language
    words = natural_language.strip().split()
    return " ".join(words[:8]) + ("…" if len(words) > 8 else "")
