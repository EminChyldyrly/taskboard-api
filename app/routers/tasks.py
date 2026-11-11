from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import func, or_, select

from app.deps import CurrentUser, DbSession, get_task_for_participant
from app.models import Task, User
from app.schemas import Status, TaskCreate, TaskOut, TaskPage, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ensure_user_exists(db, user_id: int | None) -> None:
    if user_id is not None and db.get(User, user_id) is None:
        raise HTTPException(status_code=422, detail="Исполнитель не найден")


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: DbSession, user: CurrentUser):
    _ensure_user_exists(db, payload.assignee_id)
    task = Task(
        title=payload.title,
        description=payload.description,
        author_id=user.id,
        assignee_id=payload.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=TaskPage)
def list_tasks(
    db: DbSession,
    user: CurrentUser,
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    assignee_id: int | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Список задач, где пользователь автор или исполнитель, с фильтрами и пагинацией."""
    stmt = select(Task).where(or_(Task.author_id == user.id, Task.assignee_id == user.id))
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if q:
        stmt = stmt.where(Task.title.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Task.id.desc()).limit(limit).offset(offset)).all()
    return TaskPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: DbSession, user: CurrentUser):
    return get_task_for_participant(db, task_id, user)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: DbSession, user: CurrentUser):
    """Автор меняет любые поля, исполнитель — только статус."""
    task = get_task_for_participant(db, task_id, user)
    data = payload.model_dump(exclude_unset=True)
    for field in ("title", "description", "status"):
        if field in data and data[field] is None:
            raise HTTPException(status_code=422, detail=f"Поле {field} нельзя обнулить")
    if user.id != task.author_id and set(data) - {"status"}:
        raise HTTPException(status_code=403, detail="Исполнитель может менять только статус")
    if "assignee_id" in data:
        _ensure_user_exists(db, data["assignee_id"])
    for field, value in data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: DbSession, user: CurrentUser):
    task = get_task_for_participant(db, task_id, user)
    if task.author_id != user.id:
        raise HTTPException(status_code=403, detail="Удалять задачу может только автор")
    db.delete(task)
    db.commit()
    return Response(status_code=204)
