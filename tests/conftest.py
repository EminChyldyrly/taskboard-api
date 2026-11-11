import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """Клиент с чистой SQLite-базой в памяти на каждый тест."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def make_user(client, email, password="password123"):
    """Регистрирует пользователя и возвращает (id, заголовки авторизации)."""
    created = client.post("/auth/register", json={"email": email, "password": password})
    assert created.status_code == 201, created.text
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return created.json()["id"], {"Authorization": f"Bearer {token}"}
