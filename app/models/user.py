from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class UserRole(str, PyEnum):
    TUTOR = "tutor"
    STUDENT = "student"


class User(Base):
    """Модель пользователя (репетитор или ученик)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.STUDENT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lessons_as_tutor = relationship("Lesson", back_populates="tutor", foreign_keys="Lesson.tutor_id")
    lessons_as_student = relationship("Lesson", back_populates="student", foreign_keys="Lesson.student_id")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
