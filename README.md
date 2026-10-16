# Tutor Platform — веб-сайт для репетиторов

Платформа для управления занятиями между репетитором и учеником.

## Возможности (тема 12)

- Регистрация / вход (роли: **tutor** и **student**)
- Создание занятий репетитором
- Прикрепление ссылки на занятие, файлов ДЗ и материалов
- Загрузка готовой домашней работы учеником
- Отметка оплаты занятия **с обеих сторон**
- Автоматические напоминания о предстоящих занятиях (APScheduler)

## Стек

| Компонент       | Технология                          |
|-----------------|-------------------------------------|
| Язык            | Python 3.12                         |
| Framework       | FastAPI                             |
| ORM             | SQLAlchemy 2.0 (async)              |
| БД              | SQLite (dev) / PostgreSQL (prod)    |
| Auth            | JWT + OAuth2                        |
| Планировщик     | APScheduler                         |
| Файлы           | локальное хранилище `uploads/`      |

## Быстрый старт

```bash
cd tutor_web
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Для SQLite ничего дополнительно не нужно
# Для PostgreSQL: создай БД и пропиши DATABASE_URL в .env

uvicorn app.main:app --reload
```

Открой http://127.0.0.1:8000/docs — интерактивная документация Swagger.

## Основные эндпоинты

- `POST /api/auth/register` — регистрация
- `POST /api/auth/login` — вход (form-data: username=email, password=...)
- `GET  /api/auth/me` — текущий пользователь
- `POST /api/lessons` — создать занятие (только tutor)
- `GET  /api/lessons` — список своих занятий
- `POST /api/lessons/{id}/payment` — отметить оплату
- `POST /api/lessons/{id}/attachments` — загрузить файл (tutor)
- `POST /api/lessons/{id}/homework` — сдать ДЗ (student)

## ООП и паттерны

- **Единая ответственность**: каждый Service и Router отвечает за свою зону
- **Repository / Service layer**: бизнес-логика отделена от HTTP
- **Dependency Injection**: FastAPI Depends
- **Singleton**: `get_settings()`, `reminder_service`
- **Strategy** (можно расширить): разные каналы напоминаний (email / Telegram / push)
- **Observer-подобный**: планировщик следит за временем и реагирует

## Структура

```
tutor_web/
├── app/
│   ├── api/          # HTTP-роутеры
│   ├── core/         # конфиг, БД, security
│   ├── models/       # SQLAlchemy модели
│   ├── schemas/      # Pydantic схемы
│   ├── services/     # бизнес-логика
│   └── main.py
├── uploads/          # загруженные файлы
├── requirements.txt
└── README.md
```

## Дальнейшее развитие

1. Frontend (React / Vue / простой Jinja2)
2. Реальная отправка email / Telegram-напоминаний
3. Админ-панель для репетитора
4. Статистика оплат и посещаемости
5. Деплой (Timeweb / Railway / Render)
