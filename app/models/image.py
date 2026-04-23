from typing import Optional, Dict, Any
from uuid import UUID
import uuid6
from datetime import datetime
from pydantic import BaseModel, Field

class ImageBase(BaseModel):
    device_id: str
    status: str
    captured_at: datetime = Field(default_factory=datetime.now)
    image_path: str
    context: Dict[str, Any] = Field(default_factory=dict)
    route_key: Optional[str] = None

class ImageCreate(ImageBase):
    id: UUID = Field(default_factory=uuid6.uuid7)

class ImageRead(ImageBase):
    id: UUID
