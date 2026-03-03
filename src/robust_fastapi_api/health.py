import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .core.health import check_database, check_redis

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    api: HealthStatus
    database: HealthStatus
    redis: HealthStatus


@router.get("/health", response_model=HealthResponse)
async def health():
    database, redis = await asyncio.gather(check_database(), check_redis())
    return HealthResponse(api=HealthStatus(status="ok"), database=HealthStatus(**database), redis=HealthStatus(**redis))
