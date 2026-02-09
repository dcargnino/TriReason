"""Redis caching layer for prompt/output pairs and run results."""

from __future__ import annotations

import json
import logging

import redis.asyncio as redis

from trireason.config import settings

logger = logging.getLogger(__name__)

_pool: redis.Redis | None = None

# Cache TTLs (seconds)
RUN_TTL = 3600  # 1 hour
PROMPT_PAIR_TTL = 86400  # 24 hours


async def get_redis() -> redis.Redis:
    """Return a shared async Redis client."""
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ── Run result caching ─────────────────────────────────────────────


def _run_key(run_id: str) -> str:
    return f"trireason:run:{run_id}"


async def cache_run_result(run_id: str, result: dict) -> None:
    """Cache a completed optimization run result."""
    r = await get_redis()
    await r.set(_run_key(run_id), json.dumps(result), ex=RUN_TTL)


async def get_cached_run(run_id: str) -> dict | None:
    """Retrieve a cached run result, or None if not found."""
    r = await get_redis()
    raw = await r.get(_run_key(run_id))
    if raw is None:
        return None
    return json.loads(raw)


# ── Prompt/output pair caching ──────────────────────────────────────


def _pair_key(data_hash: str, objective_hash: str) -> str:
    return f"trireason:pair:{data_hash}:{objective_hash}"


async def cache_prompt_pair(data_hash: str, objective_hash: str, result: dict) -> None:
    """Cache a prompt/output pair keyed by content hashes."""
    r = await get_redis()
    await r.set(_pair_key(data_hash, objective_hash), json.dumps(result), ex=PROMPT_PAIR_TTL)


async def get_cached_pair(data_hash: str, objective_hash: str) -> dict | None:
    """Retrieve a cached prompt/output pair."""
    r = await get_redis()
    raw = await r.get(_pair_key(data_hash, objective_hash))
    if raw is None:
        return None
    return json.loads(raw)
