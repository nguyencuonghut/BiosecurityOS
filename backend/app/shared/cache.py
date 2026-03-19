"""Redis cache utility for performance optimization (Sprint 11).

Provides a simple JSON cache backed by Redis with configurable TTL.
"""

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Lazy-init a shared Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _pool


async def close_redis() -> None:
    """Close the pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def cache_get(key: str) -> Any | None:
    """Return cached JSON value or None."""
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Store a JSON-serialisable value with TTL in seconds."""
    r = await get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern."""
    r = await get_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break
