from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.pairing import (
    PairingRequest, 
    PairingResponse, 
    PairingStatusResponse
)
from app.models.enums import PairingStatus
from app.redis.client import RedisClient, get_redis_client

router = APIRouter()

@router.post("/request", response_model=PairingResponse)
async def request_pairing_code(
    request: PairingRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    ttl_minutes = 15
    code = await redis.create_pairing_code(request.device_id, ttl_minutes=ttl_minutes)
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    
    return PairingResponse(
        code=code,
        expires_at=expires_at
    )

@router.get("/status", response_model=PairingStatusResponse)
async def check_pairing_status(
    device_id: str = Query(..., title="Device Id"),
    code: str = Query(..., title="Code"),
    redis: RedisClient = Depends(get_redis_client)
):
    # Check status by code (verifying device_id matches)
    pairing_data = await redis.get_pairing_status(code, device_id)
    
    if not pairing_data:
        # If no data found, it's expired or invalid
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pairing session expired or invalid"
        )
    
    # Defaults to WAITING if status field is missing (backward compatibility)
    current_status = pairing_data.get("status", PairingStatus.WAITING.value)
    
    return PairingStatusResponse(
        status=PairingStatus(current_status),
        apikey=pairing_data.get("apikey")
    )
