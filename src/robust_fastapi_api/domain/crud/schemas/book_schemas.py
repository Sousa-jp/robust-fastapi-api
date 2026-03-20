from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_read: bool = False


class BookUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_read: Optional[bool] = None


class BookOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    is_read: bool
    deleted_at: Optional[datetime] = None


class BooksListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BookOut]
