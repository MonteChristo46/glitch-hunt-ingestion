from typing import Optional
from app.db.handlers.base import BaseHandler
from app.models.account import AccountCreate, AccountRead

class AccountHandler(BaseHandler):
    async def create(self, account: AccountCreate) -> AccountRead:
        query = """
            INSERT INTO accounts (name, is_active)
            VALUES ($1, $2)
            RETURNING id, name, is_active
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, account.name, account.is_active)
            return AccountRead(**dict(row))

    async def get_by_name(self, name: str) -> Optional[AccountRead]:
        query = "SELECT id, name, is_active FROM accounts WHERE name = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, name)
            if row:
                return AccountRead(**dict(row))
            return None
