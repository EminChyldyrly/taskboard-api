from tests.conftest import make_user


def create_task(client, headers, **fields):
    payload = {"title": "Написать тесты", **fields}
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_task(client):
    author_id, headers = make_user(client, "author@example.com")
    task = create_task(client, headers, description="pytest")
    assert task["author_id"] == author_id
    assert task["status"] == "todo"
    assert task["assignee_id"] is None
    fetched = client.get(f"/tasks/{task['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Написать тесты"


def test_title_is_required(client):
    _, headers = make_user(client, "author@example.com")
    assert client.post("/tasks", json={"title": ""}, headers=headers).status_code == 422
    assert client.post("/tasks", json={}, headers=headers).status_code == 422


def test_unknown_assignee_is_rejected(client):
    _, headers = make_user(client, "author@example.com")
    response = client.post("/tasks", json={"title": "x", "assignee_id": 999}, headers=headers)
    assert response.status_code == 422


def test_stranger_cannot_see_the_task(client):
    _, author = make_user(client, "author@example.com")
    _, stranger = make_user(client, "stranger@example.com")
    task = create_task(client, author)
    assert client.get(f"/tasks/{task['id']}", headers=stranger).status_code == 404
    assert client.get("/tasks", headers=stranger).json()["total"] == 0


def test_assignee_sees_task_and_changes_only_status(client):
    _, author = make_user(client, "author@example.com")
    assignee_id, assignee = make_user(client, "worker@example.com")
    task = create_task(client, author, assignee_id=assignee_id)

    assert client.get("/tasks", headers=assignee).json()["total"] == 1

    done = client.patch(f"/tasks/{task['id']}", json={"status": "done"}, headers=assignee)
    assert done.status_code == 200
    assert done.json()["status"] == "done"

    forbidden = client.patch(f"/tasks/{task['id']}", json={"title": "Другое"}, headers=assignee)
    assert forbidden.status_code == 403


def test_author_can_edit_and_reassign(client):
    _, author = make_user(client, "author@example.com")
    assignee_id, _ = make_user(client, "worker@example.com")
    task = create_task(client, author)
    updated = client.patch(
        f"/tasks/{task['id']}",
        json={"title": "Новое название", "assignee_id": assignee_id, "status": "in_progress"},
        headers=author,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert (body["title"], body["assignee_id"], body["status"]) == ("Новое название", assignee_id, "in_progress")
    unassigned = client.patch(f"/tasks/{task['id']}", json={"assignee_id": None}, headers=author)
    assert unassigned.json()["assignee_id"] is None


def test_invalid_status_and_null_title(client):
    _, author = make_user(client, "author@example.com")
    task = create_task(client, author)
    assert client.patch(f"/tasks/{task['id']}", json={"status": "weird"}, headers=author).status_code == 422
    assert client.patch(f"/tasks/{task['id']}", json={"title": None}, headers=author).status_code == 422


def test_only_author_can_delete(client):
    _, author = make_user(client, "author@example.com")
    assignee_id, assignee = make_user(client, "worker@example.com")
    task = create_task(client, author, assignee_id=assignee_id)
    assert client.delete(f"/tasks/{task['id']}", headers=assignee).status_code == 403
    assert client.delete(f"/tasks/{task['id']}", headers=author).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=author).status_code == 404


def test_filters_search_and_pagination(client):
    _, author = make_user(client, "author@example.com")
    for index in range(5):
        create_task(client, author, title=f"Задача {index}")
    create_task(client, author, title="Релиз версии 1.0")
    done = create_task(client, author, title="Старая задача")
    client.patch(f"/tasks/{done['id']}", json={"status": "done"}, headers=author)

    page = client.get("/tasks", params={"limit": 3, "offset": 0}, headers=author).json()
    assert page["total"] == 7
    assert len(page["items"]) == 3
    assert page["items"][0]["id"] > page["items"][1]["id"]

    second = client.get("/tasks", params={"limit": 3, "offset": 6}, headers=author).json()
    assert len(second["items"]) == 1

    assert client.get("/tasks", params={"status": "done"}, headers=author).json()["total"] == 1
    assert client.get("/tasks", params={"q": "релиз"}, headers=author).json()["total"] == 1
    assert client.get("/tasks", params={"limit": 1000}, headers=author).status_code == 422
