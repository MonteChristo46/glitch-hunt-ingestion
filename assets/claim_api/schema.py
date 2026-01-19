import asyncpg
from app.db.handlers.accounts import AccountHandler
from app.models.account import AccountCreate
from app.core.config import settings

class SchemaManager:
    """
    Responsible for checking database schema state and initializing tables/defaults.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    async def ensure_schema(self):
        """
        Idempotently creates tables and default data.
        """
        async with self.db.pool.acquire() as conn:
            # 1. Accounts Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Users Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    external_auth_id TEXT UNIQUE NOT NULL,
                    account_id UUID REFERENCES accounts(id) NOT NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Devices Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id VARCHAR(64) PRIMARY KEY,
                    account_id UUID REFERENCES accounts(id) NOT NULL,
                    auth_token_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

        # 4. Ensure System Account
        # Using the handler provides a nice abstraction, ensuring we use our own business logic layers where possible.
        # However, we need to check if it exists first to be idempotent.
        existing = await self.db.accounts.get_by_name(settings.SYSTEM_ACCOUNT_NAME)
        if not existing:
            print(f"Initializing default '{settings.SYSTEM_ACCOUNT_NAME}'...")
            await self.db.accounts.create(AccountCreate(name=settings.SYSTEM_ACCOUNT_NAME))
        else:
            print(f"'{settings.SYSTEM_ACCOUNT_NAME}' already exists.")
