"""Smoke-test the wheel rather than relying on an editable source checkout."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_built_wheel_includes_and_loads_reference_schema(tmp_path: Path) -> None:
    """The SQL resource must survive packaging because app import reads it eagerly."""
    wheel_dir = tmp_path / "wheel"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "hatchling",
            "build",
            "--target",
            "wheel",
            "--directory",
            str(wheel_dir),
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )

    wheel = next(wheel_dir.glob("taskbox_api_course-*.whl"))
    extracted_wheel = tmp_path / "installed-wheel"
    with ZipFile(wheel) as archive:
        assert "taskbox/adapters/reference_schema.sql" in archive.namelist()
        archive.extractall(extracted_wheel)

    environment = os.environ | {
        "PYTHONPATH": str(extracted_wheel),
        "TASKBOX_ENV": "test",
        "TASKBOX_DATABASE_URL": "sqlite:///:memory:",
        "TASKBOX_JWT_SECRET": "wheel-test-jwt-secret",
        "TASKBOX_WEBHOOK_SECRET": "wheel-test-webhook-secret",
    }
    smoke_test = """
import sys
from importlib.resources import files
from pathlib import Path

import taskbox.main
from taskbox.adapters import sqlite

wheel_root = Path(sys.argv[1]).resolve()
assert Path(taskbox.main.__file__).resolve().is_relative_to(wheel_root)
assert Path(sqlite.__file__).resolve().is_relative_to(wheel_root)
schema = files("taskbox.adapters").joinpath("reference_schema.sql")
assert "CREATE TABLE IF NOT EXISTS users" in schema.read_text()
assert "CREATE TABLE IF NOT EXISTS users" in sqlite.REFERENCE_SCHEMA
"""
    subprocess.run(
        [sys.executable, "-c", smoke_test, str(extracted_wheel)],
        check=True,
        cwd=tmp_path,
        env=environment,
    )
