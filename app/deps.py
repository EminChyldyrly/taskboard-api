"""Общие зависимости: сессия БД, текущий пользователь, доступ к задаче."""
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, User
from app.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=401, detail="Требуется авторизация", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_task_for_participant(db: Session, task_id: int, user: User) -> Task:
    """Задача видна только автору и исполнителю; остальным отвечаем 404, чтобы не раскрывать её существование."""
    task = db.get(Task, task_id)
    if task is None or user.id not in (task.author_id, task.assignee_id):
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task
