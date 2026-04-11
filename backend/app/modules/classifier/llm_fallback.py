"""LLM fallback classifier for edge-case AI Act risk assessment.

Called when the deterministic Annex III decision tree marks a result as
``is_edge_case=True`` or when the caller explicitly requests LLM review.
"""

from __future__ import annotations

import json
import logging

from app.config import settings
from app.modules.classifier.annex3_rules import ClassificationResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert EU AI Act compliance lawyer.
You analyse AI systems and classify them according to the EU AI Act risk categories:
- high_risk: listed in Annex III or Art. 6(1), requires Annex IV Technical File
- limited_risk: transparency obligations only (Art. 52)
- minimal_risk: no mandatory obligations

Respond ONLY with a valid JSON object with keys:
  risk_level (string: "high_risk" | "limited_risk" | "minimal_risk"),
  justification (string: 2-3 sentence explanation),
  article_citations (list of strings),
  annex_iii_category (string or null)
"""


def classify_with_llm(
    answers: dict,
    preliminary_result: ClassificationResult | None = None,
) -> ClassificationResult:
    """Use GPT-4o to review an edge-case classification.

    Falls back gracefully to the preliminary_result on any error.
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        description = answers.get("q10", "No description provided")
        sector = answers.get("q2", "Unknown")
        function_ = answers.get("q1", "Unknown")
        preliminary = preliminary_result.risk_level if preliminary_result else "unknown"

        user_message = (
            f"AI system description: {description}\n"
            f"Sector: {sector}\n"
            f"Primary function: {function_}\n"
            f"Preliminary classification: {preliminary}\n\n"
            "Please confirm or correct this classification with full justification."
        )

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ClassificationResult(
            risk_level=data.get("risk_level", preliminary_result.risk_level if preliminary_result else "minimal_risk"),
            justification=data.get("justification", ""),
            article_citations=data.get("article_citations", []),
            annex_iii_category=data.get("annex_iii_category"),
            is_edge_case=True,
        )

    except Exception as exc:
        logger.warning("LLM classifier fallback failed: %s", exc)
        if preliminary_result:
            return preliminary_result
        return ClassificationResult(
            risk_level="high_risk",
            justification=(
                "Unable to automatically determine risk level. We recommend treating this "
                "system as high-risk and preparing Annex IV documentation as a precaution."
            ),
            article_citations=["Art. 6 AI Act — Classification of high-risk AI systems"],
            is_edge_case=True,
        )
