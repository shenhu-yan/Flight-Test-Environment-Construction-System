from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flight Test Environment Construction System"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fltect"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "fltect"

    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
