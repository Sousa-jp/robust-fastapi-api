from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.logging import configure_logging
from .core.settings import settings
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

app.include_router(health_router, prefix="/v1")
