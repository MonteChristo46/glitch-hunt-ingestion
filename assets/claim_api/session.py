import asyncpg
import redis.asyncio as redis
from app.core.config import settings
from app.db.handlers.users import UserHandler
from app.db.handlers.devices import DeviceHandler
from app.db.handlers.accounts import AccountHandler


class DatabaseManager:
    """
    Central entry point for Database access.
    Manages the connection pool and provides access to domain handlers.
    """

    def __init__(self):
        self.pool: asyncpg.Pool | None = None
        self.redis: redis.Redis | None = None
        self.users: UserHandler | None = None
        self.devices: DeviceHandler | None = None
        self.accounts: AccountHandler | None = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            # Initialize Handlers
            self.users = UserHandler(self.pool)
            self.devices = DeviceHandler(self.pool)
            self.accounts = AccountHandler(self.pool)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
        if self.redis:
            await self.redis.close()
            self.redis = None


db_manager = DatabaseManager()
