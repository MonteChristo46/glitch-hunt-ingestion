from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class DeviceBase(BaseModel):
    device_id: str
    account_id: UUID
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeviceCreate(DeviceBase):
    auth_token_hash: str

class DeviceRead(DeviceBase):
    pass
