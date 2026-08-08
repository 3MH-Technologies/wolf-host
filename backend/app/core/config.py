from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Wolf Host"
    ENVIRONMENT: str = "production"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str
    REDIS_URL: str

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    DOCKER_NETWORK_NAME: str = "wolfhost_bots_net"
    DOCKER_IMAGE_PYTHON: str = "python:3.12-slim"
    BOTS_STORAGE_PATH: str = "/var/wolfhost/bots"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: str = "live"

    USDT_TRC20_ADDRESS: str = ""
    USDT_BEP20_ADDRESS: str = ""
    TRONGRID_API_KEY: str = ""
    BSCSCAN_API_KEY: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@wolfhost.local"

    MAX_UPLOAD_SIZE_MB: int = 200

    RATE_LIMIT_PER_MINUTE: int = 60


settings = Settings()
