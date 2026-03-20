from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from robust_fastapi_api.domain.auth.security import CurrentUser
from robust_fastapi_api.domain.users.schemas.models import (
    ActivateUserSuccessResponse,
    CreateUserPayload,
    SecurityMessageResponse,
    UserResponse,
)
from robust_fastapi_api.domain.users.services.unverified_user_service import (
    UnverifiedUserService,
    get_unverified_user_service,
)
from robust_fastapi_api.domain.users.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me", response_model=SecurityMessageResponse)
async def create_self_unverified_user(
    user_payload: CreateUserPayload,
    unverified_user_service: Annotated[
        UnverifiedUserService,
        Depends(get_unverified_user_service),
    ],
) -> SecurityMessageResponse:
    return await unverified_user_service.create_unverified_user(user_payload)


@router.post("/activate", response_model=ActivateUserSuccessResponse, status_code=201)
async def activate_unverified_user(
    token: Annotated[str, Query(..., description="Token to verify account")],
    unverified_user_service: Annotated[
        UnverifiedUserService,
        Depends(get_unverified_user_service),
    ],
) -> ActivateUserSuccessResponse:
    return await unverified_user_service.activate_user(token)


@router.get("/me", response_model=UserResponse)
async def get_user_me(
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.get_user_info(current_user)
