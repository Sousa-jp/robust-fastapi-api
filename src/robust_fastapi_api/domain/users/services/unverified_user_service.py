from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from jwt import DecodeError, ExpiredSignatureError

from robust_fastapi_api.core.datetime import now
from robust_fastapi_api.core.email.email import EmailClient, EmailTemplate, get_email_client
from robust_fastapi_api.core.security.password import get_password_hash
from robust_fastapi_api.core.security.token import create_access_token, decode_token
from robust_fastapi_api.core.settings import settings

from ..models.unverified_user_model import UnverifiedUser
from ..models.user_model import User, UserOrigin
from ..repositories.unverified_user_repository import UnverifiedUserRepository, get_unverified_user_repository
from ..repositories.user_repository import UserRepository, get_user_repository
from ..schemas.models import (
    ActivateUserSuccessResponse,
    CreateUserPayload,
    SecurityMessageResponse,
    SecurityTokenErrorResponse,
)


class UnverifiedUserService:
    def __init__(
        self,
        unverified_user_repository: UnverifiedUserRepository,
        user_repository: UserRepository,
        email_client: EmailClient,
    ) -> None:
        self._unverified_user_repository = unverified_user_repository
        self._user_repository = user_repository
        self._email_client = email_client

    async def create_unverified_user(self, user_payload: CreateUserPayload) -> dict:
        existing_verified = await self._user_repository.find_by_email(user_payload.email)
        if existing_verified and existing_verified.origin == UserOrigin.MANUAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        unverified_user = await self._unverified_user_repository.find_by_email(user_payload.email)
        if unverified_user:
            if not self._can_send_activation_email(unverified_user):
                return SecurityMessageResponse().model_dump()
            unverified_user.first_name = user_payload.first_name
            unverified_user.last_name = user_payload.last_name
            unverified_user.password = get_password_hash(user_payload.password)
            unverified_user.activation_token_version += 1
            unverified_user.last_activation_sent_at = now()
            unverified_user = await self._unverified_user_repository.save(unverified_user)
        else:
            unverified_user = UnverifiedUser(
                first_name=user_payload.first_name,
                last_name=user_payload.last_name,
                password=get_password_hash(user_payload.password),
                email=user_payload.email,
                activation_token_version=1,
            )
            unverified_user = await self._unverified_user_repository.save(unverified_user)

        await self._send_activation_email(unverified_user)
        return SecurityMessageResponse().model_dump()

    @staticmethod
    def _can_send_activation_email(unverified_user: UnverifiedUser) -> bool:
        if unverified_user.last_activation_sent_at is None:
            return True
        return (now() - unverified_user.last_activation_sent_at) >= timedelta(minutes=10)

    async def _send_activation_email(self, unverified_user: UnverifiedUser) -> None:
        token_data = {
            "sub": unverified_user.email,
            "user_id": str(unverified_user.id),
            "token_type": "activation",
            "token_version": unverified_user.activation_token_version,
        }
        token, _ = create_access_token(token_data, expires_in_minutes=10)
        verify_url = f"{settings.frontend_url}/activate?token={token}"
        template = EmailTemplate(
            template_name="account_activation",
            subject="Account Activation",
            variables={"user_name": unverified_user.first_name, "verify_url": verify_url},
        )
        await self._email_client.send_email([unverified_user.email], template)

    async def activate_user(self, token: str) -> dict:
        payload = self._validate_activation_token(token)
        user = await self._user_repository.find_by_email(payload["sub"])
        self._is_already_verified(user)
        unverified_user = await self._validate_user_attempt(payload)
        await self._migrate_to_verified(user, unverified_user)
        return ActivateUserSuccessResponse().model_dump()

    @staticmethod
    def _validate_activation_token(token: str) -> dict:
        try:
            payload = decode_token(token, token_type="activation")
        except (DecodeError, ExpiredSignatureError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SecurityTokenErrorResponse().detail,
            ) from e

        email = payload.get("sub")
        token_type = payload.get("token_type", "")
        user_id = payload.get("user_id")
        token_version = payload.get("token_version")
        if token_type != "activation" or not user_id or not token_version or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SecurityTokenErrorResponse().detail,
            )
        return payload

    async def _validate_user_attempt(self, payload: dict) -> UnverifiedUser:
        user_id = UUID(str(payload["user_id"]))
        token_version = int(payload["token_version"])
        unverified_user = await self._unverified_user_repository.find_by_id(user_id)
        if not unverified_user or unverified_user.activation_token_version != token_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SecurityTokenErrorResponse().detail,
            )
        return unverified_user

    @staticmethod
    def _is_already_verified(user: Optional[User]) -> None:
        if user and user.origin == UserOrigin.MANUAL.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already verified")

    async def _migrate_to_verified(self, user: Optional[User], unverified_user: UnverifiedUser) -> None:
        if user:
            user.first_name = unverified_user.first_name
            user.last_name = unverified_user.last_name
            user.password = unverified_user.password
            user.origin = UserOrigin.MANUAL.value
        else:
            user = User(
                first_name=unverified_user.first_name,
                last_name=unverified_user.last_name,
                password=unverified_user.password,
                email=unverified_user.email,
                origin=UserOrigin.MANUAL.value,
            )
        await self._user_repository.save(user)
        await self._unverified_user_repository.delete(unverified_user)


def get_unverified_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    unverified_user_repository: UnverifiedUserRepository = Depends(get_unverified_user_repository),
    email_client: EmailClient = Depends(get_email_client),
) -> UnverifiedUserService:
    return UnverifiedUserService(
        unverified_user_repository=unverified_user_repository,
        user_repository=user_repository,
        email_client=email_client,
    )


UnverifiedUserServiceDep = Depends(get_unverified_user_service)
