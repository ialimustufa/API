"""Executable checks that keep the generated API aligned with the course contract."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _app():
    for module_name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        if hasattr(module, "app") and hasattr(module.app, "openapi"):
            return module.app
    pytest.skip("TaskBox HTTP application is not present in this lab checkout")


def test_generated_paths_match_committed_contract() -> None:
    expected = json.loads(Path("contracts/taskbox.openapi.json").read_text())
    actual = _app().openapi()
    methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    expected_routes = {
        (p, m) for p, item in expected["paths"].items() for m in item if m in methods
    }
    actual_routes = {
        (p, m) for p, item in actual["paths"].items() for m in item if m in methods
    }
    assert actual_routes == expected_routes
