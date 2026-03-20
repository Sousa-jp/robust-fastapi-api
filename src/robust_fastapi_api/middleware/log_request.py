import asyncio
import json
import time
import traceback
import urllib.parse
from typing import Any, Awaitable, Callable

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse

from ..core.settings import settings

log = structlog.get_logger()


def _ignore_path(path: str) -> bool:
    ignore = set(settings.logging.ignore_paths)
    return path in ignore or "*" in ignore


def _parse_body(body_bytes: bytes) -> Any:
    if not body_bytes:
        return ""
    try:
        return json.loads(body_bytes)
    except (json.JSONDecodeError, TypeError):
        try:
            decoded = body_bytes.decode(errors="ignore")
            parsed = urllib.parse.parse_qs(decoded, keep_blank_values=True)
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        except Exception:
            return body_bytes.decode(errors="replace")


def _log_level(status_code: int) -> str:
    if status.HTTP_400_BAD_REQUEST <= status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "warning"
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "error"
    return "info"


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if _ignore_path(request.url.path):
            return await call_next(request)

        body_bytes = b""
        try:
            body_bytes = await request.body()
        except Exception:
            pass

        start = time.perf_counter()
        error = None
        error_info = None

        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            tb = traceback.extract_tb(e.__traceback__)
            error_info = (
                {
                    "file": tb[-1].filename,
                    "line": tb[-1].lineno,
                    "function": tb[-1].name,
                }
                if tb
                else {"file": "unknown", "line": 0, "function": "unknown"}
            )
            response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

        duration_ms = (time.perf_counter() - start) * 1000
        response_body_bytes = b""
        try:
            is_sse = isinstance(response, StreamingResponse) and response.media_type == "text/event-stream"
            is_sse_header = response.headers.get("content-type", "").startswith("text/event-stream")
            if not is_sse and not is_sse_header:
                chunks = [section async for section in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(chunks))
                if chunks:
                    response_body_bytes = b"".join(chunks)
        except Exception:
            pass

        request_body = _parse_body(body_bytes)
        response_body = _parse_body(response_body_bytes) if error is None else {"detail": "Internal Server Error"}
        level = _log_level(response.status_code)
        log_kw = {
            "message": f"{request.method} {response.status_code} {request.url.path}",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_host": request.client.host if request.client else None,
            "request_body": request_body,
            "response_body": response_body,
        }
        if error is not None and error_info:
            log_kw["error"] = str(error)
            log_kw["error_info"] = error_info

        asyncio.create_task(self._emit(level, log_kw))
        return response

    @staticmethod
    async def _emit(level: str, data: dict) -> None:
        try:
            getattr(log, level)(**data)
        except Exception as e:
            log.error("log_request_emit_failed", error=str(e))
