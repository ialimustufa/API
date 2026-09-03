#!/usr/bin/env python3
"""Validate the generated TaskBox OpenAPI document against its public contract."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def generated() -> dict[str, Any]:
    for name in ("taskbox.api", "taskbox.main", "taskbox.app"):
        try:
            module = importlib.import_module(name)
        except ImportError:
            continue
        app = getattr(module, "app", None)
        if app is not None and hasattr(app, "openapi"):
            return app.openapi()
    raise RuntimeError("FastAPI app not found")


def resolve(document: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    reference = value.get("$ref")
    if not reference:
        return value
    if not reference.startswith("#/components/"):
        raise ValueError(f"unsupported OpenAPI reference: {reference}")
    current: Any = document
    for part in reference.removeprefix("#/").split("/"):
        current = current[part]
    return current


def ref(value: dict[str, Any]) -> str | None:
    return value.get("$ref")


def operation_errors(
    contract: dict[str, Any],
    generated_doc: dict[str, Any],
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for key in ("operationId", "security"):
        if expected.get(key) != actual.get(key):
            errors.append(f"{key} differs")

    expected_request, actual_request = expected.get("requestBody"), actual.get("requestBody")
    if bool(expected_request) != bool(actual_request):
        errors.append("request body presence differs")
    elif expected_request and actual_request:
        expected_schema = expected_request["content"]["application/json"]["schema"]
        actual_schema = actual_request["content"]["application/json"]["schema"]
        if ref(expected_schema) != ref(actual_schema):
            errors.append("request body schema differs")

    expected_headers = {
        p["name"].lower() for p in expected.get("parameters", []) if p.get("in") == "header"
    }
    actual_headers = {
        p["name"].lower() for p in actual.get("parameters", []) if p.get("in") == "header"
    }
    if expected_headers != actual_headers:
        errors.append("header parameters differ")

    missing_statuses = set(expected["responses"]) - set(actual["responses"])
    if missing_statuses:
        return errors + [f"missing response status codes: {sorted(missing_statuses)}"]
    for status, expected_response in expected["responses"].items():
        expected_response = resolve(contract, expected_response)
        actual_response = resolve(generated_doc, actual["responses"][status])
        if set(expected_response.get("content", {})) != set(actual_response.get("content", {})):
            errors.append(f"{status} response media type differs")
            continue
        for media_type, expected_media in expected_response.get("content", {}).items():
            actual_media = actual_response["content"][media_type]
            if ref(expected_media["schema"]) != ref(actual_media["schema"]):
                errors.append(f"{status} response schema differs")
    return errors


def validate(contract: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("title", "version", "description"):
        if contract["info"].get(key) != actual["info"].get(key):
            errors.append(f"info.{key} differs")
    if contract.get("servers") != actual.get("servers"):
        errors.append("servers differ")
    if contract["components"]["securitySchemes"] != actual["components"]["securitySchemes"]:
        errors.append("security schemes differ")

    expected_paths = {
        (path, method)
        for path, item in contract["paths"].items()
        for method in item
        if method in METHODS
    }
    actual_paths = {
        (path, method)
        for path, item in actual["paths"].items()
        for method in item
        if method in METHODS
    }
    if expected_paths != actual_paths:
        errors.append("path and method set differs")
    for path, method in sorted(expected_paths & actual_paths):
        for error in operation_errors(
            contract, actual, contract["paths"][path][method], actual["paths"][path][method]
        ):
            errors.append(f"{method.upper()} {path}: {error}")

    for name, expected_schema in contract["components"]["schemas"].items():
        actual_schema = actual["components"].get("schemas", {}).get(name)
        if actual_schema is None:
            errors.append(f"component schema {name} is missing")
        elif not set(expected_schema.get("required", [])).issubset(
            actual_schema.get("required", [])
        ):
            errors.append(f"component schema {name} is missing required fields")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="contracts/taskbox.openapi.json")
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    errors = validate(contract, generated())
    if errors:
        print("OpenAPI contract mismatch:\n- " + "\n- ".join(errors))
        return 1
    operation_count = sum(
        len([method for method in item if method in METHODS]) for item in contract["paths"].values()
    )
    print(f"OpenAPI contract OK ({operation_count} operations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
