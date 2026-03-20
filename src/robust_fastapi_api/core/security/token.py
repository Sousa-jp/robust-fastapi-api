from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol

from jwt import DecodeError, ExpiredSignatureError
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode

from ..datetime import now
from ..settings import settings


class UserRepositoryProtocol(Protocol):
    async def find_by_email(self, email: str) -> Any: ...


def create_access_token(
    data: dict[str, Any],
    *,
    expires_in_minutes: float,
) -> tuple[str, datetime]:
    to_encode = data.copy()
    expire = now() + timedelta(minutes=expires_in_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt_encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)
    return encoded_jwt, expire


def decode_token(
    token: str,
    *,
    token_type: str,
) -> dict[str, Any]:
    payload = jwt_decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
    )
    if payload.get("token_type") != token_type:
        raise ValueError("invalid_token_type")
    return payload


async def validate_access_token(
    token: str,
    *,
    token_type: str,
    user_repository: UserRepositoryProtocol,
) -> tuple[Any, str, datetime]:
    try:
        payload = jwt_decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
    except (DecodeError, ExpiredSignatureError) as e:
        raise ValueError(str(e)) from e

    user = await user_repository.find_by_email(payload.get("sub", ""))
    version_ok = True
    if token_type == "access":
        version_ok = int(payload.get("version", 0)) == getattr(user, "access_token_version", -1) if user else False
    if token_type == "refresh":
        version_ok = True
        if user is not None:
            version_ok = int(payload.get("version", 0)) == getattr(user, "refresh_token_version", -1)

    if not user or payload.get("token_type") != token_type or not version_ok:
        raise ValueError("invalid_credentials")

    exp_ts = payload.get("exp")
    if isinstance(exp_ts, (int, float)):
        expires_at = datetime.fromtimestamp(exp_ts)
    else:
        try:
            expires_at = datetime.fromtimestamp(exp_ts.timestamp())
        except Exception:
            expires_at = now()

    return user, token, expires_at
