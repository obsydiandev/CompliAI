"""Draft generator for Annex IV sections.

Generates LLM drafts for any of the 9 sections using structured prompts.
Supports both full-response and streaming (SSE) modes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Generator

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.ai_assistant import cache as _cache
from app.modules.ai_assistant.prompt_templates import SECTION_PROMPTS, SYSTEM_PROMPT
from app.modules.ai_assistant.usage_logger import log_usage

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v1.0"


def _openai_client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _build_section_prompt(
    section_number: int,
    system_name: str,
    description: str,
    intended_purpose: str,
    category: str,
    annex_iii: bool,
    existing_content: dict,
) -> str:
    template = SECTION_PROMPTS.get(section_number)
    if not template:
        raise ValueError(f"No prompt template for section {section_number}")

    existing_str = json.dumps(existing_content, indent=2) if existing_content else "{}"
    return template.format(
        system_name=system_name or "Unknown",
        description=description or "No description provided",
        intended_purpose=intended_purpose or "Not specified",
        category=category or "high_risk",
        annex_iii="Yes" if annex_iii else "No",
        existing_content=existing_str,
    )


def generate_section_draft(
    db: Session,
    *,
    section_number: int,
    system_name: str,
    description: str,
    intended_purpose: str,
    category: str,
    annex_iii: bool,
    existing_content: dict,
    org_id: str | None = None,
    user_id: str | None = None,
    ai_system_id: str | None = None,
) -> dict:
    """Generate a draft for a single section. Returns parsed JSON dict."""
    prompt = _build_section_prompt(
        section_number,
        system_name,
        description,
        intended_purpose,
        category,
        annex_iii,
        existing_content,
    )
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

    # Check cache
    cached = _cache.get_response_cache(prompt_hash)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass

    client = _openai_client()
    start = time.time()
    success = True
    error_msg = None
    prompt_tokens = 0
    completion_tokens = 0
    result: dict = {}

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        _cache.set_response_cache(prompt_hash, content)
    except Exception as exc:
        logger.error("Draft generation failed for section %d: %s", section_number, exc)
        success = False
        error_msg = str(exc)
        raise
    finally:
        latency = int((time.time() - start) * 1000)
        try:
            log_usage(
                db,
                feature=f"draft_section_{section_number}",
                model=settings.OPENAI_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                org_id=org_id,
                user_id=user_id,
                ai_system_id=ai_system_id,
                prompt_version=_PROMPT_VERSION,
                latency_ms=latency,
                success=success,
                error_message=error_msg,
            )
        except Exception:
            pass

    return result


def stream_section_draft(
    *,
    section_number: int,
    system_name: str,
    description: str,
    intended_purpose: str,
    category: str,
    annex_iii: bool,
    existing_content: dict,
    org_id: str | None = None,
    plan: str = "starter",
) -> Generator[str, None, None]:
    """Stream a section draft as SSE events.

    Yields SSE-formatted strings: ``data: <chunk>\\n\\n``.
    The final event is ``data: [DONE]\\n\\n``.
    """
    # Check rate limit before starting stream
    if org_id and not _cache.check_rate_limit(org_id, plan=plan):
        yield 'data: {"error": "Rate limit exceeded. Please wait before generating another draft."}\n\n'
        return

    prompt = _build_section_prompt(
        section_number,
        system_name,
        description,
        intended_purpose,
        category,
        annex_iii,
        existing_content,
    )

    client = _openai_client()
    try:
        stream = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield f"data: {json.dumps({'delta': delta})}\n\n"
    except Exception as exc:
        logger.error("Streaming draft failed for section %d: %s", section_number, exc)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"
