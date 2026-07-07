from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # S3 / RustFS Configurations
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "eu-central-1"
    S3_BUCKET_NAME: str = "glitch-hunt-dev"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_CACHE_DB: int = 2
    REDIS_EVENTS_DB: int = 0
    REDIS_STREAM_KEY: str = "ingest:events"
    REDIS_STREAM_MAXLEN: int = 1000000
    REDIS_QUOTA_TTL: int = 60

    # Postgres Configuration
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "secret_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ingest_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Event Configuration
    EVENT_VERSION: str = "1.0"

    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
