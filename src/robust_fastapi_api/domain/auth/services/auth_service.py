from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status

from robust_fastapi_api.core.datetime import now
from robust_fastapi_api.core.email.email import EmailClient, EmailTemplate, get_email_client
from robust_fastapi_api.core.security.password import get_password_hash, verify_password
from robust_fastapi_api.core.security.token import create_access_token
from robust_fastapi_api.core.settings import settings
from robust_fastapi_api.domain.users.models.user_model import User
from robust_fastapi_api.domain.users.repositories.user_repository import UserRepository, get_user_repository

from ..schemas.models import (
    AccessTokenResponse,
    LogoutResponse,
    PasswordResetConfirmPayload,
    PasswordResetRequestPayload,
    PasswordResetSuccessResponse,
    PasswordResetVerifyPayload,
    SecurityMessageResponse,
    ValidateResponse,
    VerificationCodeResponse,
)


@dataclass
class PasswordResetCode:
    email: str
    code: str
    created_at: datetime
    expires_at: datetime
    last_attempt: Optional[datetime] = None


password_reset_codes: dict[str, PasswordResetCode] = {}

DEFAULT_SECURITY_MESSAGE = SecurityMessageResponse()


class AuthService:
    def __init__(self, user_repository: UserRepository, email_client: EmailClient) -> None:
        self._user_repository = user_repository
        self._email_client = email_client

    async def _authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self._user_repository.find_by_email(email)
        if not user or not user.password or not verify_password(password, user.password):
            return None
        return user

    async def login(self, login_schema) -> AccessTokenResponse:
        user = await self._authenticate_user(login_schema.username, login_schema.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.access_token_version += 1
        user.refresh_token_version += 1
        await self._user_repository.save(user)

        access_token, access_expires_at = create_access_token(
            data={"sub": login_schema.username, "token_type": "access", "version": user.access_token_version},
            expires_in_minutes=settings.security.access_token_expire_minutes,
        )

        refresh_token, refresh_expires_at = create_access_token(
            data={"sub": login_schema.username, "token_type": "refresh", "version": user.refresh_token_version},
            expires_in_minutes=settings.security.refresh_token_expire_days * 24 * 60,
        )

        return AccessTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at,
        )

    async def refresh_token(self, current_user_info) -> AccessTokenResponse:
        current_user, rfsh_token, expires_at_refresh_token = current_user_info
        current_user.access_token_version += 1
        await self._user_repository.save(current_user)

        token, expires_at_token = create_access_token(
            data={"sub": current_user.email, "token_type": "access", "version": current_user.access_token_version},
            expires_in_minutes=settings.security.access_token_expire_minutes,
        )

        return AccessTokenResponse(
            access_token=token,
            refresh_token=rfsh_token,
            token_type="bearer",
            access_token_expires_at=expires_at_token,
            refresh_token_expires_at=expires_at_refresh_token,
        )

    async def logout(self, current_user: User) -> LogoutResponse:
        current_user.access_token_version += 1
        current_user.refresh_token_version += 1
        await self._user_repository.save(current_user)
        return LogoutResponse()

    @staticmethod
    def _generate_reset_code() -> str:
        letters = string.ascii_uppercase
        digits = string.digits
        code = random.sample(letters + digits, 4)
        code.append(random.choice(letters))
        code.append(random.choice(digits))
        random.shuffle(code)
        return "".join(code)

    @staticmethod
    def _get_reset_code(email: str) -> Optional[PasswordResetCode]:
        return password_reset_codes.get(email)

    @staticmethod
    def _save_reset_code(email: str, code: str) -> None:
        now_dt = now()
        password_reset_codes[email] = PasswordResetCode(
            email=email,
            code=code,
            created_at=now_dt,
            expires_at=now_dt + timedelta(minutes=10),
            last_attempt=now_dt,
        )

    async def request_password_reset(self, payload: PasswordResetRequestPayload) -> dict:
        existing_code = self._get_reset_code(payload.email)
        should_process = True
        if existing_code and existing_code.last_attempt:
            time_since_last = now() - existing_code.last_attempt
            should_process = time_since_last >= timedelta(minutes=1)

        if should_process:
            user = await self._user_repository.find_by_email(payload.email)
            if user:
                code = self._generate_reset_code()
                self._save_reset_code(payload.email, code)
                template = self._create_password_reset_template(code)
                await self._email_client.send_email([payload.email], template)

        return DEFAULT_SECURITY_MESSAGE

    @staticmethod
    def _create_password_reset_template(code: str) -> EmailTemplate:
        return EmailTemplate(
            template_name="password_reset",
            subject="Password Recovery",
            variables={"code": code},
        )

    async def verify_reset_code(self, payload: PasswordResetVerifyPayload) -> VerificationCodeResponse:
        code_data = self._get_reset_code(payload.email)
        if not code_data or code_data.code != payload.code or now() > code_data.expires_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

        code_data.last_attempt = now()
        return VerificationCodeResponse()

    async def _validate_reset_code(self, email: str, code: str) -> None:
        try:
            await self.verify_reset_code(PasswordResetVerifyPayload(email=email, code=code))
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    @staticmethod
    def _validate_new_password(user: User, new_password: str) -> None:
        if not user.password or verify_password(new_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="New password must be different from the current one",
            )

    async def confirm_password_reset(self, payload: PasswordResetConfirmPayload) -> PasswordResetSuccessResponse:
        user = await self._user_repository.find_by_email(payload.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await self._validate_reset_code(payload.email, payload.code)
        self._validate_new_password(user, payload.new_password)

        user.password = get_password_hash(payload.new_password)
        user.access_token_version += 1
        user.refresh_token_version += 1
        await self._user_repository.save(user)

        password_reset_codes.pop(payload.email, None)
        return PasswordResetSuccessResponse()

    @staticmethod
    async def validate_token(current_user: User) -> ValidateResponse:
        return ValidateResponse(user_id=current_user.id, token_valid=True)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    email_client: EmailClient = Depends(get_email_client),
) -> AuthService:
    return AuthService(user_repository=user_repository, email_client=email_client)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
