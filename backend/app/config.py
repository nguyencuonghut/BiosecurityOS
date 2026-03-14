from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "BIOSECURITY OS 2026"
    API_V1_PREFIX: str = "/api/v1"

    # ── Database
    DATABASE_URL: str = "postgresql+asyncpg://biosec:biosec_dev_2026@localhost:5432/biosecurity"

    # ── Redis
    REDIS_URL: str = "redis://:redis_dev@localhost:6379/0"

    # ── MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_dev"
    MINIO_SECRET_KEY: str = "minio_dev_2026"
    MINIO_BUCKET: str = "biosec-evidence"
    MINIO_USE_SSL: bool = False

    # ── JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
