import asyncpg
from app.config import settings

class DatabaseManager:
    """
    Manages the PostgreSQL connection pool.
    """
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def check_device_active(self, device_id: str) -> bool:
        """
        Checks if a device exists and is active.
        """
        if not self.pool:
            raise RuntimeError("Database connection not initialized")
            
        query = "SELECT 1 FROM devices WHERE device_id = $1 AND is_active = TRUE"
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, device_id)
            return result is not None

db_manager = DatabaseManager()

async def get_db() -> DatabaseManager:
    return db_manager
