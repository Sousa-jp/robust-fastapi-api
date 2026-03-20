from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .core.logging import configure_logging
from .core.settings import settings
from .domain.auth.routers.auth_router import router as auth_router
from .domain.crud.routers.book_router import router as books_router
from .domain.socket.socket_router import router as socket_router
from .domain.sse.sse_router import router as sse_router
from .domain.users.routers.users_router import router as users_router
from .health import router as health_router
from .middleware.log_request import LogRequestMiddleware
from .middleware.sanitize import SanitizeMiddleware

configure_logging()

app = FastAPI(
    title=settings.app.name,
    description=settings.app.description,
    version=settings.app.version,
)

app.add_middleware(LogRequestMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)
app.add_middleware(SanitizeMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.security.secret_key,
    same_site="none" if settings.dns_on else "lax",
    https_only=settings.security.session_https_only,
    max_age=int(settings.security.access_token_expire_minutes * 60),
)

app.include_router(health_router, prefix="/v1")
app.include_router(books_router, prefix="/v1")
app.include_router(sse_router, prefix="/v1")
app.include_router(socket_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
