from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.attachment import AttachmentType


class AttachmentCreate(BaseModel):
    file_type: AttachmentType = AttachmentType.MATERIAL
    description: Optional[str] = None


class AttachmentOut(BaseModel):
    id: int
    lesson_id: int
    file_name: str
    file_path: str
    file_type: AttachmentType
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
