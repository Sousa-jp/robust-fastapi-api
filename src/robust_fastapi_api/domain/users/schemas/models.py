from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from robust_fastapi_api.core.settings import settings

from .fields import NameField, PasswordField


class CreateUserPayload(BaseModel):
    first_name: NameField
    last_name: NameField
    email: EmailStr = Field(
        ...,
        description=(
            f"Email must belong to one of the domains: {', '.join(settings.account_domain)}"
            if "*" not in settings.account_domain
            else "Email from any domain is allowed"
        ),
    )
    password: PasswordField

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        if "*" not in settings.account_domain:
            email_domain = v.rsplit("@", maxsplit=1)[-1]
            if email_domain not in settings.account_domain:
                raise ValueError(f"Email must belong to one of the domains: {', '.join(settings.account_domain)}")
        return v


class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityMessageResponse(BaseModel):
    detail: str = (
        "An email has been sent to your email with instructions to activate your account. "
        "If you do not receive the email within a few minutes, please try again."
    )


class SecurityTokenErrorResponse(BaseModel):
    detail: str = "Invalid or expired token"


class ActivateUserSuccessResponse(BaseModel):
    detail: str = "Account successfully activated"
