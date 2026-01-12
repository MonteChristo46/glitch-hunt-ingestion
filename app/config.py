import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MinIO Configurations
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "s3.my-basement.cloud")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "pusteblume123!")
    MINIO_REGION: str = os.getenv("MINIO_REGION", "eu-central-1")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "glitch-hunt-dev")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_STREAM_KEY: str = "ingest:events"
    
    # Event Configuration
    EVENT_VERSION: str = os.getenv("EVENT_VERSION", "1.0")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
