from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from .sse_service import BooksSseService, get_books_sse_service

router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/books")
async def books_sse(
    request: Request,
    service: Annotated[BooksSseService, Depends(get_books_sse_service)],
) -> StreamingResponse:
    generator = service.stream_books(request=request)
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    return StreamingResponse(generator, media_type="text/event-stream", headers=headers)
