import json
import secrets
import string
from uuid import UUID
from datetime import timedelta
import redis.asyncio as redis
from app.config import settings
from app.models.schemas import IngestRequest, ConfirmRequest, EventType, PairingStatus

class RedisClient:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def close(self):
        await self.redis.close()

    async def cache_handshake(self, handshake_id: UUID, payload: IngestRequest, ttl_minutes: int = 30, server_start_time: float | None = None):
        key = f"handshake:{handshake_id}"
        # Serialize datetime objects to string for JSON serialization
        data = payload.model_dump(mode='json')
        if server_start_time is not None:
            data['_server_start_time'] = server_start_time
        await self.redis.setex(key, timedelta(minutes=ttl_minutes), json.dumps(data))

    async def get_handshake(self, handshake_id: UUID) -> dict | None:
        key = f"handshake:{handshake_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def push_event(self, handshake_id: UUID, confirm_payload: ConfirmRequest, original_payload: dict):
        """
        Pushes the completed event to the Redis Stream.
        Follows a structured Envelope/Payload pattern.
        Envelope: event_type, version, handshake_id
        Payload: JSON string of the actual data
        """
        # Construct the inner payload
        payload_data = {
            "status": confirm_payload.status.value,
            "error_message": confirm_payload.error_message,
            "device_id": original_payload.get("device_id"),
            "filename": original_payload.get("filename"),
            "file_size_bytes": original_payload.get("file_size_bytes"),
            "sha256_checksum": original_payload.get("sha256_checksum"),
            "timestamp": original_payload.get("timestamp"),
            "metadata": original_payload.get("metadata", {}),
            "context": original_payload.get("context", [])
        }

        # Construct the Redis Stream entry (Envelope)
        event_data = {
            "event_type": EventType.FILE_UPLOADED.value,
            "version": settings.EVENT_VERSION,
            "handshake_id": str(handshake_id),
            "payload": json.dumps(payload_data)
        }
        
        await self.redis.xadd(settings.REDIS_STREAM_KEY, event_data)

    async def create_pairing_code(self, device_id: str, ttl_minutes: int = 15) -> int:
        # Generate a 6-character alphanumeric code
        chars = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(chars) for _ in range(6))
        
        # Store code -> device mapping
        code_key = f"pairing:code:{code}"
        await self.redis.setex(code_key, timedelta(minutes=ttl_minutes), device_id)
        
        # Initialize device status
        device_key = f"pairing:device:{device_id}"
        initial_status = {
            "status": PairingStatus.WAITING.value,
            "apikey": None
        }
        # Status TTL should match or slightly exceed code TTL to allow for polling
        await self.redis.setex(device_key, timedelta(minutes=ttl_minutes), json.dumps(initial_status))
        
        return code

    async def get_pairing_status(self, device_id: str) -> dict | None:
        key = f"pairing:device:{device_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def claim_device(self, code: str) -> dict | None:
        code_key = f"pairing:code:{code}"
        device_id = await self.redis.get(code_key)
        
        if not device_id:
            return None
            
        # Generate API Key
        api_key = secrets.token_urlsafe(32)
        
        # Update device status
        device_key = f"pairing:device:{device_id}"
        status_data = {
            "status": PairingStatus.CLAIMED.value,
            "apikey": api_key
        }
        # Extend TTL for the claimed status so the device has time to pick it up
        await self.redis.setex(device_key, timedelta(minutes=30), json.dumps(status_data))
        
        # Remove the code so it can't be used again
        await self.redis.delete(code_key)
        
        return {"device_id": device_id, "apikey": api_key}

redis_client = RedisClient()

async def get_redis_client() -> RedisClient:
    return redis_client
