
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.db.handlers.base import BaseHandler
from app.models.device import DeviceCreate, DeviceRead

class DeviceHandler(BaseHandler):
    async def register_device(self, device_id: str, account_id: UUID, auth_token_hash: str) -> DeviceRead:
        query = """
            INSERT INTO devices (device_id, account_id, auth_token_hash, is_active, metadata)
            VALUES ($1, $2, $3, TRUE, '{}'::jsonb)
            ON CONFLICT (device_id) DO UPDATE
            SET account_id = EXCLUDED.account_id,
                auth_token_hash = EXCLUDED.auth_token_hash,
                is_active = TRUE
            RETURNING device_id, account_id, is_active, metadata
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, device_id, account_id, auth_token_hash)
            return DeviceRead(**dict(row))

    async def get_all_by_account(self, account_id: UUID, is_active: Optional[bool] = None) -> List[DeviceRead]:
        query = "SELECT device_id, account_id, is_active, metadata FROM devices WHERE account_id = $1"
        args = [account_id]
        
        if is_active is not None:
            query += " AND is_active = $2"
            args.append(is_active)
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [DeviceRead(
                device_id=row['device_id'],
                account_id=row['account_id'],
                is_active=row['is_active'],
                metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
            ) for row in rows]

    async def create(self, device: DeviceCreate) -> DeviceRead:
        query = """
            INSERT INTO devices (device_id, account_id, auth_token_hash, is_active, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING device_id, account_id, is_active, metadata
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                device.device_id,
                device.account_id,
                device.auth_token_hash,
                device.is_active,
                json.dumps(device.metadata)
            )
            return DeviceRead(**dict(row))

    async def get_by_id(self, device_id: str) -> Optional[DeviceRead]:
        query = "SELECT device_id, account_id, is_active, metadata FROM devices WHERE device_id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, device_id)
            if row:
                return DeviceRead(
                    device_id=row['device_id'],
                    account_id=row['account_id'],
                    is_active=row['is_active'],
                    metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                )
            return None
    
    async def is_active(self, device_id: str) -> bool:
        query = "SELECT 1 FROM devices WHERE device_id = $1 AND is_active = TRUE"
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, device_id)
            return result is not None

    async def update_metadata(self, device_id: str, metadata: Dict[str, Any]) -> Optional[DeviceRead]:
        query = """
            UPDATE devices
            SET metadata = $2
            WHERE device_id = $1
            RETURNING device_id, account_id, is_active, metadata
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, device_id, json.dumps(metadata))
            if row:
                return DeviceRead(
                    device_id=row['device_id'],
                    account_id=row['account_id'],
                    is_active=row['is_active'],
                    metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                )
            return None
