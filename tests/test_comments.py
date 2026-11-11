from tests.conftest import make_user


def test_participants_can_comment(client):
    _, author = make_user(client, "author@example.com")
    assignee_id, assignee = make_user(client, "worker@example.com")
    task = client.post("/tasks", json={"title": "x", "assignee_id": assignee_id}, headers=author).json()

    first = client.post(f"/tasks/{task['id']}/comments", json={"text": "Взял в работу"}, headers=assignee)
    assert first.status_code == 201
    client.post(f"/tasks/{task['id']}/comments", json={"text": "Спасибо"}, headers=author)

    comments = client.get(f"/tasks/{task['id']}/comments", headers=author).json()
    assert [c["text"] for c in comments] == ["Взял в работу", "Спасибо"]


def test_stranger_cannot_read_or_write_comments(client):
    _, author = make_user(client, "author@example.com")
    _, stranger = make_user(client, "stranger@example.com")
    task = client.post("/tasks", json={"title": "x"}, headers=author).json()
    assert client.get(f"/tasks/{task['id']}/comments", headers=stranger).status_code == 404
    assert client.post(f"/tasks/{task['id']}/comments", json={"text": "hi"}, headers=stranger).status_code == 404


def test_empty_comment_is_rejected(client):
    _, author = make_user(client, "author@example.com")
    task = client.post("/tasks", json={"title": "x"}, headers=author).json()
    assert client.post(f"/tasks/{task['id']}/comments", json={"text": ""}, headers=author).status_code == 422


def test_deleting_a_task_removes_its_comments(client):
    _, author = make_user(client, "author@example.com")
    task = client.post("/tasks", json={"title": "x"}, headers=author).json()
    client.post(f"/tasks/{task['id']}/comments", json={"text": "hi"}, headers=author)
    assert client.delete(f"/tasks/{task['id']}", headers=author).status_code == 204
    assert client.get(f"/tasks/{task['id']}/comments", headers=author).status_code == 404
