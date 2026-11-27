from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession

from app.routers import auth, comments, tasks

app = FastAPI(title="taskboard-api", version="0.1.0", description="API трекера задач: авторы, исполнители, комментарии")
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["service"])
def ready(db: DbSession):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}
