from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator

from ...users.schemas.fields import PasswordField
from .fields import VerificationCodeField


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime


OAuthPayload = Annotated[OAuth2PasswordRequestForm, Depends()]


class PasswordResetRequestPayload(BaseModel):
    email: EmailStr


class PasswordResetVerifyPayload(BaseModel):
    email: EmailStr
    code: VerificationCodeField


class PasswordResetConfirmPayload(BaseModel):
    email: EmailStr
    code: VerificationCodeField
    new_password: PasswordField
    confirm_password: PasswordField

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class SecurityMessageResponse(BaseModel):
    message: str = (
        "If your email is registered, you will receive a verification code. "
        "If you haven't requested it in the last minute, please wait up to one minute to receive a new code."
    )


class VerificationCodeResponse(BaseModel):
    message: str = "Code is valid"


class PasswordResetSuccessResponse(BaseModel):
    message: str = "Password has been reset successfully"


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class ValidateResponse(BaseModel):
    user_id: UUID
    token_valid: bool
