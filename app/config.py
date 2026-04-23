import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MinIO Configurations
    S3_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "blob.my-basement.cloud")
    S3_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin-de1b7035")
    S3_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "4MoXVEV2WHEpb90hfWpmGIdafqFH95pC")
    S3_REGION: str = os.getenv("MINIO_REGION", "eu-central-1")
    S3_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "glitch-hunt-dev")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_CACHE_DB: int = int(os.getenv("REDIS_CACHE_DB", 2))
    REDIS_EVENTS_DB: int = int(os.getenv("REDIS_EVENTS_DB", 0))
    REDIS_STREAM_KEY: str = "ingest:events"
    REDIS_STREAM_MAXLEN: int = int(os.getenv("REDIS_STREAM_MAXLEN", 1000000))
    REDIS_QUOTA_TTL: int = int(os.getenv("REDIS_QUOTA_TTL", 60))

    # Postgres Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secret_password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ingest_db")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Event Configuration
    EVENT_VERSION: str = os.getenv("EVENT_VERSION", "1.0")

    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
