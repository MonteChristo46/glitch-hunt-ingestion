from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import IngestStatus

class IngestionEventPayload(BaseModel):
    status: IngestStatus
    error_message: Optional[str] = None
    device_id: str
    filename: str
    file_size_bytes: int
    sha256_checksum: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    file_path_context: List[str] = []
    device_context: Dict[str, Any] = {}
