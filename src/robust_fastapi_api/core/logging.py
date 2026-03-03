import logging
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from .settings import settings


def _redact_sensitive(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    sensitive = set(settings.logging.sensitive_keys)
    if not sensitive:
        return event_dict

    def sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: "********" if k in sensitive else sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    return {k: "********" if k in sensitive else sanitize(v) for k, v in event_dict.items()}


def configure_logging() -> None:
    level = settings.logging.level.upper()
    debug = settings.app.debug
    chain = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        _redact_sensitive,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    structlog.configure(
        processors=chain,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=chain[:-1],
        processor=structlog.dev.ConsoleRenderer(colors=True) if debug else structlog.processors.JSONRenderer(),
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
