from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_ready_with_database(client):
    assert client.get("/ready").json() == {"status": "ok"}


def test_readiness_reports_database_failure(client):
    class FailingSession:
        def execute(self, statement):
            raise OperationalError(None, None, RuntimeError("database offline"))

    app.dependency_overrides[get_db] = FailingSession
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert client.get("/health").status_code == 200
