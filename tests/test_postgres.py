"""Integration coverage for a disposable PostgreSQL database upgraded with Alembic."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1", reason="requires a migrated PostgreSQL database"
)


def test_concurrent_registration_and_task_lifecycle():
    assert engine.url.get_backend_name() == "postgresql"
    credentials = {"email": f"{uuid4()}@example.com", "password": "password123"}

    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200

        def register():
            return client.post("/auth/register", json=credentials).status_code

        with ThreadPoolExecutor(max_workers=6) as workers:
            requests = [workers.submit(register) for _ in range(6)]
            assert sorted(request.result() for request in requests) == [201, 409, 409, 409, 409, 409]

        login = client.post("/auth/login", json=credentials)
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        task = client.post("/tasks", json={"title": "PostgreSQL smoke test"}, headers=headers)
        assert task.status_code == 201

        path = f"/tasks/{task.json()['id']}"
        assert client.get(path, headers=headers).status_code == 200
        assert client.delete(path, headers=headers).status_code == 204
        assert client.get(path, headers=headers).status_code == 404
