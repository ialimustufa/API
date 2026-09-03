"""Minimal HTTP integration smoke test (enabled when the app composition root exists)."""
from __future__ import annotations

import importlib

import pytest


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
