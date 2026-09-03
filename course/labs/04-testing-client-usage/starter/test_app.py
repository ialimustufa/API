from fastapi.testclient import TestClient
from starter.app import app

client = TestClient(app)


def test_unknown_note_is_not_found():
    # TODO: assert the appropriate response status for an unknown UUID.
    response = client.get("/api/v1/notes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 501
