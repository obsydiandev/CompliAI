"""Inline suggestions for missing Annex IV section fields.

For each missing required field, the assistant provides a brief,
actionable suggestion explaining what should be added and why.
"""

from __future__ import annotations

import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.ai_assistant.prompt_templates import SUGGESTIONS_PROMPT, SYSTEM_PROMPT
from app.modules.ai_assistant.usage_logger import log_usage
from app.modules.annex_iv_core.schemas import SECTION_NAMES

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v1.0"


def get_section_suggestions(
    db: Session,
    *,
    section_number: int,
    current_content: dict,
    missing_fields: list[str],
    org_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    """Return per-field suggestions for missing required fields.

    Returns a dict mapping field_key -> suggestion_text.
    """
    if not missing_fields:
        return {}

    section_name = SECTION_NAMES.get(section_number, f"Section {section_number}")
    content_str = json.dumps(current_content, indent=2) if current_content else "{}"
    missing_str = ", ".join(missing_fields)

    prompt = SUGGESTIONS_PROMPT.format(
        section_number=section_number,
        section_name=section_name,
        current_content=content_str,
        missing_fields=missing_str,
    )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt_tokens = 0
    completion_tokens = 0
    success = True
    error_msg = None

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        # Ensure we only return suggestions for the missing fields
        return {k: str(v) for k, v in result.items() if k in missing_fields}
    except Exception as exc:
        logger.error("Suggestions generation failed for section %d: %s", section_number, exc)
        success = False
        error_msg = str(exc)
        # Return empty hints on error so callers don't crash
        return {}
    finally:
        try:
            log_usage(
                db,
                feature=f"suggestions_section_{section_number}",
                model=settings.OPENAI_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                org_id=org_id,
                user_id=user_id,
                prompt_version=_PROMPT_VERSION,
                success=success,
                error_message=error_msg,
            )
        except Exception:
            pass
