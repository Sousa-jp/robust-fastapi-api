from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.db.session import get_session
from ...sse.sse_service import BooksSseService, get_books_sse_service
from ..repositories.book_repository import BooksRepository
from ..schemas.book_schemas import BookCreate, BookOut, BookUpdate


class BooksService:
    def __init__(self, repository: BooksRepository, sse: BooksSseService) -> None:
        self._repository = repository
        self._sse = sse

    async def create_book(self, payload: BookCreate) -> BookOut:
        record = await self._repository.create(name=payload.name, is_read=payload.is_read)
        await self._sse.notify_book_change(event="book_created", record=record)
        return BookOut(
            id=record.id,
            name=record.name,
            created_at=record.created_at,
            is_read=record.is_read,
            deleted_at=record.deleted_at,
        )

    async def list_books(self, limit: int, offset: int) -> tuple[int, int, int, list[BookOut]]:
        records, total = await self._repository.list_active(limit=limit, offset=offset)
        items = [
            BookOut(
                id=r.id,
                name=r.name,
                created_at=r.created_at,
                is_read=r.is_read,
                deleted_at=r.deleted_at,
            )
            for r in records
        ]
        return total, limit, offset, items

    async def get_book(self, book_id: UUID) -> BookOut:
        record = await self._repository.get_active(book_id=book_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        return BookOut(
            id=record.id,
            name=record.name,
            created_at=record.created_at,
            is_read=record.is_read,
            deleted_at=record.deleted_at,
        )

    async def update_book(self, book_id: UUID, payload: BookUpdate) -> BookOut:
        record = await self._repository.update_active(
            book_id,
            name=payload.name,
            is_read=payload.is_read,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        await self._sse.notify_book_change(event="book_updated", record=record)
        return BookOut(
            id=record.id,
            name=record.name,
            created_at=record.created_at,
            is_read=record.is_read,
            deleted_at=record.deleted_at,
        )

    async def delete_book(self, book_id: UUID) -> BookOut:
        record = await self._repository.soft_delete(book_id=book_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        await self._sse.notify_book_change(event="book_deleted", record=record)
        return BookOut(
            id=record.id,
            name=record.name,
            created_at=record.created_at,
            is_read=record.is_read,
            deleted_at=record.deleted_at,
        )


def get_books_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    sse: Annotated[BooksSseService, Depends(get_books_sse_service)],
) -> BooksService:
    return BooksService(repository=BooksRepository(session=session), sse=sse)
