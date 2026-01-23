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
            "file_path_context": original_payload.get("file_path_context", []),
            "device_context": original_payload.get("device_context", {})
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
        # Generate a 6-character alphanumeric code in XXX-XXX format
        chars = string.ascii_uppercase + string.digits
        part1 = ''.join(secrets.choice(chars) for _ in range(3))
        part2 = ''.join(secrets.choice(chars) for _ in range(3))
        code = f"{part1}-{part2}"
        
        # Store code -> device mapping with status
        # This matches the schema expected by the external Claim API
        key = f"pairing:{code}"
        data = {
            "device_id": device_id,
            "status": PairingStatus.WAITING.value
        }
        await self.redis.setex(key, timedelta(minutes=ttl_minutes), json.dumps(data))
        
        return code

    async def get_pairing_status(self, code: str, device_id: str) -> dict | None:
        key = f"pairing:{code}"
        data = await self.redis.get(key)
        
        if not data:
            return None
            
        try:
            parsed = json.loads(data)
            # Security check: Ensure the code actually belongs to this device
            if parsed.get("device_id") != device_id:
                return None
            return parsed
        except json.JSONDecodeError:
            return None

redis_client = RedisClient()

async def get_redis_client() -> RedisClient:
    return redis_client
