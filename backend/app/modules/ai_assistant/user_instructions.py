"""User Instructions generator (EU AI Act Art. 13).

Generates a plain-language "Instructions for Use" document from the
Technical File sections, as required by Art. 13 of EU Regulation 2024/1689.
"""

from __future__ import annotations

import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.ai_assistant.prompt_templates import SYSTEM_PROMPT, USER_INSTRUCTIONS_PROMPT
from app.modules.ai_assistant.usage_logger import log_usage

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v1.0"


def generate_user_instructions(
    db: Session,
    *,
    system_name: str,
    intended_purpose: str,
    category: str,
    section_5_content: dict,
    section_6_content: dict,
    section_7_content: dict,
    org_id: str | None = None,
    user_id: str | None = None,
    ai_system_id: str | None = None,
) -> str:
    """Generate a Markdown "Instructions for Use" document (Art. 13).

    Returns the document as a Markdown string.
    """
    prompt = USER_INSTRUCTIONS_PROMPT.format(
        system_name=system_name,
        intended_purpose=intended_purpose or "Not specified",
        category=category,
        section_5_content=json.dumps(section_5_content, indent=2) if section_5_content else "{}",
        section_6_content=json.dumps(section_6_content, indent=2) if section_6_content else "{}",
        section_7_content=json.dumps(section_7_content, indent=2) if section_7_content else "{}",
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
            temperature=0.3,
            max_tokens=3000,
        )
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("User instructions generation failed: %s", exc)
        success = False
        error_msg = str(exc)
        raise
    finally:
        try:
            log_usage(
                db,
                feature="user_instructions",
                model=settings.OPENAI_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                org_id=org_id,
                user_id=user_id,
                ai_system_id=ai_system_id,
                prompt_version=_PROMPT_VERSION,
                success=success,
                error_message=error_msg,
            )
        except Exception:
            pass
