from __future__ import annotations

import re
from typing import Annotated

from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError


def password_validator(value: str) -> str:
    pattern = r"^(?=.*[A-Za-z])(?=.*\\d)(?=.*[@$!%*#?&])[A-Za-z\\d@$!%*#?&]{8,}$"
    if not re.match(pattern, value):
        raise PydanticCustomError(
            "password_validation",
            "Password must contain at least 8 characters, including letters, numbers and special characters",
        )
    return value


PasswordField = Annotated[
    str,
    Field(
        description="Password must contain at least 8 characters, including letters, numbers and special characters",
    ),
    BeforeValidator(password_validator),
]


NameField = Annotated[
    str,
    Field(min_length=2, max_length=50, description="Name must be between 2 and 50 characters long"),
]
