from uuid import UUID
from typing import Optional, Union
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

    async def get_remaining_quota(self, account_id: Union[UUID, str]) -> int:
        """
        Calculates the remaining quota for an account based on their subscription tier
        and current usage period.
        """
        # Ensure account_id is a UUID object for asyncpg
        if isinstance(account_id, str):
            account_id = UUID(account_id)

        query = """
            WITH account_info AS (
                SELECT 
                    a.id as account_id, 
                    a.tier_id, 
                    COALESCE(a.current_period_end, date_trunc('month', CURRENT_TIMESTAMP) + interval '1 month') as period_end, 
                    (COALESCE(a.current_period_end, date_trunc('month', CURRENT_TIMESTAMP) + interval '1 month') - interval '1 month') as period_start,
                    st.inference_limit_monthly
                FROM accounts a
                JOIN subscription_tiers st ON a.tier_id = st.id
                WHERE a.id = $1
            ),
            current_usage AS (
                SELECT inference_count
                FROM account_usage_counters auc
                JOIN account_info ai ON auc.account_id = ai.account_id AND auc.period_start = ai.period_start
            )
            SELECT 
                ai.inference_limit_monthly - COALESCE(cu.inference_count, 0) as remaining_quota
            FROM account_info ai
            LEFT JOIN current_usage cu ON true;
        """
        async with self.pool.acquire() as conn:
            remaining_quota = await conn.fetchval(query, account_id)
            return remaining_quota if remaining_quota is not None else 0
