from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from robust_fastapi_api.core.db.session import get_session

from ..models.oauth_token_model import OAuthToken


class OAuthTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_user_and_provider(self, user_id: UUID, provider: str) -> Optional[OAuthToken]:
        stmt = select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == provider)
        return await self._session.scalar(stmt)

    async def save(self, oauth_token: OAuthToken) -> OAuthToken:
        self._session.add(oauth_token)
        await self._session.commit()
        await self._session.refresh(oauth_token)
        return oauth_token


def get_oauth_token_repository(session: AsyncSession = Depends(get_session)) -> OAuthTokenRepository:
    return OAuthTokenRepository(session)
