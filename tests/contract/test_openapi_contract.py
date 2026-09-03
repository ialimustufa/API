"""Contract-level verification for the generated TaskBox OpenAPI document."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts.check_openapi_contract import validate


def _app():
    for module_name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        app = getattr(module, "app", None)
        if app is not None and hasattr(app, "openapi"):
            return app
    pytest.skip("TaskBox HTTP application is not present in this lab checkout")


def test_generated_document_matches_curated_contract() -> None:
    contract = json.loads(Path("contracts/taskbox.openapi.json").read_text(encoding="utf-8"))
    assert validate(contract, _app().openapi()) == []
