from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket

from .socket_service import SocketChatService, get_socket_chat_service

router = APIRouter(prefix="/ws", tags=["websocket"])


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
async def chat(
    websocket: WebSocket,
    service: Annotated[SocketChatService, Depends(get_socket_chat_service)],
) -> None:
    await service.handle_chat(websocket=websocket)
