from typing import List

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


class Settings(HeadSettings):
    app: AppSettings
    logging: LoggingSettings
    cors: CORSSettings
    database: DatabaseSettings
    redis: RedisSettings
