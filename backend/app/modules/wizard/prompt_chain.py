"""LLM prompt chain for the Lite Wizard (Epic 0).

Converts user answers from each wizard block into formal Annex IV paragraphs.
These prompts are intentionally simpler than the Pro draft_generator prompts —
they're focused on translating 5–8 user answers per block into a single
well-structured paragraph in regulatory language.

Per PRD v1.15 §1.3: 'LLM as translator, not decision-maker.'
LLM transforms user input → formal paragraph.  LLM does NOT invent content.
"""

from __future__ import annotations

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a legal-technical writer specialising in EU AI Act documentation.
Your task is to transform user-provided answers about an AI system into a formal Annex IV
Technical File paragraph. Write in clear, professional regulatory language suitable for
submission to a national supervisory authority.

Rules:
1. Use ONLY the information provided in the answers — do NOT invent details.
2. If an answer is missing or empty, note it as '[TO BE COMPLETED]' in the output.
3. Output a single well-structured paragraph (or short numbered list) of 100–300 words.
4. Do NOT include headings — only the paragraph text.
5. Write in English, formal register.
6. Do NOT use the word 'compliance' — use 'conformity' or 'conformance' instead."""


_BLOCK_PROMPTS: dict[str, str] = {
    "B1": """Generate an Annex IV §1 paragraph covering system identification and intended purpose.

User answers:
{answers_json}

Write the paragraph covering: system name, version, intended purpose, end-users, and deployment territory.""",

    "B2": """Generate Annex IV §2 (system description) and §3 (training data) paragraphs.

User answers:
{answers_json}

Write two short paragraphs:
1. Architecture and infrastructure (based on architecture type, inputs, integrations, hosting).
2. Training data (based on training data description, preprocessing, special categories, quality measures).""",

    "B3": """Generate an Annex IV §4 (validation and testing) paragraph.

User answers:
{answers_json}

Write a paragraph covering: performance metrics, validation methodology, fairness/bias testing,
known limitations, third-party testing (if any), and cybersecurity measures.""",

    "B4": """Generate an Annex IV §6 (risk management) paragraph.

User answers:
{answers_json}

Write a paragraph covering: risk management process and responsibility, identified risks,
mitigation measures, residual risks, real-world testing, and system ownership.""",

    "B5": """Generate an Annex IV §5 (monitoring, operation, and control) paragraph.

User answers:
{answers_json}

Write a paragraph covering: human override capability, human-in-the-loop process,
operator training requirements, low-confidence notifications, and emergency shutdown procedure.""",

    "B6": """Generate an Annex IV §7 (post-market monitoring) paragraph.

User answers:
{answers_json}

Write a paragraph covering: monitoring metrics, update/retraining frequency,
incident reporting process, and affected persons' rights to information and appeal.""",

    "B7": """Generate Annex IV §8 (standards) and §9 (declaration of conformity) text.

User answers:
{answers_json}

Write two short paragraphs:
1. Applicable harmonised standards, third-party certification, and other EU regulations.
2. Provider identification for EU Declaration of Conformity (Art. 47 / Annex V).""",
}


def generate_block_paragraph(
    block_id: str,
    answers: dict,
    openai_api_key: str | None = None,
) -> str:
    """Generate a formal Annex IV paragraph for a wizard block.

    Args:
        block_id: "B1" … "B7"
        answers: dict of {question_id: answer_value} for this block
        openai_api_key: optional override (for BYOK)

    Returns the generated paragraph as a string.
    Raises ValueError if block_id is unknown.
    """
    prompt_template = _BLOCK_PROMPTS.get(block_id)
    if not prompt_template:
        raise ValueError(f"Unknown wizard block: {block_id}")

    answers_json = json.dumps(answers, ensure_ascii=False, indent=2)
    user_prompt = prompt_template.format(answers_json=answers_json)

    api_key = openai_api_key or settings.OPENAI_API_KEY
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — returning placeholder paragraph")
        return (
            f"[AI DRAFT UNAVAILABLE — OpenAI API key not configured]\n\n"
            f"Please complete this section manually based on your answers:\n{answers_json}"
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.error("Wizard paragraph generation failed for block %s: %s", block_id, exc)
        raise


def stream_block_paragraph(
    block_id: str,
    answers: dict,
    openai_api_key: str | None = None,
):
    """Stream a block paragraph as SSE events.

    Yields SSE-formatted strings: ``data: <json>\\n\\n``.
    Final event: ``data: [DONE]\\n\\n``.
    """
    import json as _json

    prompt_template = _BLOCK_PROMPTS.get(block_id)
    if not prompt_template:
        yield f'data: {_json.dumps({"error": f"Unknown block {block_id}"})}\n\n'
        return

    answers_json = _json.dumps(answers, ensure_ascii=False, indent=2)
    user_prompt = prompt_template.format(answers_json=answers_json)

    api_key = openai_api_key or settings.OPENAI_API_KEY
    if not api_key:
        yield f'data: {_json.dumps({"delta": "[AI draft unavailable — configure OPENAI_API_KEY]"})}\n\n'
        yield "data: [DONE]\n\n"
        return

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        stream = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=800,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield f"data: {_json.dumps({'delta': delta})}\n\n"
    except Exception as exc:
        logger.error("Streaming wizard paragraph failed for block %s: %s", block_id, exc)
        yield f"data: {_json.dumps({'error': str(exc)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"
