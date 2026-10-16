"""
Система напоминаний о занятиях.
Аналог ReminderScheduler из примера Telegram-бота.
Использует APScheduler + (опционально) email.
"""
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.lesson import Lesson, LessonStatus
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Паттерн: инкапсуляция логики напоминаний.
    Снаружи достаточно start() / stop().
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._started = False

    async def _check_and_send(self):
        """Проверяет занятия, которые начнутся через ~2 часа, и отправляет напоминания."""
        now = datetime.now(timezone.utc)
        target_from = now + timedelta(hours=1, minutes=50)
        target_to = now + timedelta(hours=2, minutes=10)

        async with AsyncSessionLocal() as db:
            lessons = await db.scalars(
                select(Lesson)
                .where(
                    Lesson.status == LessonStatus.PLANNED,
                    Lesson.scheduled_at >= target_from,
                    Lesson.scheduled_at <= target_to,
                )
            )
            for lesson in lessons:
                # Здесь можно отправлять email / Telegram / push
                # Пока просто логируем (для демо)
                tutor = await db.get(User, lesson.tutor_id)
                student = await db.get(User, lesson.student_id)
                msg = (
                    f"Напоминание: занятие «{lesson.title}» "
                    f"в {lesson.scheduled_at.strftime('%d.%m.%Y %H:%M')} "
                    f"(репетитор: {tutor.full_name if tutor else '?'}, "
                    f"ученик: {student.full_name if student else '?'})"
                )
                logger.info(msg)
                # TODO: реальная отправка email / Telegram

    def start(self):
        if self._started:
            return
        # Каждые 10 минут проверяем
        self.scheduler.add_job(self._check_and_send, "interval", minutes=10)
        self.scheduler.start()
        self._started = True
        logger.info("ReminderService started")

    def stop(self):
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("ReminderService stopped")


# Глобальный экземпляр (Singleton)
reminder_service = ReminderService()
