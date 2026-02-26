import json
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5
        )
    return _redis_client


def cache_get(key: str):
    try:
        client = get_redis_client()
        data = client.get(key)
        if data:
            logger.debug(f"Cache HIT - key: {key}")
            return json.loads(data)
        logger.debug(f"Cache MISS - key: {key}")
        return None
    except Exception as e:
        logger.warning(f"Redis GET failed, falling back to DB - key: {key}, error: {e}")
        return None


def cache_set(key: str, value, ttl: int = 300):
    try:
        client = get_redis_client()
        client.setex(key, ttl, json.dumps(value))
        logger.debug(f"Cache SET - key: {key}, ttl: {ttl}s")
    except Exception as e:
        logger.warning(f"Redis SET failed - key: {key}, error: {e}")


def cache_delete(key: str):
    try:
        client = get_redis_client()
        client.delete(key)
        logger.debug(f"Cache DELETE - key: {key}")
    except Exception as e:
        logger.warning(f"Redis DELETE failed - key: {key}, error: {e}")


def cache_delete_pattern(pattern: str):
    try:
        client = get_redis_client()
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
            logger.debug(f"Cache DELETE pattern: {pattern}, keys deleted: {len(keys)}")
    except Exception as e:
        logger.warning(f"Redis DELETE pattern failed - pattern: {pattern}, error: {e}")