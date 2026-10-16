from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HomeworkCreate(BaseModel):
    comment: Optional[str] = None


class HomeworkOut(BaseModel):
    id: int
    lesson_id: int
    student_id: int
    file_name: str
    file_path: str
    comment: Optional[str]
    submitted_at: datetime
    checked: bool
    tutor_feedback: Optional[str]

    class Config:
        from_attributes = True


class HomeworkFeedback(BaseModel):
    tutor_feedback: str
    checked: bool = True
