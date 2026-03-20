from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from robust_fastapi_api.core.datetime import now
from robust_fastapi_api.core.db.base import Base


class UserOrigin(str, Enum):
    MANUAL = "manual"
    SOCIAL = "social"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    origin: Mapped[str] = mapped_column(String(20), nullable=False, default=UserOrigin.MANUAL.value)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    access_token_version: Mapped[int] = mapped_column(nullable=False, default=1)
    refresh_token_version: Mapped[int] = mapped_column(nullable=False, default=1)
