import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.device import DeviceRead
from app.db.session import DatabaseManager, get_db
from app.db.handlers.devices import DeviceHandler

router = APIRouter()
logger = logging.getLogger(__name__)

@router.patch("/{device_id}/metadata", response_model=DeviceRead)
async def update_device_metadata(
    device_id: str,
    metadata: Dict[str, Any],
    db: DatabaseManager = Depends(get_db)
):
    """
    Update the metadata for a specific device.
    This endpoint allows devices to 'blob' JSON metadata into their record.
    """
    device_handler = DeviceHandler(db.pool)
    
    logger.info(f"Updating metadata for device: {device_id}")
    
    updated_device = await device_handler.update_metadata(device_id, metadata)
    
    if not updated_device:
        logger.warning(f"Device not found for metadata update: {device_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )
        
    return updated_device
