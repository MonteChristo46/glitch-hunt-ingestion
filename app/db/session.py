import asyncpg
from app.config import settings

class DatabaseManager:
    """
    Manages the PostgreSQL connection pool.
    """
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Database connection not initialized")
        return self._pool

db_manager = DatabaseManager()

async def get_db() -> DatabaseManager:
    return db_manager