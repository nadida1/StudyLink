from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
from uuid import uuid4
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.attachment import Attachment, AttachmentType
from app.models.homework import Homework
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonOut, PaymentMark
from app.schemas.attachment import AttachmentOut
from app.schemas.homework import HomeworkOut, HomeworkCreate, HomeworkFeedback
from app.services.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["lessons"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=LessonOut)
async def create_lesson(
    data: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LessonService(db)
    lesson = await service.create(current_user, data)
    return lesson


@router.get("", response_model=List[LessonOut])
async def list_lessons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LessonService(db)
    return await service.list_for_user(current_user)


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LessonService(db)
    return await service.get(lesson_id, current_user)


@router.patch("/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LessonService(db)
    return await service.update(lesson_id, current_user, data)


@router.post("/{lesson_id}/payment", response_model=LessonOut)
async def mark_payment(
    lesson_id: int,
    data: PaymentMark,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отметить оплату занятия (ученик или репетитор)."""
    service = LessonService(db)
    return await service.mark_payment(lesson_id, current_user, data.paid)


@router.post("/{lesson_id}/attachments", response_model=AttachmentOut)
async def upload_attachment(
    lesson_id: int,
    file: UploadFile = File(...),
    file_type: AttachmentType = Form(AttachmentType.MATERIAL),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Репетитор прикрепляет файл (ДЗ / материалы)."""
    if current_user.role != UserRole.TUTOR:
        from fastapi import HTTPException
        raise HTTPException(403, "Только репетитор может загружать материалы")
    service = LessonService(db)
    lesson = await service.get(lesson_id, current_user)

    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    async with aiofiles.open(path, "wb") as f:
        content = await file.read()
        await f.write(content)

    att = Attachment(
        lesson_id=lesson.id,
        uploaded_by_id=current_user.id,
        file_name=file.filename or unique_name,
        file_path=path,
        file_type=file_type,
        description=description,
    )
    db.add(att)
    await db.flush()
    return att


@router.post("/{lesson_id}/homework", response_model=HomeworkOut)
async def submit_homework(
    lesson_id: int,
    file: UploadFile = File(...),
    comment: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ученик загружает готовую домашнюю работу."""
    if current_user.role != UserRole.STUDENT:
        from fastapi import HTTPException
        raise HTTPException(403, "Только ученик может сдавать ДЗ")
    service = LessonService(db)
    lesson = await service.get(lesson_id, current_user)

    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    async with aiofiles.open(path, "wb") as f:
        content = await file.read()
        await f.write(content)

    hw = Homework(
        lesson_id=lesson.id,
        student_id=current_user.id,
        file_name=file.filename or unique_name,
        file_path=path,
        comment=comment,
    )
    db.add(hw)
    await db.flush()
    return hw
