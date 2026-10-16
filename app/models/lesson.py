from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class LessonStatus(str, PyEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Lesson(Base):
    """Занятие между репетитором и учеником."""
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), default="Занятие")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(default=60)
    meeting_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=LessonStatus.PLANNED,
    )

    # Отметка оплаты с обеих сторон
    paid_by_student: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_by_tutor: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tutor = relationship("User", back_populates="lessons_as_tutor", foreign_keys=[tutor_id])
    student = relationship("User", back_populates="lessons_as_student", foreign_keys=[student_id])
    attachments = relationship("Attachment", back_populates="lesson", cascade="all, delete-orphan")
    homeworks = relationship("Homework", back_populates="lesson", cascade="all, delete-orphan")

    @property
    def is_fully_paid(self) -> bool:
        """Оплата подтверждена обеими сторонами."""
        return self.paid_by_student and self.paid_by_tutor

    def __repr__(self) -> str:
        return f"<Lesson {self.id} {self.scheduled_at}>"
