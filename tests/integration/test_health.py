"""Minimal HTTP integration smoke test (enabled when the app composition root exists)."""

from __future__ import annotations

import importlib

import pytest

from taskbox.main import create_app


def test_healthz() -> None:
    for module_name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        app = getattr(module, "app", None)
        if app is not None:
            from fastapi.testclient import TestClient

            response = TestClient(app).get("/healthz")
            assert response.status_code == 200
            return
    pytest.skip("TaskBox HTTP application is not present in this lab checkout")


def test_readyz_uses_locked_database_runner() -> None:
    from fastapi.testclient import TestClient

    app = create_app(database_url="sqlite:///:memory:")
    database = app.state.database
    original_run = database.run
    calls = 0

    def locked_run(callback):
        nonlocal calls
        calls += 1
        return original_run(callback)

    database.run = locked_run
    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == 1


def test_healthz_is_grouped_under_the_health_openapi_tag() -> None:
    app = create_app(database_url="sqlite:///:memory:")

    document = app.openapi()

    assert {"name": "Health"} in document["tags"]
    assert document["paths"]["/healthz"]["get"]["tags"] == ["Health"]


@pytest.mark.parametrize("environment", ["production", "staging"])
@pytest.mark.parametrize(
    ("setting", "development_value"),
    [
        ("TASKBOX_JWT_SECRET", "dev-only-change-me"),
        ("TASKBOX_WEBHOOK_SECRET", "dev-webhook-secret"),
        ("TASKBOX_JWT_SECRET", "change-me-in-development"),
    ],
)
def test_strict_environments_reject_known_development_secrets(
    monkeypatch, environment: str, setting: str, development_value: str
) -> None:
    monkeypatch.setenv("TASKBOX_ENV", environment)
    monkeypatch.setenv("TASKBOX_JWT_SECRET", "jwt-secret-for-a-production-test")
    monkeypatch.setenv("TASKBOX_WEBHOOK_SECRET", "webhook-secret-for-a-production-test")
    monkeypatch.setenv(setting, development_value)

    with pytest.raises(RuntimeError, match=setting):
        create_app(database_url="sqlite:///:memory:")


def test_local_development_retains_disposable_secret_defaults(monkeypatch) -> None:
    monkeypatch.setenv("TASKBOX_ENV", "development")
    monkeypatch.delenv("TASKBOX_JWT_SECRET", raising=False)
    monkeypatch.delenv("TASKBOX_WEBHOOK_SECRET", raising=False)

    app = create_app(database_url="sqlite:///:memory:")

    assert app.title == "TaskBox API"


def test_empty_secrets_are_rejected_in_every_environment(monkeypatch) -> None:
    monkeypatch.setenv("TASKBOX_ENV", "development")

    with pytest.raises(RuntimeError, match="TASKBOX_JWT_SECRET"):
        create_app(
            database_url="sqlite:///:memory:",
            jwt_secret="",
            webhook_secret="webhook-secret-for-a-test",
        )
