from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..schemas.book_schemas import BookCreate, BookOut, BooksListResponse, BookUpdate
from ..services.book_service import BooksService, get_books_service

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookOut)
async def create_book(
    payload: BookCreate,
    service: Annotated[BooksService, Depends(get_books_service)],
) -> BookOut:
    return await service.create_book(payload)


@router.get("", response_model=BooksListResponse)
async def list_books(
    service: Annotated[BooksService, Depends(get_books_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BooksListResponse:
    total, applied_limit, applied_offset, items = await service.list_books(limit=limit, offset=offset)
    return BooksListResponse(total=total, limit=applied_limit, offset=applied_offset, items=items)


@router.get("/{book_id}", response_model=BookOut)
async def get_book(
    book_id: UUID,
    service: Annotated[BooksService, Depends(get_books_service)],
) -> BookOut:
    return await service.get_book(book_id=book_id)


@router.patch("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: UUID,
    payload: BookUpdate,
    service: Annotated[BooksService, Depends(get_books_service)],
) -> BookOut:
    return await service.update_book(book_id=book_id, payload=payload)


@router.delete("/{book_id}", response_model=BookOut)
async def delete_book(
    book_id: UUID,
    service: Annotated[BooksService, Depends(get_books_service)],
) -> BookOut:
    return await service.delete_book(book_id=book_id)
