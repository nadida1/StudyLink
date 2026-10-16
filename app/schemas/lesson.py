from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from app.models.lesson import LessonStatus
from app.schemas.user import UserOut


class LessonCreate(BaseModel):
    student_id: int
    title: str = "Занятие"
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    status: Optional[LessonStatus] = None
    notes: Optional[str] = None


class PaymentMark(BaseModel):
    """Отметка оплаты одной из сторон."""
    paid: bool = True


class LessonOut(BaseModel):
    id: int
    tutor_id: int
    student_id: int
    title: str
    scheduled_at: datetime
    duration_minutes: int
    meeting_link: Optional[str]
    status: LessonStatus
    paid_by_student: bool
    paid_by_tutor: bool
    is_fully_paid: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
