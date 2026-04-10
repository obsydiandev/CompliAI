"""LLM usage logger.

Records token consumption and cost to the llm_usage_logs table.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.llm_usage import LLMUsageLog

logger = logging.getLogger(__name__)

# Cost per 1K tokens (USD) for common OpenAI models
_MODEL_COST: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.005, 0.015),  # input, output per 1K tokens
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "text-embedding-3-small": (0.00002, 0.0),
    "text-embedding-3-large": (0.00013, 0.0),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD for a given model and token counts."""
    costs = _MODEL_COST.get(model, (0.01, 0.03))
    return (prompt_tokens * costs[0] + completion_tokens * costs[1]) / 1000.0


def log_usage(
    db: Session,
    *,
    feature: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    org_id: str | None = None,
    user_id: str | None = None,
    ai_system_id: str | None = None,
    prompt_version: str | None = None,
    latency_ms: int | None = None,
    success: bool = True,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> LLMUsageLog:
    """Persist a usage log entry. Silently logs errors to avoid disrupting callers."""
    try:
        total_tokens = prompt_tokens + completion_tokens
        cost = estimate_cost(model, prompt_tokens, completion_tokens)

        entry = LLMUsageLog(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id) if org_id else None,
            user_id=uuid.UUID(user_id) if user_id else None,
            ai_system_id=uuid.UUID(ai_system_id) if ai_system_id else None,
            feature=feature,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
            success=1 if success else 0,
            error_message=error_message,
            metadata_=metadata,
            created_at=datetime.now(UTC),
        )
        db.add(entry)
        db.commit()
        return entry
    except Exception as exc:
        logger.warning("Failed to log LLM usage: %s", exc)
        db.rollback()
        raise
