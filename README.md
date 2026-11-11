# taskboard-api

[![tests](https://github.com/EminChyldyrly/taskboard-api/actions/workflows/ci.yml/badge.svg)](https://github.com/EminChyldyrly/taskboard-api/actions/workflows/ci.yml)

REST API трекера задач на **FastAPI + PostgreSQL**: регистрация и вход по JWT, роли «автор» и «исполнитель», фильтры и пагинация, комментарии, миграции Alembic, запуск одной командой через Docker Compose.

*English: [README.en.md](README.en.md)*

## Быстрый старт

```bash
docker compose up --build
```

Сервис поднимется на http://localhost:8000, интерактивная документация — http://localhost:8000/docs. Миграции применяются автоматически при старте контейнера.

Пример работы:

```bash
# регистрация и вход
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
     -d '{"email":"anna@example.com","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
     -d '{"email":"anna@example.com","password":"password123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# создать задачу и посмотреть список
curl -X POST localhost:8000/tasks -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"title":"Подготовить релиз"}'
curl "localhost:8000/tasks?status=todo&limit=10" -H "Authorization: Bearer $TOKEN"
```

## Эндпоинты

| Метод | Путь | Что делает |
|---|---|---|
| POST | `/auth/register` | регистрация (e-mail, пароль от 8 символов) |
| POST | `/auth/login` | вход, возвращает JWT |
| POST | `/tasks` | создать задачу (автор — текущий пользователь), можно сразу назначить исполнителя |
| GET | `/tasks` | задачи, где вы автор или исполнитель; фильтры `status`, `assignee_id`, поиск `q`, пагинация `limit` (1–100) и `offset` |
| GET | `/tasks/{id}` | одна задача |
| PATCH | `/tasks/{id}` | автор меняет любые поля, исполнитель — только `status` |
| DELETE | `/tasks/{id}` | удалить может только автор |
| POST, GET | `/tasks/{id}/comments` | комментарии доступны автору и исполнителю |
| GET | `/health` | проверка работоспособности |

Статусы задачи: `todo`, `in_progress`, `done`. Чужая задача отвечает `404`, чтобы не раскрывать её существование.

## Схема базы данных

```
users     (id, email UNIQUE, password_hash, created_at)
tasks     (id, title, description, status, author_id → users, assignee_id → users NULL, created_at, updated_at)
comments  (id, task_id → tasks, author_id → users, text, created_at)
```

Индексы: `users.email` (уникальный), `tasks.status`, `tasks.author_id`, `tasks.assignee_id`, `comments.task_id`.

## Запуск без Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/taskboard   # по умолчанию SQLite-файл
alembic upgrade head
uvicorn app.main:app --reload
```

## Тесты

```bash
pip install -r requirements-dev.txt
pytest -q
```

Тесты используют SQLite в памяти и отдельную базу на каждый тест, поэтому PostgreSQL для них не нужен. Покрыты: регистрация и вход, права доступа (автор, исполнитель, посторонний), фильтры и пагинация, комментарии, валидация, хеширование паролей и токены. Тесты запускаются в GitHub Actions на каждый push.

## Настройки

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./taskboard.db` | строка подключения к базе |
| `SECRET_KEY` | заглушка для разработки | ключ подписи JWT; в продакшене задайте длинную случайную строку |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | срок жизни токена |

## Устройство проекта

```
app/            приложение: main.py, models.py, schemas.py, security.py, deps.py, routers/
migrations/     миграции Alembic
tests/          тесты pytest
```

Пароли хешируются PBKDF2-SHA256 (стандартная библиотека) с солью, токены подписываются HS256.

## Лицензия

MIT
