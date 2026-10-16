from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AttachmentType(str, PyEnum):
    HOMEWORK = "homework"          # ДЗ от репетитора
    MATERIAL = "material"          # Дополнительные материалы
    LESSON_LINK = "lesson_link"    # Ссылка (можно хранить и в Lesson.meeting_link)


class Attachment(Base):
    """Файлы и материалы, прикреплённые репетитором к занятию."""
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[AttachmentType] = mapped_column(
        Enum(AttachmentType, values_callable=lambda obj: [e.value for e in obj]),
        default=AttachmentType.MATERIAL,
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lesson = relationship("Lesson", back_populates="attachments")
    uploaded_by = relationship("User")

    def __repr__(self) -> str:
        return f"<Attachment {self.file_name} ({self.file_type})>"
