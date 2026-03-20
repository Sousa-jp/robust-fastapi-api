from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from redis.asyncio import Redis

from ...core.redis.session import get_redis_client
from ...core.settings import settings


def get_books_sse_channel() -> str:
    return f"{settings.app.name}:sse:books"


def _format_sse(data: str, event: str = "message") -> str:
    return f"event: {event}\ndata: {data}\n\n"


class BooksSseService:
    def __init__(self, redis: Redis, channel: str) -> None:
        self._redis = redis
        self._channel = channel

    async def stream_books(self, request: Request) -> AsyncIterator[str]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel)
        yield ": connected\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    return

                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                if message.get("type") != "message":
                    continue

                data: Any = message.get("data")
                if isinstance(data, bytes):
                    data = data.decode("utf-8", errors="replace")
                if data is None:
                    continue

                raw = data if isinstance(data, str) else str(data)
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    yield _format_sse(raw, event="book_update")
                    continue

                event_name = str(parsed.get("event") or "book_update")
                payload: Any = parsed.get("data", parsed)
                yield _format_sse(json.dumps(payload, default=str), event=event_name)
        finally:
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(self._channel)
            with contextlib.suppress(Exception):
                await pubsub.close()

    async def notify_book_change(self, *, event: str, record: Any) -> None:
        payload = {
            "id": getattr(record, "id", None),
            "name": getattr(record, "name", None),
            "is_read": getattr(record, "is_read", None),
            "created_at": getattr(record, "created_at", None),
            "deleted_at": getattr(record, "deleted_at", None),
        }
        with contextlib.suppress(Exception):
            await self._redis.publish(
                self._channel,
                json.dumps({"event": event, "data": payload}, default=str),
            )


async def get_books_sse_service() -> BooksSseService:
    redis = await get_redis_client()
    return BooksSseService(redis=redis, channel=get_books_sse_channel())


async def publish_book_change(redis: Redis, payload: dict[str, Any], event: str) -> None:
    await redis.publish(get_books_sse_channel(), json.dumps({"event": event, "data": payload}, default=str))
