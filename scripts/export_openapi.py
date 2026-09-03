#!/usr/bin/env python3
"""Export the TaskBox application's generated OpenAPI document.

Usage: python scripts/export_openapi.py OUTPUT.json
The app can expose either ``taskbox.api:app`` or ``taskbox.main:app``.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def find_app():
    for module_name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        app = getattr(module, "app", None)
        if app is not None and hasattr(app, "openapi"):
            return app
    raise RuntimeError("Could not find a FastAPI app (tried taskbox.api/main/app:app)")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/export_openapi.py OUTPUT.json", file=sys.stderr)
        return 2
    destination = Path(sys.argv[1])
    document = find_app().openapi()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
