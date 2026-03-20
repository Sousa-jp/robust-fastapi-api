import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["websocket"])

_active: Set[WebSocket] = set()


@router.get(
    "/chat",
    summary="WebSocket Chat (documentation)",
    description="""Connect to **WebSocket** `ws://{host}/v1/ws/chat`.
     Broadcast room: every message is sent to all connected clients.
     Send JSON: `{\"user\": \"string\", \"message\": \"string\"}`. Server echoes `{\"user\", \"message\"}` to all.
     Use a WebSocket client or browser DevTools to test.""",
)
def chat_doc() -> dict:
    return {
        "protocol": "websocket",
        "url": "ws://{host}/v1/ws/chat",
        "description": "Broadcast chat room. All connected clients receive every message.",
        "send": {"user": "string (optional, default: anonymous)", "message": "string"},
        "receive": {"user": "string", "message": "string"},
    }


@router.websocket("/chat")
async def chat(websocket: WebSocket) -> None:
    await websocket.accept()
    _active.add(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw) if raw.strip() else {}
            user = data.get("user", "anonymous")
            message = data.get("message", raw)
            payload = json.dumps({"user": user, "message": message})
            for conn in list(_active):
                try:
                    await conn.send_text(payload)
                except Exception:
                    _active.discard(conn)
    except WebSocketDisconnect:
        pass
    finally:
        _active.discard(websocket)
