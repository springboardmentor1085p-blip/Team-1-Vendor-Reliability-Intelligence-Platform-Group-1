import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://vendoriq_user:vendoriq_secure_pass_2026@db:5432/vendoriq_db"
    JWT_SECRET: str = "supersecretjwtkeythatisextremelysecureandlongenoughfor2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENV_MODE: str = "development"
    FRONTEND_URL: str = "http://localhost:4200"
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost:80,http://localhost"

    # SMTP Settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@vendoriq.com"
    SMTP_USE_TLS: bool = True

    # SMS Settings
    SMS_PROVIDER: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # File Upload Settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Allow custom .env reading if it exists
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
