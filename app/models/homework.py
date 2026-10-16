from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Homework(Base):
    """Готовая домашняя работа, загруженная учеником."""
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    checked: Mapped[bool] = mapped_column(default=False)
    tutor_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    lesson = relationship("Lesson", back_populates="homeworks")
    student = relationship("User")

    def __repr__(self) -> str:
        return f"<Homework {self.file_name} for lesson {self.lesson_id}>"
