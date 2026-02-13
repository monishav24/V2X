"""
SmartV2X-CP Ultra — Redis Cache Layer
=======================================
Async Redis wrapper for caching vehicle states with TTL-based expiry.
Falls back to in-memory dict if Redis is unavailable.
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisCache:
    """Async Redis cache with automatic fallback to in-memory."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._url = redis_url
        self._redis = None
        self._fallback: Dict[str, str] = {}
        self._using_fallback = False

    async def connect(self):
        """Connect to Redis. Falls back to in-memory on failure."""
        if not REDIS_AVAILABLE:
            logger.warning("redis package not installed — using in-memory fallback")
            self._using_fallback = True
            return
        try:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connected: %s", self._url)
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — using in-memory fallback", exc)
            self._using_fallback = True

    async def close(self):
        if self._redis:
            await self._redis.close()

    # ── Key-Value operations ──────────────────────────────
    async def set(self, key: str, value: Any, ttl: int = 60):
        """Store a value with TTL (seconds)."""
        data = json.dumps(value) if not isinstance(value, str) else value
        if self._using_fallback:
            self._fallback[key] = data
            return
        await self._redis.set(key, data, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        if self._using_fallback:
            raw = self._fallback.get(key)
        else:
            raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def delete(self, key: str):
        if self._using_fallback:
            self._fallback.pop(key, None)
        else:
            await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        if self._using_fallback:
            return key in self._fallback
        return await self._redis.exists(key) > 0

    # ── Vehicle-specific helpers ──────────────────────────
    async def set_vehicle_state(self, vehicle_id: str, state: Dict):
        await self.set(f"vehicle:{vehicle_id}", state, ttl=60)

    async def get_vehicle_state(self, vehicle_id: str) -> Optional[Dict]:
        return await self.get(f"vehicle:{vehicle_id}")

    async def get_all_vehicle_keys(self):
        if self._using_fallback:
            return [k for k in self._fallback.keys() if k.startswith("vehicle:")]
        keys = []
        async for key in self._redis.scan_iter(match="vehicle:*"):
            keys.append(key)
        return keys
