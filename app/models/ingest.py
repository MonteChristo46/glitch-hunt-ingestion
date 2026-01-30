from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.enums import IngestStatus

class IngestRequest(BaseModel):
    device_id: str
    filename: str
    file_size_bytes: int
    sha256_checksum: str = Field(..., min_length=64, max_length=64)
    file_path_context: List[str] = []
    device_context: Dict[str, Any] = {}
    metadata: Dict[str, str] = {}
    timestamp: datetime

class IngestResponse(BaseModel):
    handshake_id: UUID
    upload_url: str
    expires_at: datetime

class ConfirmRequest(BaseModel):
    handshake_id: UUID
    status: IngestStatus
    error_message: Optional[str] = None
