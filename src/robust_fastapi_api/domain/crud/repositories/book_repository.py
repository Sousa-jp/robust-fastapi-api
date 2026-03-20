from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from robust_fastapi_api.core.datetime import now

from ..models.book_model import Book


class BooksRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, is_read: bool) -> Book:
        record = Book(name=name, is_read=is_read)
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def list_active(self, limit: int, offset: int) -> tuple[list[Book], int]:
        count_stmt = select(func.count()).select_from(Book).where(Book.deleted_at.is_(None))
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(Book).where(Book.deleted_at.is_(None)).order_by(Book.id).limit(limit).offset(offset)
        records = (await self._session.execute(stmt)).scalars().all()
        return records, int(total)

    async def get_active(self, book_id: UUID) -> Optional[Book]:
        stmt = select(Book).where(Book.id == book_id, Book.deleted_at.is_(None))
        return (await self._session.execute(stmt)).scalars().first()

    async def update_active(
        self,
        book_id: UUID,
        *,
        name: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> Optional[Book]:
        record = await self.get_active(book_id=book_id)
        if record is None:
            return None
        if name is not None:
            record.name = name
        if is_read is not None:
            record.is_read = is_read
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def soft_delete(self, book_id: UUID) -> Optional[Book]:
        record = await self.get_active(book_id=book_id)
        if record is None:
            return None
        record.deleted_at = now()
        await self._session.commit()
        await self._session.refresh(record)
        return record
