from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HeadSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


class AppSettings(HeadSettings):
    name: str
    version: str
    description: str
    debug: bool
    timezone: str = "UTC"


class LoggingSettings(HeadSettings):
    level: str
    sensitive_keys: List[str]
    ignore_paths: List[str]


class CORSSettings(HeadSettings):
    allow_origins: str
    allow_credentials: bool
    allow_methods: str
    allow_headers: str


class DatabaseSettings(HeadSettings):
    url: str


class RedisSettings(HeadSettings):
    url: str


class SecuritySettings(HeadSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: float
    refresh_token_expire_days: int
    session_https_only: bool = False


class EmailSettings(HeadSettings):
    email_host: str
    email_port: int
    email_username: str
    email_password: str
    email_from: str
    from_name: str
    use_tls: bool
    use_ssl: bool
    suppress_send: bool = False


class OAuthSettings(HeadSettings):
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_tenant_id: Optional[str] = None


class Settings(HeadSettings):
    app: AppSettings
    logging: LoggingSettings
    cors: CORSSettings
    database: DatabaseSettings
    redis: RedisSettings
    security: SecuritySettings
    email: EmailSettings
    oauth: OAuthSettings
    account_domain: List[str] = ["*"]
    frontend_url: str = "http://localhost:3000"
    dns_on: bool = False

    @field_validator("account_domain", mode="before")
    @classmethod
    def parse_account_domain(cls, v):
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [domain.strip() for domain in v.split(";") if domain.strip()]
        return v
