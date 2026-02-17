import time
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from prometheus_client import Histogram
from app.models.ingest import IngestRequest, IngestResponse, ConfirmRequest
from app.models.enums import IngestStatus, EventType
from app.models.image import ImageCreate
from app.redis.client import RedisClient, get_redis_client
from app.services.storage import StorageService, get_storage_service
from app.db.session import DatabaseManager, get_db
from app.db.handlers.devices import DeviceHandler
from app.db.handlers.images import ImageHandler

router = APIRouter()
logger = logging.getLogger(__name__)

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
    storage: StorageService = Depends(get_storage_service),
    db: DatabaseManager = Depends(get_db)
):
    device_handler = DeviceHandler(db.pool)
    
    # Verify Device Authorization
    logger.debug(f"Checking authorization for device: {request.device_id}")
    is_allowed = await device_handler.is_active(request.device_id)
    if not is_allowed:
        logger.warning(f"Unauthorized access attempt by device: {request.device_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device not authorized or inactive"
        )

    start_time = time.time()
    handshake_id = uuid4()
    
    # Generate Presigned URL
    try:
        upload_url, object_key, expires_at = storage.generate_presigned_url(request.filename, request.file_path_context)
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate upload URL")


    request.metadata['s3_key'] = object_key

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
    redis: RedisClient = Depends(get_redis_client),
    db: DatabaseManager = Depends(get_db)
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
    
    # If success, write to DB
    if request.status == IngestStatus.SUCCESS:
        image_handler = ImageHandler(db.pool)
        
        # Extract s3_key from metadata (where we stored it)
        metadata = handshake_data.get("metadata", {})
        s3_key = metadata.get("s3_key")
        
        if not s3_key:
            # Fallback if not found (shouldn't happen with new flow)
            logger.error(f"Missing s3_key for handshake {request.handshake_id}")
            # We might want to construct it or fail. 
            # For now, let's assume it's there or fail.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Integrity Error: s3_key missing")

        try:
            image_create = ImageCreate(
                device_id=handshake_data.get("device_id"),
                status=request.status.value,
                captured_at=handshake_data.get("timestamp"),
                image_path=s3_key,
                context=handshake_data.get("device_context", {}),
                route_key=None # You can add logic here to determine route key
            )
            await image_handler.create(image_create)
        except Exception as e:
            logger.error(f"Failed to record image in DB: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    # Push to Redis Stream only on success
    if request.status == IngestStatus.SUCCESS:
        await redis.push_event(request.handshake_id, request, handshake_data, event_type=EventType.FILE_UPLOADED)

    return {"status": "processed"}