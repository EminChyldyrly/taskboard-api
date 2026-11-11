from tests.conftest import make_user


def test_register_and_login(client):
    user_id, headers = make_user(client, "Anna@Example.com")
    assert user_id == 1
    assert client.get("/tasks", headers=headers).status_code == 200


def test_duplicate_email_is_rejected(client):
    make_user(client, "a@example.com")
    again = client.post("/auth/register", json={"email": "A@example.com", "password": "password123"})
    assert again.status_code == 409


def test_invalid_registration_data(client):
    assert client.post("/auth/register", json={"email": "not-an-email", "password": "password123"}).status_code == 422
    assert client.post("/auth/register", json={"email": "a@example.com", "password": "short"}).status_code == 422


def test_wrong_password(client):
    make_user(client, "a@example.com")
    response = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_protected_routes_need_a_valid_token(client):
    assert client.get("/tasks").status_code == 401
    assert client.get("/tasks", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
