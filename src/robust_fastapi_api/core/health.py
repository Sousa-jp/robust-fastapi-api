from typing import Any

import asyncpg
from redis.asyncio import Redis

from .settings import settings


async def check_database() -> dict[str, Any]:
    if not settings.database.url or not settings.database.url.strip():
        return {"status": "disabled"}
    try:
        dsn = settings.database.url.replace("postgresql+asyncpg://", "postgresql://", 1)
        conn = await asyncpg.connect(dsn)
        await conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def check_redis() -> dict[str, Any]:
    if not settings.redis.url or not settings.redis.url.strip():
        return {"status": "disabled"}
    try:
        client = Redis.from_url(settings.redis.url)
        await client.ping()
        await client.aclose()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
