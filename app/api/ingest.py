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
from app.db.handlers.accounts import AccountHandler

router = APIRouter()
logger = logging.getLogger(__name__)

async def verify_quota(
    request: IngestRequest,
    redis: RedisClient = Depends(get_redis_client),
    db: DatabaseManager = Depends(get_db)
):
    """
    Gateway Dependency: Verifies device authorization and account quota.
    Implements Lazy Load from Postgres to Redis DB 1 if quota key is missing.
    """
    device_handler = DeviceHandler(db.pool)
    device = await device_handler.get_by_id(request.device_id)

    if not device or not device.is_active:
        logger.warning(f"Unauthorized access attempt by device: {request.device_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device not authorized or inactive"
        )

    account_id = str(device.account_id)
    
    # 1. Check Redis DB 1 (Quota Cache)
    remaining_quota = await redis.get_quota(account_id)
    
    if remaining_quota is None:
        # 2. Lazy Load: Not in Redis, fetch from Postgres
        account_handler = AccountHandler(db.pool)
        remaining_quota = await account_handler.get_remaining_quota(account_id)
        
        # 3. Re-hydrate Redis
        await redis.set_quota(account_id, remaining_quota)
        logger.info(f"Quota Lazy Load: Hydrated {account_id} with {remaining_quota}")

    # 4. Validate Quota
    if remaining_quota <= 0:
        logger.warning(f"Quota Exceeded for account: {account_id}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Quota Exceeded"
        )

    return device

# Metrics
INGESTION_DURATION = Histogram(
    "glitch_hunt_ingestion_duration_seconds",
    "Time from handshake request to confirmation (Latency to Que)",
    ["status"]
)


@router.post("/request", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_request(
    request: IngestRequest,
    device = Depends(verify_quota),
    redis: RedisClient = Depends(get_redis_client),
    storage: StorageService = Depends(get_storage_service)
):
    start_time = time.time()
    handshake_id = uuid4()
    
    # Generate Presigned URL
    try:
        upload_url, object_key, expires_at = storage.generate_presigned_url(
            filename=request.filename, 
            file_path_context=request.file_path_context,
            account_id=str(device.account_id),
            device_id=request.device_id
        )
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate upload URL")


    request.metadata['s3_key'] = object_key

    # Persist to Redis Cache
    await redis.cache_handshake(
        handshake_id, 
        request, 
        server_start_time=start_time, 
        account_id=str(device.account_id)
    )

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

    start_time = handshake_data.get("_server_start_time")

    # If success, write to DB
    if request.status == IngestStatus.INGESTED:
        image_handler = ImageHandler(db.pool)
        
        metadata = handshake_data.get("metadata", {})
        s3_key = metadata.get("s3_key")
        
        if not s3_key:
            logger.error(f"Missing s3_key for handshake {request.handshake_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Integrity Error: s3_key missing")

        try:
            fpc = handshake_data.get("file_path_context", [])
            route_key = ".".join(str(x) for x in fpc) if fpc else None

            ctx = handshake_data.get("device_context", {})
            if fpc:
                ctx["file_path_context"] = fpc

            image_create = ImageCreate(
                id=request.handshake_id,
                device_id=handshake_data.get("device_id"),
                status=request.status.value,
                captured_at=handshake_data.get("timestamp"),
                image_path=s3_key,
                context=ctx,
                route_key=route_key
            )
            await image_handler.create(image_create)
        except Exception as e:
            logger.error(f"Failed to record image in DB: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    # Push to Redis Stream
    try:
        await redis.push_event(request.handshake_id, request, handshake_data)
        logger.info(f"Published event for handshake {request.handshake_id}")
    except Exception as e:
        logger.error(f"Failed to publish event for handshake {request.handshake_id}: {e}")
        # Decide on error handling: fail the request or just log?
        # For now, we'll log and proceed.
        
    # Calculate and record total ingestion duration
    if start_time:
        duration = time.time() - start_time
        INGESTION_DURATION.labels(status=request.status.value).observe(duration)

    return {"status": "processed"}