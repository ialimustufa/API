from fastapi.testclient import TestClient

from solution.app import app

client = TestClient(app)


def test_create_and_list_note():
    created = client.post("/api/v1/notes", json={"title": "First", "body": "Hello"})
    assert created.status_code == 201
    note = created.json()
    assert note["title"] == "First"
    listed = client.get("/api/v1/notes")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == note["id"]


def test_validation_is_explicit():
    response = client.post("/api/v1/notes", json={"title": ""})
    assert response.status_code == 422


def test_missing_note_is_not_found():
    response = client.delete("/api/v1/notes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
