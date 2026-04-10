import logging

logger = logging.getLogger(__name__)


def get_cached(key: str) -> str | None:
    try:
        import redis
        from app.config import settings
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        return r.get(key)
    except Exception:
        return None


def set_cached(key: str, value: str, ttl: int = 3600) -> bool:
    try:
        import redis
        from app.config import settings
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.setex(key, ttl, value)
        return True
    except Exception:
        return False
