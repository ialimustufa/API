#!/usr/bin/env python3
"""Check generated OpenAPI routes against the committed course contract."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path


def generated():
    for name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        app = getattr(mod, "app", None)
        if app is not None and hasattr(app, "openapi"):
            return app.openapi()
    raise RuntimeError("FastAPI app not found")


def route_methods(doc: dict) -> set[tuple[str, str]]:
    methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    return {
        (path, method)
        for path, item in doc.get("paths", {}).items()
        for method in item
        if method in methods
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="contracts/taskbox.openapi.json")
    args = parser.parse_args()
    expected = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    actual = generated()
    missing = sorted(route_methods(expected) - route_methods(actual))
    extra = sorted(route_methods(actual) - route_methods(expected))
    if missing or extra:
        if missing:
            print("Missing contract routes:", ", ".join(f"{m.upper()} {p}" for p, m in missing))
        if extra:
            print("Unexpected routes:", ", ".join(f"{m.upper()} {p}" for p, m in extra))
        return 1
    print(f"OpenAPI contract OK ({len(route_methods(expected))} operations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
