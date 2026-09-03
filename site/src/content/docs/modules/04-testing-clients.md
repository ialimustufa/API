---
title: "Module 4: Testing APIs and clients"
description: Verify behavior at domain, HTTP, contract, and deployment boundaries.
---

An API test suite should prove more than “the route returned 200.” It must cover rules clients rely
on: authentication challenges, permission boundaries, response schemas, transaction behavior,
idempotency, and failure media types.

## A practical test pyramid

- **Unit tests** exercise domain validation and service policy without HTTP.
- **API tests** send requests through FastAPI with an isolated database.
- **Contract tests** compare generated routes with the committed OpenAPI artifact.
- **Integration tests** verify complete workflows across authentication, persistence, and adapters.
- **Smoke tests** run against the built container after deployment.

Run the repository gates from the root:

```bash
uv run pytest
uv run ruff check .
uv run python scripts/validate_course_map.py
uv run python scripts/check_openapi_contract.py
```

The TaskBox workflow test registers an owner and viewer, obtains JWTs, creates a project, verifies
that a viewer cannot write, creates and updates a task as the owner, lists it as the viewer, imports
a signed webhook, and rejects a duplicate event.

## Isolate state

Tests call `create_app(database_url="sqlite:///:memory:", ...)`. Each test supplies non-production
JWT and webhook secrets. This keeps tests deterministic and prevents local `taskbox.db` state from
changing assertions.

## Test errors as carefully as success

For a forbidden request, assert the status, content type, and stable code:

```python
assert response.status_code == 403
assert response.headers["content-type"].startswith("application/problem+json")
assert response.json()["code"] == "forbidden"
```

Avoid exact assertions on timestamps, generated UUIDs, or full human-readable sentences unless
those values are truly contractual.

## Client behavior

A good client sets timeouts, checks status before decoding success data, and treats network errors
differently from API errors. It must never log Bearer tokens or passwords. Retry only operations
that are safe or protected by an idempotency key, and use bounded exponential backoff.

## Lab

Use `course/labs/04-testing-client-usage/README.md`. Complete the starter test before consulting the
solution. Run the example client, then deliberately request an unknown resource and improve the
client's error output. Finally, add one regression test for a bug you could imagine shipping.
