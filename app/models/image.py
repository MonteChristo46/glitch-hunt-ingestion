from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class ImageBase(BaseModel):
    device_id: str
    status: str
    captured_at: Optional[datetime] = None
    image_path: str
    context: Dict[str, Any] = Field(default_factory=dict)
    route_key: Optional[str] = None

class ImageCreate(ImageBase):
    id: Optional[UUID] = None

class ImageRead(ImageBase):
    id: UUID
