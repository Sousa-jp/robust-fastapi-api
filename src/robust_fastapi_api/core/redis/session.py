from __future__ import annotations

import asyncio
from typing import Optional

from redis.asyncio import Redis

from ..settings import settings


class _RedisClientProvider:
    def __init__(self) -> None:
        self._client: Optional[Redis] = None
        self._lock = asyncio.Lock()

    async def get(self) -> Redis:
        async with self._lock:
            if self._client is None:
                self._client = Redis.from_url(settings.redis.url, decode_responses=True)
            return self._client


_provider = _RedisClientProvider()


async def get_redis_client() -> Redis:
    return await _provider.get()
