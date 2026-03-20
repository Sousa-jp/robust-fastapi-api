from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from robust_fastapi_api.core.db.session import get_session

from ..models.unverified_user_model import UnverifiedUser


class UnverifiedUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_email(self, email: str) -> Optional[UnverifiedUser]:
        stmt = select(UnverifiedUser).where(UnverifiedUser.email == email)
        return await self._session.scalar(stmt)

    async def find_by_id(self, user_id: UUID) -> Optional[UnverifiedUser]:
        stmt = select(UnverifiedUser).where(UnverifiedUser.id == user_id)
        return await self._session.scalar(stmt)

    async def save(self, user: UnverifiedUser) -> UnverifiedUser:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user: UnverifiedUser) -> None:
        self._session.delete(user)
        await self._session.commit()


def get_unverified_user_repository(session: AsyncSession = Depends(get_session)) -> UnverifiedUserRepository:
    return UnverifiedUserRepository(session)
