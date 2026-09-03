"""Corrected Flask implementation of the original jokes API.

Run locally with ``flask --app legacy.fixed_flask_api.app:create_app run``.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import Flask, Response, current_app, g, jsonify, request

from .auth import authenticate, configured_credentials
from .models import MalformedJSONError, ValidationError, validate_joke_payload
from .store import JokeStore

F = TypeVar("F", bound=Callable[..., Any])
PROBLEM_BASE = "https://ialimustufa.github.io/API/problems/"


def _problem(
    status: int,
    title: str,
    detail: str,
    code: str,
    *,
    errors: list[dict[str, str]] | None = None,
) -> Response:
    payload: dict[str, object] = {
        "type": f"{PROBLEM_BASE}{code.replace('_', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
        "code": code,
        "request_id": g.get("request_id", "req_unknown"),
    }
    if errors:
        payload["errors"] = errors
    response = Response(
        json.dumps(payload, separators=(",", ":")),
        status=status,
        content_type="application/problem+json",
    )
    if status == 401:
        # Keep the challenge deliberately simple for the teaching contract.
        response.headers["WWW-Authenticate"] = "Basic"
    return response


def _json_body() -> object:
    if not request.is_json:
        raise MalformedJSONError("Content-Type must be application/json.")
    try:
        return request.get_json(silent=False)
    except Exception as exc:
        raise MalformedJSONError("Request body is not valid JSON.") from exc


def _joke_response(joke: Any, status: int = 200) -> Response:
    response = jsonify(joke.as_dict())
    response.status_code = status
    return response


def _require_auth(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Response:
        username, password_hash = configured_credentials(current_app.config)
        if not password_hash:
            return _problem(
                503,
                "Authentication unavailable",
                "Configure LEGACY_API_PASSWORD_HASH before using write operations.",
                "authentication_not_configured",
            )
        if not authenticate(request.headers.get("Authorization"), username, password_hash):
            return _problem(
                401,
                "Authentication required",
                "Provide valid HTTP Basic credentials.",
                "authentication_required",
            )
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        TESTING=False,
        AUTH_USERNAME=os.environ.get("LEGACY_API_USERNAME", "admin"),
        AUTH_PASSWORD_HASH=os.environ.get("LEGACY_API_PASSWORD_HASH"),
        AUTH_PASSWORD=None,
        JOKE_STORE=None,
    )
    if test_config:
        app.config.update(test_config)
    app.extensions["joke_store"] = app.config.get("JOKE_STORE") or JokeStore()

    @app.before_request
    def set_request_id() -> None:
        incoming = request.headers.get("X-Request-ID", "")
        g.request_id = (
            incoming[:128]
            if incoming and all(ch.isprintable() for ch in incoming)
            else f"req_{uuid.uuid4().hex}"
        )

    @app.after_request
    def add_request_id(response: Response) -> Response:
        response.headers.setdefault("X-Request-ID", g.get("request_id", "req_unknown"))
        return response

    @app.get("/health/live")
    def live() -> Response:
        return jsonify({"status": "ok"})

    @app.get("/api/v1/jokes")
    def list_jokes() -> Response:
        try:
            page = _positive_int(request.args.get("page", "1"), "page")
            page_size = _positive_int(request.args.get("page_size", "20"), "page_size")
            if page_size > 100:
                raise ValidationError("'page_size' must be at most 100.", "page_size")
        except MalformedJSONError as exc:
            return _malformed_json_problem(exc)
        except ValidationError as exc:
            return _problem(400, "Invalid pagination", str(exc), "invalid_pagination")
        items = app.extensions["joke_store"].list(
            author=request.args.get("author"), query=request.args.get("q")
        )
        start = (page - 1) * page_size
        selected = items[start : start + page_size]
        return jsonify(
            {
                "items": [item.as_dict() for item in selected],
                "page": page,
                "page_size": page_size,
                "total": len(items),
            }
        )

    @app.get("/api/v1/jokes/random")
    def random_joke() -> Response:
        joke = app.extensions["joke_store"].random(
            author=request.args.get("author"), query=request.args.get("q")
        )
        if joke is None:
            return _not_found("No joke matched the requested filters.", "joke_not_found")
        return _joke_response(joke)

    @app.get("/api/v1/jokes/<int:joke_id>")
    def get_joke(joke_id: int) -> Response:
        joke = app.extensions["joke_store"].get(joke_id)
        if joke is None:
            return _not_found(f"Joke {joke_id} was not found.", "joke_not_found")
        return _joke_response(joke)

    @app.post("/api/v1/jokes")
    @_require_auth
    def create_joke() -> Response:
        try:
            values = validate_joke_payload(_json_body())
        except MalformedJSONError as exc:
            return _malformed_json_problem(exc)
        except ValidationError as exc:
            return _validation_problem(exc)
        joke = app.extensions["joke_store"].create(**values)
        response = _joke_response(joke, 201)
        response.headers["Location"] = f"/api/v1/jokes/{joke.id}"
        return response

    @app.put("/api/v1/jokes/<int:joke_id>")
    @_require_auth
    def replace_joke(joke_id: int) -> Response:
        try:
            values = validate_joke_payload(_json_body())
        except ValidationError as exc:
            return _validation_problem(exc)
        joke = app.extensions["joke_store"].replace(joke_id, **values)
        if joke is None:
            return _not_found(f"Joke {joke_id} was not found.", "joke_not_found")
        return _joke_response(joke)

    @app.delete("/api/v1/jokes/<int:joke_id>")
    @_require_auth
    def delete_joke(joke_id: int) -> Response:
        if not app.extensions["joke_store"].delete(joke_id):
            return _not_found(f"Joke {joke_id} was not found.", "joke_not_found")
        response = Response(status=204)
        response.headers.pop("Content-Type", None)
        return response

    @app.errorhandler(404)
    def handle_404(error: Any) -> Response:
        return _not_found("The requested route was not found.", "route_not_found")

    @app.errorhandler(405)
    def handle_405(error: Any) -> Response:
        return _problem(
            405,
            "Method not allowed",
            "This method is not supported for the route.",
            "method_not_allowed",
        )

    return app


def _positive_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"'{field}' must be an integer.", field) from exc
    if parsed < 1:
        raise ValidationError(f"'{field}' must be at least 1.", field)
    return parsed


def _validation_problem(error: ValidationError) -> Response:
    errors = [{"field": error.field, "message": str(error)}] if error.field else None
    return _problem(422, "Validation failed", str(error), "validation_failed", errors=errors)


def _malformed_json_problem(error: MalformedJSONError) -> Response:
    return _problem(400, "Malformed JSON", str(error), "malformed_json")


def _not_found(detail: str, code: str) -> Response:
    return _problem(
        404,
        "Joke not found" if code == "joke_not_found" else "Route not found",
        detail,
        code,
    )


if __name__ == "__main__":  # pragma: no cover
    create_app().run(debug=False)
