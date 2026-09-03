"""Black-box contract tests for the corrected legacy Flask jokes API.

The application under test is deliberately imported inside the fixture.  This
keeps the test contract readable while allowing the implementation to land in
``legacy.fixed_flask_api`` independently of the tests.

The app factory contract used here is ``create_app(config: Mapping | None)``.
The primary authentication settings are ``BASIC_AUTH_USERNAME`` and
``BASIC_AUTH_PASSWORD_HASH``; the plain-password aliases are supplied only so
that a test configuration can work with a conventional Flask implementation
while the production configuration remains hash-based.
"""

from __future__ import annotations

import base64
from typing import Any

import pytest
from werkzeug.security import generate_password_hash

USERNAME = "contract-user"
PASSWORD = "contract-password"


def _auth_header(username: str = USERNAME, password: str = PASSWORD) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def _json(response: Any) -> dict[str, Any]:
    payload = response.get_json()
    assert isinstance(payload, dict), response.data
    return payload


def _assert_problem(response: Any, status: int) -> dict[str, Any]:
    assert response.status_code == status, response.data
    assert response.content_type == "application/problem+json"
    payload = _json(response)
    for field in ("type", "title", "status", "detail", "instance", "code", "request_id"):
        assert field in payload, payload
    assert payload["status"] == status
    return payload


@pytest.fixture
def app() -> Any:
    from legacy.fixed_flask_api.app import create_app

    password_hash = generate_password_hash(PASSWORD, method="scrypt")
    # ``create_app`` is required to accept a Flask-style configuration mapping.
    # Extra aliases are harmless Flask config entries and make this fixture
    # explicit about the accepted test-only injection points.
    application = create_app(
        {
            "TESTING": True,
            "BASIC_AUTH_USERNAME": USERNAME,
            "BASIC_AUTH_PASSWORD_HASH": password_hash,
            "BASIC_AUTH_PASSWORD": PASSWORD,
            "AUTH_USERNAME": USERNAME,
            "AUTH_PASSWORD_HASH": password_hash,
            "AUTH_PASSWORD": PASSWORD,
        }
    )
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app: Any) -> Any:
    return app.test_client()


def _create(client: Any, *, author: str = "Ada", joke: str = "A contract joke") -> Any:
    return client.post(
        "/api/v1/jokes",
        json={"author": author, "joke": joke},
        headers={"Authorization": _auth_header()},
    )


def test_liveness_is_public_and_json(client: Any) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.content_type == "application/json"
    payload = _json(response)
    assert payload.get("status") in {"ok", "healthy", "live"}


def test_collection_has_stable_envelope_and_seeded_id_zero(client: Any) -> None:
    response = client.get("/api/v1/jokes")

    assert response.status_code == 200
    payload = _json(response)
    assert set(("items", "page", "page_size", "total")) <= payload.keys()
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total"] >= 1
    assert any(item["id"] == 0 for item in payload["items"])


def test_item_zero_is_not_treated_as_random(client: Any) -> None:
    item = _json(client.get("/api/v1/jokes/0"))
    collection = _json(client.get("/api/v1/jokes"))
    seeded = next(entry for entry in collection["items"] if entry["id"] == 0)

    assert item["id"] == 0
    assert item == seeded


def test_random_returns_a_seeded_item(client: Any) -> None:
    response = client.get("/api/v1/jokes/random")

    assert response.status_code == 200
    payload = _json(response)
    assert isinstance(payload.get("id"), int)
    assert payload["joke"]


def test_random_empty_store_returns_not_found(client: Any) -> None:
    collection = _json(client.get("/api/v1/jokes"))
    for item in collection["items"]:
        deleted = client.delete(
            f"/api/v1/jokes/{item['id']}",
            headers={"Authorization": _auth_header()},
        )
        assert deleted.status_code == 204, deleted.data

    assert _assert_problem(client.get("/api/v1/jokes/random"), 404)["code"]


def test_collection_paginates_and_filters_by_author_and_query(client: Any) -> None:
    first = _create(client, author="Grace", joke="pagination marker alpha")
    second = _create(client, author="Grace", joke="pagination marker beta")
    assert first.status_code == 201
    assert second.status_code == 201

    page = client.get("/api/v1/jokes?page=1&page_size=1")
    page_payload = _json(page)
    assert page.status_code == 200
    assert len(page_payload["items"]) == 1
    assert page_payload["page"] == 1
    assert page_payload["page_size"] == 1
    assert page_payload["total"] >= 3

    author_payload = _json(client.get("/api/v1/jokes?author=Grace"))
    assert author_payload["total"] == 2
    assert {item["author"] for item in author_payload["items"]} == {"Grace"}

    query_payload = _json(client.get("/api/v1/jokes?q=marker+beta"))
    assert query_payload["total"] == 1
    assert query_payload["items"][0]["joke"] == "pagination marker beta"


def test_pagination_bounds_are_problem_details(client: Any) -> None:
    for query in ("page=0", "page_size=0", "page_size=101", "page=not-an-int"):
        _assert_problem(client.get(f"/api/v1/jokes?{query}"), 400)


@pytest.mark.parametrize(
    "body, expected_status",
    [
        ({}, 422),
        ({"author": "", "joke": "text"}, 422),
        ({"author": "Ada", "joke": ""}, 422),
        ({"author": "Ada", "joke": "x", "source": "not-a-url"}, 422),
        ({"author": "Ada", "joke": "x", "id": 10}, 422),
    ],
)
def test_create_validation_uses_problem_details(
    client: Any, body: dict[str, Any], expected_status: int
) -> None:
    response = client.post(
        "/api/v1/jokes",
        json=body,
        headers={"Authorization": _auth_header()},
    )
    _assert_problem(response, expected_status)


