from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import engine, get_db
from app.models import Base, User, UserRole
from app.api import auth, lessons
from app.services.reminder_service import reminder_service
from app.services.auth_service import AuthService
from app.services.lesson_service import LessonService
from app.core.security import create_access_token, decode_access_token
from app.core.config import get_settings
from app.schemas.user import UserCreate
import logging

logging.basicConfig(level=logging.INFO)
settings = get_settings()

# --- Надёжный способ работы с шаблонами (без бага Starlette) ---
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render(template_name: str, **context) -> HTMLResponse:
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    reminder_service.start()
    yield
    reminder_service.stop()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Веб-платформа для репетиторов",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(lessons.router, prefix="/api")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------- Helpers ----------

async def get_current_user_from_cookie(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    user = await db.get(User, user_id)
    return user if user and user.is_active else None


def login_redirect():
    return RedirectResponse("/login?error=Войдите+в+аккаунт", status_code=303)


# ---------- Web pages ----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user_from_cookie)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return render("home.html", request=request, user=user)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user_from_cookie)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return render("login.html", request=request, user=user)


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        user = await service.authenticate(email, password)
    except HTTPException:
        return RedirectResponse("/login?error=Неверный+email+или+пароль", status_code=303)
    token = service.create_token(user)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user_from_cookie)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return render("register.html", request=request, user=user)


@app.post("/register")
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        role_enum = UserRole.TUTOR if role == "tutor" else UserRole.STUDENT
        data = UserCreate(email=email, password=password, full_name=full_name, role=role_enum)
        user = await service.register(data)
    except HTTPException as e:
        return RedirectResponse(f"/register?error={e.detail}", status_code=303)
    token = service.create_token(user)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    service = LessonService(db)
    lessons_list = await service.list_for_user(user)
    return render("dashboard.html", request=request, user=user, lessons=lessons_list)


@app.post("/lessons/{lesson_id}/pay")
async def pay_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    service = LessonService(db)
    try:
        await service.mark_payment(lesson_id, user, paid=True)
    except HTTPException:
        return RedirectResponse("/dashboard?error=Не+удалось+отметить+оплату", status_code=303)
    return RedirectResponse("/dashboard?success=Оплата+отмечена", status_code=303)

@app.get("/lessons/new", response_class=HTMLResponse)
async def lesson_new_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    if str(user.role) not in ("tutor", "UserRole.TUTOR") and getattr(user.role, "value", None) != "tutor":
        return RedirectResponse("/dashboard?error=Только+репетитор", status_code=303)

    # Получаем всех учеников
    result = await db.scalars(select(User).where(User.role == UserRole.STUDENT))
    students = list(result)

    return render("lesson_new.html", request=request, user=user, students=students)

@app.post("/lessons/new")
async def lesson_new_submit(
    request: Request,
    title: str = Form("Занятие"),
    student_id: int = Form(...),
    scheduled_at: str = Form(...),
    duration_minutes: int = Form(60),
    meeting_link: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    from datetime import datetime
    from app.schemas.lesson import LessonCreate
    try:
        dt = datetime.fromisoformat(scheduled_at)
        data = LessonCreate(
            student_id=student_id,
            title=title,
            scheduled_at=dt,
            duration_minutes=duration_minutes,
            meeting_link=meeting_link or None,
            notes=notes or None,
        )
        service = LessonService(db)
        await service.create(user, data)
    except Exception as e:
        return RedirectResponse(f"/lessons/new?error={str(e)}", status_code=303)
    return RedirectResponse("/dashboard?success=Занятие+создано", status_code=303)

@app.get("/lessons/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail(
    lesson_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    service = LessonService(db)
    try:
        lesson = await service.get(lesson_id, user)
    except HTTPException:
        return RedirectResponse("/dashboard?error=Занятие+не+найдено", status_code=303)
    return render(
        "lesson_detail.html",
        request=request,
        user=user,
        lesson=lesson,
        attachments=lesson.attachments or [],
        homeworks=lesson.homeworks or [],
    )


@app.post("/lessons/{lesson_id}/upload")
async def upload_file_web(
    lesson_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    form = await request.form()
    file = form.get("file")
    file_type = form.get("file_type", "material")
    if not file or not hasattr(file, "filename"):
        return RedirectResponse(f"/lessons/{lesson_id}?error=Файл+не+выбран", status_code=303)

    import os
    from uuid import uuid4
    import aiofiles
    from app.models.attachment import Attachment, AttachmentType

    service = LessonService(db)
    try:
        lesson = await service.get(lesson_id, user)
    except HTTPException:
        return RedirectResponse("/dashboard?error=Нет+доступа", status_code=303)

    if str(user.role) not in ("tutor", "UserRole.TUTOR") and getattr(user.role, "value", None) != "tutor":
        return RedirectResponse(f"/lessons/{lesson_id}?error=Только+репетитор", status_code=303)

    os.makedirs("uploads", exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid4().hex}{ext}"
    path = os.path.join("uploads", unique_name)
    content = await file.read()
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    att_type = AttachmentType.HOMEWORK if file_type == "homework" else AttachmentType.MATERIAL
    att = Attachment(
        lesson_id=lesson.id,
        uploaded_by_id=user.id,
        file_name=file.filename or unique_name,
        file_path=path,
        file_type=att_type,
    )
    db.add(att)
    await db.flush()
    return RedirectResponse(f"/lessons/{lesson_id}?success=Файл+загружен", status_code=303)


@app.post("/lessons/{lesson_id}/homework")
async def submit_homework_web(
    lesson_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    if not user:
        return login_redirect()
    form = await request.form()
    file = form.get("file")
    comment = form.get("comment") or None
    if not file or not hasattr(file, "filename"):
        return RedirectResponse(f"/lessons/{lesson_id}?error=Файл+не+выбран", status_code=303)

    import os
    from uuid import uuid4
    import aiofiles
    from app.models.homework import Homework

    service = LessonService(db)
    try:
        lesson = await service.get(lesson_id, user)
    except HTTPException:
        return RedirectResponse("/dashboard?error=Нет+доступа", status_code=303)

    if str(user.role) not in ("student", "UserRole.STUDENT") and getattr(user.role, "value", None) != "student":
        return RedirectResponse(f"/lessons/{lesson_id}?error=Только+ученик", status_code=303)

    os.makedirs("uploads", exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid4().hex}{ext}"
    path = os.path.join("uploads", unique_name)
    content = await file.read()
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)

    hw = Homework(
        lesson_id=lesson.id,
        student_id=user.id,
        file_name=file.filename or unique_name,
        file_path=path,
        comment=comment,
    )
    db.add(hw)
    await db.flush()
    return RedirectResponse(f"/lessons/{lesson_id}?success=ДЗ+сдано", status_code=303)

