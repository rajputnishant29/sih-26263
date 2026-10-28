from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EDUTrace — APAAR ID-Based Student Data Management and Verification Platform"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://smartshutter:smartshutter_local_dev@localhost:5432/edutrace"

    HMAC_SECRET_KEY: str = "edutrace_sih2026_super_secure_identity_hmac_secret_key"
    JWT_SECRET_KEY: str = "edutrace_sih2026_super_secure_jwt_secret_key_access_token"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    ALLOW_DEMO_ROLE_SWITCHER: bool = True
    IS_SYNTHETIC_DATA: bool = True

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
