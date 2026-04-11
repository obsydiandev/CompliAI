"""Redis-backed cache for embeddings and LLM responses.

Provides a simple key-value cache with TTL.  Falls back gracefully
if Redis is unavailable so that the assistant still works without caching.
"""

from __future__ import annotations

import hashlib
import json
import logging

logger = logging.getLogger(__name__)

_redis_client = None
_EMBEDDING_TTL = 60 * 60 * 24 * 7  # 7 days
_RESPONSE_TTL = 60 * 60 * 4  # 4 hours


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis

            from app.config import settings

            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
            _redis_client.ping()
        except Exception as exc:
            logger.warning("Redis unavailable, caching disabled: %s", exc)
            _redis_client = False  # Mark as unavailable
    return _redis_client if _redis_client else None


def _cache_key(namespace: str, *parts: str) -> str:
    raw = ":".join([namespace, *parts])
    return "compliai:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_embedding_cache(text: str, model: str) -> list[float] | None:
    client = _get_redis()
    if not client:
        return None
    try:
        key = _cache_key("emb", model, text)
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as exc:
        logger.debug("Cache get error: %s", exc)
    return None


def set_embedding_cache(text: str, model: str, embedding: list[float]) -> None:
    client = _get_redis()
    if not client:
        return
    try:
        key = _cache_key("emb", model, text)
        client.setex(key, _EMBEDDING_TTL, json.dumps(embedding))
    except Exception as exc:
        logger.debug("Cache set error: %s", exc)


def get_response_cache(prompt_hash: str) -> str | None:
    client = _get_redis()
    if not client:
        return None
    try:
        key = _cache_key("resp", prompt_hash)
        value = client.get(key)
        if value:
            return value.decode("utf-8") if isinstance(value, bytes) else value
    except Exception as exc:
        logger.debug("Cache get error: %s", exc)
    return None


def set_response_cache(prompt_hash: str, response: str) -> None:
    client = _get_redis()
    if not client:
        return
    try:
        key = _cache_key("resp", prompt_hash)
        client.setex(key, _RESPONSE_TTL, response.encode("utf-8"))
    except Exception as exc:
        logger.debug("Cache set error: %s", exc)


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


# ── Rate limiting ─────────────────────────────────────────────────────────────

_RATE_LIMIT_WINDOW = 60  # seconds

# Requests per window per org, keyed by billing plan.
# Starter: conservative burst guard; Pro: relaxed; Enterprise: effectively unlimited.
_PLAN_RATE_LIMITS: dict[str, int] = {
    "starter": 10,
    "pro": 30,
    "enterprise": 200,
}
_RATE_LIMIT_DEFAULT = 10  # fallback when plan is unknown


def check_rate_limit(org_id: str, plan: str = "starter") -> bool:
    """Returns True if the request is allowed, False if rate-limited.

    Parameters
    ----------
    org_id:
        UUID of the organization (used as Redis key).
    plan:
        Billing plan of the organization — one of ``"starter"``, ``"pro"``,
        or ``"enterprise"``.  Determines the per-window request cap.
    """
    client = _get_redis()
    if not client:
        return True  # Allow if Redis unavailable
    limit = _PLAN_RATE_LIMITS.get(plan, _RATE_LIMIT_DEFAULT)
    try:
        key = f"compliai:rl:{org_id}"
        current = client.incr(key)
        if current == 1:
            client.expire(key, _RATE_LIMIT_WINDOW)
        return int(current) <= limit
    except Exception as exc:
        logger.debug("Rate limit check error: %s", exc)
        return True  # Allow on error
