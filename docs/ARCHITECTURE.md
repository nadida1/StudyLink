# Архитектура — StudyLink

## Общий подход

Проект построен по принципу разделения ответственности:

- API / Web — HTTP-интерфейс (FastAPI + Jinja2)
- Services — бизнес-логика
- Models — сущности и работа с БД (SQLAlchemy)
- Schemas — валидация входных/выходных данных (Pydantic)

## Модули

`app/main.py` - точка входа, веб-страницы, lifespan 
`app/api/` - REST API (auth, lessons) 
`app/services/` - AuthService, LessonService, ReminderService 
`app/models/` - User, Lesson, Attachment, Homework 
`app/schemas/` - Pydantic-схемы 
`app/core/` - config, database, security 
`app/templates/` - HTML-шаблоны 

## Классы и ответственность

- User — пользователь (tutor / student)
- Lesson — занятие, статусы оплаты, ссылка
- Attachment — файлы репетитора (материалы / ДЗ)
- Homework — сданная работа ученика
- AuthService — регистрация, вход, токены
- LessonService — CRUD занятий, отметка оплаты
- ReminderService — фоновые напоминания (APScheduler)
- Config (Settings) — единая точка конфигурации (Singleton)

## Зависимости (стек)

- Python 3.12+
- FastAPI — веб-фреймворк
- SQLAlchemy 2.0 (async) + aiosqlite / PostgreSQL
- Jinja2 — шаблоны
- Pydantic — валидация
- APScheduler — напоминания
- bcrypt / python-jose — безопасность

## Хранение данных

- Разработка: SQLite (`tutor.db`)
- Production: PostgreSQL 
- Файлы: локальная папка `uploads/` 

## Паттерны ООП

- Единая ответственность — каждый Service и Model за свою зону
- Dependency Injection — FastAPI Depends
- Singleton — Settings, ReminderService
- Repository / Service layer — отделение бизнес-логики от HTTP
- Enum — роли, статусы, типы файлов
