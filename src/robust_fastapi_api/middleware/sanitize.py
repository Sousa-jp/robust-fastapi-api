import json
import urllib.parse
from typing import Awaitable, Callable, override

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.security.sanitizer import is_dangerous, payload_contains_attack
from ..core.settings import settings


def _ignore_path(path: str) -> bool:
    ignore = set(settings.logging.ignore_paths)
    return path in ignore or "*" in ignore


def _parse_body(body_bytes: bytes):
    if not body_bytes:
        return None
    try:
        return json.loads(body_bytes)
    except (json.JSONDecodeError, TypeError):
        try:
            decoded = body_bytes.decode(errors="ignore")
            parsed = urllib.parse.parse_qs(decoded, keep_blank_values=True)
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        except Exception:
            return body_bytes.decode(errors="replace")


class SanitizeMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if _ignore_path(request.url.path):
            return await call_next(request)

        if is_dangerous(request.url.path):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"},
            )

        for _key, value in request.query_params.multi_items():
            if is_dangerous(value):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request"},
                )

        body_bytes = b""
        read_body = request.method not in {"GET", "HEAD", "OPTIONS"}
        if read_body:
            try:
                body_bytes = await request.body()
            except Exception:
                pass
            payload = _parse_body(body_bytes)
            if payload is not None and payload_contains_attack(payload):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request"},
                )

        if read_body:

            async def receive():
                return {"type": "http.request", "body": body_bytes}

            request = Request(request.scope, receive)

        return await call_next(request)
