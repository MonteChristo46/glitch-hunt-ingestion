import time
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from prometheus_client import Histogram
from app.models.schemas import IngestRequest, IngestResponse, ConfirmRequest, IngestStatus
from app.redis.client import RedisClient, get_redis_client
from app.services.storage import StorageService, get_storage_service

router = APIRouter()

# Metrics
INGESTION_DURATION = Histogram(
    "glitch_hunt_ingestion_duration_seconds",
    "Time from handshake request to confirmation",
    ["status"]
)

@router.post("/request", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_request(
    request: IngestRequest,
    redis: RedisClient = Depends(get_redis_client),
    storage: StorageService = Depends(get_storage_service)
):
    start_time = time.time()
    handshake_id = uuid4()
    
    # Generate Presigned URL
    try:
        upload_url, expires_at = storage.generate_presigned_url(request.filename, request.context)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate upload URL")

    # Persist to Redis Cache
    await redis.cache_handshake(handshake_id, request, server_start_time=start_time)

    return IngestResponse(
        handshake_id=handshake_id,
        upload_url=upload_url,
        expires_at=expires_at
    )

@router.post("/confirm", status_code=status.HTTP_200_OK)
async def ingest_confirm(
    request: ConfirmRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    # Retrieve handshake data
    handshake_data = await redis.get_handshake(request.handshake_id)
    
    if not handshake_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Handshake not found or expired"
        )

    # Calculate and record ingestion duration
    start_time = handshake_data.get("_server_start_time")
    if start_time:
        duration = time.time() - start_time
        INGESTION_DURATION.labels(status=request.status.value).observe(duration)

    # Push to Redis Stream
    await redis.push_event(request.handshake_id, request, handshake_data)

    return {"status": "processed"}
