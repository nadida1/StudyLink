from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.lesson import Lesson, LessonStatus
from app.models.user import User, UserRole
from app.schemas.lesson import LessonCreate, LessonUpdate


class LessonService:
    """Сервис занятий — создание, обновление, отметка оплаты."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tutor: User, data: LessonCreate) -> Lesson:
        if tutor.role != UserRole.TUTOR:
            raise HTTPException(status_code=403, detail="Только репетитор может создавать занятия")
        student = await self.db.get(User, data.student_id)
        if not student or student.role != UserRole.STUDENT:
            raise HTTPException(status_code=404, detail="Ученик не найден")
        lesson = Lesson(
            tutor_id=tutor.id,
            student_id=data.student_id,
            title=data.title,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            meeting_link=data.meeting_link,
            notes=data.notes,
        )
        self.db.add(lesson)
        await self.db.flush()
        return lesson

    async def get(self, lesson_id: int, user: User) -> Lesson:
        lesson = await self.db.scalar(
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(selectinload(Lesson.attachments), selectinload(Lesson.homeworks))
        )
        if not lesson:
            raise HTTPException(status_code=404, detail="Занятие не найдено")
        if user.id not in (lesson.tutor_id, lesson.student_id):
            raise HTTPException(status_code=403, detail="Нет доступа к этому занятию")
        return lesson

    async def list_for_user(self, user: User) -> list[Lesson]:
        if user.role == UserRole.TUTOR:
            q = select(Lesson).where(Lesson.tutor_id == user.id)
        else:
            q = select(Lesson).where(Lesson.student_id == user.id)
        result = await self.db.scalars(q.order_by(Lesson.scheduled_at.desc()))
        return list(result)

    async def mark_payment(self, lesson_id: int, user: User, paid: bool = True) -> Lesson:
        lesson = await self.get(lesson_id, user)
        if user.role == UserRole.STUDENT and user.id == lesson.student_id:
            lesson.paid_by_student = paid
        elif user.role == UserRole.TUTOR and user.id == lesson.tutor_id:
            lesson.paid_by_tutor = paid
        else:
            raise HTTPException(status_code=403, detail="Вы не участник этого занятия")
        if lesson.is_fully_paid and not lesson.payment_confirmed_at:
            lesson.payment_confirmed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return lesson

    async def update(self, lesson_id: int, user: User, data: LessonUpdate) -> Lesson:
        lesson = await self.get(lesson_id, user)
        if user.role != UserRole.TUTOR or user.id != lesson.tutor_id:
            raise HTTPException(status_code=403, detail="Только репетитор может редактировать")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lesson, field, value)
        await self.db.flush()
        return lesson
