from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from robust_fastapi_api.domain.auth.schemas.models import (
    AccessTokenResponse,
    LogoutResponse,
    OAuthPayload,
    PasswordResetConfirmPayload,
    PasswordResetRequestPayload,
    PasswordResetSuccessResponse,
    PasswordResetVerifyPayload,
    SecurityMessageResponse,
    ValidateResponse,
    VerificationCodeResponse,
)
from robust_fastapi_api.domain.auth.security import CurrentUser, CurrentUserRefresh
from robust_fastapi_api.domain.auth.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AccessTokenResponse)
async def login_with_email_password(
    login_schema: OAuthPayload,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    return await auth_service.login(login_schema)


@router.post("/validate", response_model=ValidateResponse)
async def validate_token(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ValidateResponse:
    return await auth_service.validate_token(current_user)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    current_user_info: CurrentUserRefresh,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    return await auth_service.refresh_token(current_user_info)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponse:
    return await auth_service.logout(current_user)


@router.post("/password-reset/request", response_model=SecurityMessageResponse)
async def request_password_reset(
    payload: PasswordResetRequestPayload,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SecurityMessageResponse:
    return await auth_service.request_password_reset(payload)


@router.post("/password-reset/verify", response_model=VerificationCodeResponse)
async def verify_reset_code(
    payload: PasswordResetVerifyPayload,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> VerificationCodeResponse:
    return await auth_service.verify_reset_code(payload)


@router.post("/password-reset/confirm", response_model=PasswordResetSuccessResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmPayload,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordResetSuccessResponse:
    return await auth_service.confirm_password_reset(payload)
