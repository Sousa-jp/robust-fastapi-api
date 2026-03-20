from __future__ import annotations

from datetime import datetime
from typing import Annotated, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from robust_fastapi_api.core.security.token import validate_access_token
from robust_fastapi_api.domain.users.models.user_model import User
from robust_fastapi_api.domain.users.repositories.user_repository import UserRepository, get_user_repository

BearerSchemeRefreshToken = Annotated[
    HTTPAuthorizationCredentials,
    Depends(HTTPBearer(scheme_name="Refresh token")),
]
BearerSchemeAccessToken = Annotated[
    HTTPAuthorizationCredentials,
    Depends(HTTPBearer(scheme_name="Access token")),
]

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: BearerSchemeAccessToken,
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    try:
        user, _, _ = await validate_access_token(
            token.credentials, token_type="access", user_repository=user_repository
        )
    except ValueError:
        raise credentials_exception
    return user


async def get_current_user_refresh(
    token: BearerSchemeRefreshToken,
    user_repository: UserRepository = Depends(get_user_repository),
) -> Tuple[User, str, datetime]:
    try:
        user, rfsh_token, expires_at = await validate_access_token(
            token.credentials, token_type="refresh", user_repository=user_repository
        )
    except ValueError:
        raise credentials_exception
    return user, rfsh_token, expires_at


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserRefresh = Annotated[Tuple[User, str, datetime], Depends(get_current_user_refresh)]