def test_malformed_json_is_bad_request(client: Any) -> None:
    response = client.post(
        "/api/v1/jokes",
        data="{not-json",
        content_type="application/json",
        headers={"Authorization": _auth_header()},
    )
    _assert_problem(response, 400)


def test_writes_require_basic_auth_and_advertise_challenge(client: Any) -> None:
    for method, path in (
        ("post", "/api/v1/jokes"),
        ("put", "/api/v1/jokes/0"),
        ("delete", "/api/v1/jokes/0"),
    ):
        response = getattr(client, method)(path, json={"author": "Ada", "joke": "x"})
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate", "").startswith("Basic")
        _assert_problem(response, 401)


def test_wrong_basic_auth_is_rejected(client: Any) -> None:
    response = client.post(
        "/api/v1/jokes",
        json={"author": "Ada", "joke": "x"},
        headers={"Authorization": _auth_header(password="wrong-password")},
    )

    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate", "").startswith("Basic")


def test_create_returns_201_location_and_server_generated_id(client: Any) -> None:
    response = _create(client, author="Katherine", joke="created once")

    assert response.status_code == 201, response.data
    assert response.content_type == "application/json"
    payload = _json(response)
    assert payload["author"] == "Katherine"
    assert payload["joke"] == "created once"
    assert isinstance(payload["id"], int)
    assert "Location" in response.headers
    assert response.headers["Location"].endswith(f"/api/v1/jokes/{payload['id']}")


def test_create_rejects_client_selected_id(client: Any) -> None:
    response = client.post(
        "/api/v1/jokes",
        json={"id": 99, "author": "Ada", "joke": "x"},
        headers={"Authorization": _auth_header()},
    )

    _assert_problem(response, 422)


def test_put_replaces_resource_using_path_id_and_returns_200(client: Any) -> None:
    response = client.put(
        "/api/v1/jokes/0",
        json={"author": "Updated", "joke": "replacement", "source": "https://example.com"},
        headers={"Authorization": _auth_header()},
    )

    assert response.status_code == 200, response.data
    payload = _json(response)
    assert payload == {
        "id": 0,
        "author": "Updated",
        "joke": "replacement",
        "source": "https://example.com",
    }
    assert _json(client.get("/api/v1/jokes/0")) == payload


def test_put_does_not_accept_a_conflicting_body_id(client: Any) -> None:
    response = client.put(
        "/api/v1/jokes/0",
        json={"id": 99, "author": "Updated", "joke": "replacement"},
        headers={"Authorization": _auth_header()},
    )

    _assert_problem(response, 422)


def test_delete_returns_empty_204_and_removes_resource(client: Any) -> None:
    response = client.delete(
        "/api/v1/jokes/0",
        headers={"Authorization": _auth_header()},
    )

    assert response.status_code == 204
    assert response.data == b""
    assert response.get_data() == b""
    assert response.headers.get("Content-Type") in (None, "")
    _assert_problem(client.get("/api/v1/jokes/0"), 404)


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_resource_is_not_found(client: Any, method: str) -> None:
    kwargs: dict[str, Any] = {}
    if method in {"put", "delete"}:
        kwargs["headers"] = {"Authorization": _auth_header()}
    if method == "put":
        kwargs["json"] = {"author": "Ada", "joke": "missing"}

    response = getattr(client, method)("/api/v1/jokes/999999", **kwargs)
    _assert_problem(response, 404)


def test_app_factory_provides_isolated_in_memory_state(app: Any) -> None:
    from legacy.fixed_flask_api.app import create_app

    first = app.test_client()
    created = _create(first, author="Isolated", joke="only in first app")
    assert created.status_code == 201
    created_id = _json(created)["id"]
    assert first.get(f"/api/v1/jokes/{created_id}").status_code == 200

    second = create_app(
        {
            "TESTING": True,
            "BASIC_AUTH_USERNAME": USERNAME,
            "BASIC_AUTH_PASSWORD_HASH": generate_password_hash(PASSWORD, method="scrypt"),
            "BASIC_AUTH_PASSWORD": PASSWORD,
            "AUTH_USERNAME": USERNAME,
            "AUTH_PASSWORD": PASSWORD,
        }
    ).test_client()
    assert second.get(f"/api/v1/jokes/{created_id}").status_code == 404


def test_documented_route_methods_never_return_500(client: Any) -> None:
    requests = [
        ("GET", "/health/live", {}),
        ("GET", "/api/v1/jokes", {}),
        ("GET", "/api/v1/jokes/random", {}),
        ("GET", "/api/v1/jokes/0", {}),
        (
            "POST",
            "/api/v1/jokes",
            {"json": {"author": "Ada", "joke": "x"}, "headers": {"Authorization": _auth_header()}},
        ),
        (
            "PUT",
            "/api/v1/jokes/0",
            {"json": {"author": "Ada", "joke": "x"}, "headers": {"Authorization": _auth_header()}},
        ),
        ("DELETE", "/api/v1/jokes/0", {"headers": {"Authorization": _auth_header()}}),
        ("POST", "/health/live", {}),
        ("PUT", "/health/live", {}),
        ("DELETE", "/health/live", {}),
        ("POST", "/api/v1/jokes/0", {"json": {}, "headers": {"Authorization": _auth_header()}}),
    ]

    for method, path, kwargs in requests:
        response = client.open(path, method=method, **kwargs)
        assert response.status_code != 500, f"{method} {path}: {response.data!r}"
