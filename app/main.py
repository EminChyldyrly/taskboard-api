from fastapi import FastAPI

from app.routers import auth, comments, tasks

app = FastAPI(title="taskboard-api", version="0.1.0", description="API трекера задач: авторы, исполнители, комментарии")
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}
