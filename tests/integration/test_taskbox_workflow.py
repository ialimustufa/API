"""End-to-end coverage for the TaskBox learner-facing workflow."""

from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from taskbox.main import create_app


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple",
            "display_name": email.split("@", 1)[0].title(),
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/token",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200
    return registration.json()["id"], login.json()["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_problem_type_uses_the_request_host() -> None:
    app = create_app(database_url="sqlite:///:memory:")

    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        first = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "correct-horse-battery-staple",
                "display_name": "Duplicate",
            },
        )
        duplicate = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "correct-horse-battery-staple",
                "display_name": "Duplicate",
            },
        )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["type"] == "http://127.0.0.1:8000/problems/conflict"


def test_unknown_login_still_runs_password_verification(monkeypatch) -> None:
    app = create_app(database_url="sqlite:///:memory:")
    hasher = app.state.services.auth.hasher
    verification_calls: list[tuple[str, str]] = []

    def verify(password: str, password_hash: str) -> bool:
        verification_calls.append((password, password_hash))
        return False

    monkeypatch.setattr(hasher, "verify", verify)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/token",
            json={"email": "missing@example.com", "password": "incorrect-password"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"
    assert verification_calls == [
        ("incorrect-password", app.state.services.auth._missing_user_password_hash)
    ]


def test_authenticated_project_task_and_webhook_workflow() -> None:
    webhook_secret = "integration-webhook-secret"
    app = create_app(
        database_url="sqlite:///:memory:",
        jwt_secret="integration-jwt-secret-at-least-32-bytes-long",
        webhook_secret=webhook_secret,
    )

    with TestClient(app) as client:
        owner_id, owner_token = _register_and_login(client, "owner@example.com")
        viewer_id, viewer_token = _register_and_login(client, "viewer@example.com")

        project_response = client.post(
            "/api/v1/projects",
            headers=_bearer(owner_token),
            json={"name": "Course verification"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        member_response = client.post(
            f"/api/v1/projects/{project_id}/members",
            headers=_bearer(owner_token),
            json={"user_id": viewer_id, "role": "viewer"},
        )
        assert member_response.status_code == 201

        forbidden = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=_bearer(viewer_token),
            json={"title": "A viewer cannot create this"},
        )
        assert forbidden.status_code == 403
        assert forbidden.headers["content-type"].startswith("application/problem+json")

        task_response = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=_bearer(owner_token),
            json={"title": "Verify the API", "priority": 2},
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/tasks/{task_id}",
            headers=_bearer(owner_token),
            json={"status": "done"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "done"

        listing = client.get(
            f"/api/v1/projects/{project_id}/tasks?limit=1",
            headers=_bearer(viewer_token),
        )
        assert listing.status_code == 200
        assert [item["id"] for item in listing.json()["items"]] == [task_id]

        payload = json.dumps(
            {
                "project_id": project_id,
                "actor_id": owner_id,
                "tasks": [{"title": "Imported task"}],
            },
            separators=(",", ":"),
        ).encode()
        signature = hmac.new(webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        webhook_headers = {
            **_bearer(owner_token),
            "Content-Type": "application/json",
            "X-Webhook-Event-ID": "evt-integration-1",
            "X-Webhook-Signature": f"sha256={signature}",
        }

        missing_event_id = client.post(
            "/api/v1/webhooks/tasks/import",
            content=payload,
            headers={"X-Webhook-Signature": f"sha256={signature}"},
        )
        assert missing_event_id.status_code == 422

        altered_body = client.post(
            "/api/v1/webhooks/tasks/import",
            content=payload + b" ",
            headers=webhook_headers,
        )
        assert altered_body.status_code == 401

        imported = client.post(
            "/api/v1/webhooks/tasks/import", content=payload, headers=webhook_headers
        )
        assert imported.status_code == 202
        assert imported.json() == {"event_id": "evt-integration-1", "imported": 1}

        duplicate = client.post(
            "/api/v1/webhooks/tasks/import", content=payload, headers=webhook_headers
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "duplicate_webhook"
