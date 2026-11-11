# taskboard-api

A task-tracker REST API built with **FastAPI + PostgreSQL**: JWT authentication, author/assignee roles, filtering and pagination, comments, Alembic migrations, one-command startup with Docker Compose.

## Quick start

```bash
docker compose up --build
```

The API is served at http://localhost:8000 and the interactive docs at http://localhost:8000/docs. Migrations are applied automatically on container start.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | sign up (e-mail, password of 8+ characters) |
| POST | `/auth/login` | log in, returns a JWT |
| POST | `/tasks` | create a task, optionally with an assignee |
| GET | `/tasks` | tasks where you are the author or the assignee; filters `status`, `assignee_id`, search `q`, pagination `limit` (1–100) and `offset` |
| GET | `/tasks/{id}` | a single task |
| PATCH | `/tasks/{id}` | the author edits any field, the assignee only `status` |
| DELETE | `/tasks/{id}` | author only |
| POST, GET | `/tasks/{id}/comments` | comments, visible to the author and the assignee |
| GET | `/health` | health check |

Tasks of other users answer `404` so their existence is not revealed.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests run against in-memory SQLite with a fresh database per test, so PostgreSQL is not required. CI runs them on every push.

## License

MIT
