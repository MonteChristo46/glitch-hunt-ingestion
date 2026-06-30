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
        if isinstance(account_id, str):
            account_id = UUID(account_id)

        query = """
            WITH account_info AS (
                SELECT 
                    a.id as account_id, 
                    a.tier_id, 
                    st.inference_limit_monthly
                FROM accounts a
                JOIN subscription_tiers st ON a.tier_id = st.id
                WHERE a.id = $1
            ),
            current_usage AS (
                SELECT inference_count
                FROM account_usage_counters auc
                JOIN account_info ai ON auc.account_id = ai.account_id
                WHERE auc.period_start = date_trunc('month', CURRENT_TIMESTAMP)
            )
            SELECT 
                ai.inference_limit_monthly - COALESCE(cu.inference_count, 0) as remaining_quota
            FROM account_info ai
            LEFT JOIN current_usage cu ON true;
        """
        async with self.pool.acquire() as conn:
            remaining_quota = await conn.fetchval(query, account_id)
            return remaining_quota if remaining_quota is not None else 0

    async def increment_inference_count(self, account_id: Union[UUID, str]) -> None:
        """
        Increments the inference usage counter for the account's current billing period.
        Creates the period row if it doesn't exist yet.
        """
        if isinstance(account_id, str):
            account_id = UUID(account_id)

        query = """
            INSERT INTO account_usage_counters (account_id, period_start, period_end, inference_count)
            SELECT $1,
                   date_trunc('month', CURRENT_TIMESTAMP),
                   (date_trunc('month', CURRENT_TIMESTAMP) + INTERVAL '1 month'),
                   1
            ON CONFLICT (account_id, period_start) DO UPDATE
            SET inference_count = account_usage_counters.inference_count + 1;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, account_id)
