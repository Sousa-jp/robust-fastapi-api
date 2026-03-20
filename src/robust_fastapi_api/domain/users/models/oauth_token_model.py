from __future__ import annotations

import base64
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from robust_fastapi_api.core.datetime import now
from robust_fastapi_api.core.db.base import Base
from robust_fastapi_api.core.settings import settings


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="unique_user_provider"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    _access_token: Mapped[str] = mapped_column("access_token", String(512), nullable=False)
    _refresh_token: Mapped[Optional[str]] = mapped_column("refresh_token", String(512), nullable=True)
    access_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    def _get_cipher(self) -> Fernet:
        if not hasattr(self, "_cipher"):
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"oauth_token_salt",
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.security.secret_key.encode()))
            self._cipher = Fernet(key)
        return self._cipher

    @property
    def access_token(self) -> str:
        try:
            cipher = self._get_cipher()
            return cipher.decrypt(self._access_token.encode()).decode()
        except Exception:
            return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        if value:
            cipher = self._get_cipher()
            self._access_token = cipher.encrypt(value.encode()).decode()
        else:
            self._access_token = value

    @property
    def refresh_token(self) -> Optional[str]:
        if self._refresh_token is None:
            return None
        try:
            cipher = self._get_cipher()
            return cipher.decrypt(self._refresh_token.encode()).decode()
        except Exception:
            return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        if value:
            cipher = self._get_cipher()
            self._refresh_token = cipher.encrypt(value.encode()).decode()
        else:
            self._refresh_token = value
