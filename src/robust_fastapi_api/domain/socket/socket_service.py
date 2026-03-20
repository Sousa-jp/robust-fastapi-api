from __future__ import annotations

import asyncio
import contextlib
import json

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from ...core.redis.session import get_redis_client
from ...core.settings import settings


class SocketChatService:
    def __init__(self, redis: Redis, channel: str) -> None:
        self._redis = redis
        self._channel = channel

    async def handle_chat(self, websocket: WebSocket) -> None:
        await websocket.accept()
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel)
        forward_task = asyncio.create_task(self._forward_pubsub(websocket=websocket, pubsub=pubsub))
        try:
            while True:
                raw = await websocket.receive_text()
                if not raw.strip():
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "detail": 'Invalid message format. Send JSON: {"user": "string", "message": "string"}',
                            }
                        )
                    )
                    continue
                if not isinstance(data, dict) or "message" not in data:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "detail": 'Invalid message format. Send JSON: {"user": "string", "message": "string"}',
                            }
                        )
                    )
                    continue
                user = data.get("user", "anonymous")
                message = data["message"]
                payload = json.dumps({"user": user, "message": message})
                await self._redis.publish(self._channel, payload)
        except WebSocketDisconnect:
            pass
        finally:
            forward_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await forward_task
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(self._channel)
            with contextlib.suppress(Exception):
                await pubsub.close()

    @staticmethod
    async def _forward_pubsub(websocket: WebSocket, pubsub) -> None:
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None and message.get("type") == "message":
                    data = message.get("data")
                    if isinstance(data, bytes):
                        data = data.decode("utf-8", errors="replace")
                    if data is not None:
                        await websocket.send_text(str(data))
        except asyncio.CancelledError:
            raise
        except Exception:
            return


def get_chat_channel() -> str:
    return f"{settings.app.name}:ws:chat"


async def get_socket_chat_service() -> SocketChatService:
    redis = await get_redis_client()
    return SocketChatService(redis=redis, channel=get_chat_channel())

