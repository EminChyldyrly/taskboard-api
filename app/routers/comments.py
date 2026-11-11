from fastapi import APIRouter

from app.deps import CurrentUser, DbSession, get_task_for_participant
from app.models import Comment
from app.schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["comments"])


@router.post("", response_model=CommentOut, status_code=201)
def add_comment(task_id: int, payload: CommentCreate, db: DbSession, user: CurrentUser):
    task = get_task_for_participant(db, task_id, user)
    comment = Comment(task_id=task.id, author_id=user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("", response_model=list[CommentOut])
def list_comments(task_id: int, db: DbSession, user: CurrentUser):
    task = get_task_for_participant(db, task_id, user)
    return task.comments
