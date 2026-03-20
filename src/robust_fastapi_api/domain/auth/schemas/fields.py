from __future__ import annotations

import re
from typing import Annotated

from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError


def verification_code_validator(value: str) -> str:
    pattern = r"^(?=.*[A-Z])(?=.*\\d)[A-Z0-9]{6}$"
    if not re.match(pattern, value):
        raise PydanticCustomError(
            "verification_code_validation",
            (
                "Verification code must be exactly 6 characters long, contain only "
                "uppercase letters and numbers, and have at least one letter and one "
                "number"
            ),
        )
    return value


VerificationCodeField = Annotated[
    str,
    Field(description="Verification code must be exactly 6 characters long"),
    BeforeValidator(verification_code_validator),
]
