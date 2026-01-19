from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    device_id: str
    filename: str
    file_size_bytes: int
    sha256_checksum: str = Field(..., min_length=64, max_length=64)
    context: List[str] = []
    metadata: Dict[str, str] = {}
    timestamp: datetime

class IngestResponse(BaseModel):
    handshake_id: UUID
    upload_url: str
    expires_at: datetime

class IngestStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class EventType(str, Enum):
    FILE_UPLOADED = "file.uploaded"
    AI_PROCESSED = "ai.processed"

class ConfirmRequest(BaseModel):
    handshake_id: UUID
    status: IngestStatus
    error_message: Optional[str] = None

class PairingRequest(BaseModel):
    device_id: str

class PairingResponse(BaseModel):
    code: str
    expires_at: datetime

class PairingStatus(str, Enum):
    WAITING = "WAITING"
    CLAIMED = "CLAIMED"
    EXPIRED = "EXPIRED"

class PairingStatusResponse(BaseModel):
    status: PairingStatus
    apikey: Optional[str] = None
