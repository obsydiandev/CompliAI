"""Documentation impact analysis (Documentation Diff).

Given a change in AI system metadata or a new model version, analyses
which Annex IV sections are affected and provides draft update guidance.
"""

from __future__ import annotations

import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.ai_assistant.prompt_templates import DOC_DIFF_PROMPT, SYSTEM_PROMPT
from app.modules.ai_assistant.usage_logger import log_usage

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v1.0"


def analyse_documentation_impact(
    db: Session,
    *,
    system_name: str,
    previous_metadata: dict,
    new_metadata: dict,
    org_id: str | None = None,
    user_id: str | None = None,
    ai_system_id: str | None = None,
) -> list[dict]:
    """Analyse which sections need updating after a metadata change.

    Returns a list of dicts:
        [{section_number, section_name, reason, draft_changes}, ...]
    """
    prev_str = json.dumps(previous_metadata, indent=2)
    new_str = json.dumps(new_metadata, indent=2)

    prompt = DOC_DIFF_PROMPT.format(
        system_name=system_name,
        previous_metadata=prev_str,
        new_metadata=new_str,
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
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        content = response.choices[0].message.content or '{"sections": []}'
        parsed = json.loads(content)
        # Support both {"sections": [...]} and [...]
        if isinstance(parsed, list):
            return parsed
        return parsed.get("sections", parsed.get("items", []))
    except Exception as exc:
        logger.error("Documentation diff failed: %s", exc)
        success = False
        error_msg = str(exc)
        raise
    finally:
        try:
            log_usage(
                db,
                feature="doc_diff",
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
