from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import PairingStatus

class PairingRequest(BaseModel):
    device_id: str

class PairingResponse(BaseModel):
    code: str
    expires_at: datetime

class PairingStatusResponse(BaseModel):
    status: PairingStatus
    apikey: Optional[str] = None
