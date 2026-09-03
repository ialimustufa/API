---
title: Domain and routes
description: The TaskBox resource model and HTTP contract.
---

TaskBox is a small project-and-task API. Its public contract is deliberately boring: JSON in, JSON out, UUID identifiers, and predictable HTTP status codes. The application is mounted under `/api/v1`; liveness endpoints live at `/healthz` and `/livez`, while readiness is `/readyz`.

## The domain in one picture

Users own identities. A project has one owner and a membership row for every person who can see it. Tasks belong to a project and record both `created_by` and an optional `assignee_id`. The four task statuses are `todo`, `in_progress`, `done`, and `archived`. Project roles are `owner`, `editor`, and `viewer`.

This separation matters. A task does not grant access by itself: before reading a task, the service finds its project and checks the caller's membership. Creating or changing tasks requires `owner` or `editor`; viewing requires any membership. Project changes and membership changes are owner-only.

## Start the API and check it

From the repository root, run the development server with the project tooling:

```bash
uv run uvicorn taskbox.main:app --reload
curl -i http://127.0.0.1:8000/healthz
```

The health response is `{"status":"ok"}`. `/readyz` also executes `SELECT 1`, so it is the useful probe for whether the configured database can answer queries. Do not use a readiness check as proof that every dependency or migration is healthy in a larger deployment; add those checks at the composition root as the system grows.

## Register, create, and read

Registration requires an email, a password of at least eight characters, and a one-to-120-character display name:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada@example.com","password":"correct horse","display_name":"Ada"}'
```

The `201` response contains `id`, `email`, `display_name`, `status`, `created_at`, and `updated_at`. Email is normalized to lowercase. Exchange those credentials at `/api/v1/auth/token`, then use the returned token on protected routes:

```bash
TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada@example.com","password":"correct horse"}' | jq -r .access_token)
curl -sS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/me
curl -sS -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Release 1","description":"First milestone"}'
```

Project creation returns `201` and makes the caller both the owner and an owner membership. A project list is paginated (`items` plus `next_cursor`). Project reads, task reads, and all writes require a Bearer token.

## Route map and shapes

The core routes are:

| Area | Routes |
| --- | --- |
| Auth | `POST /auth/register`, `POST /auth/token`, `GET /me` |
| Projects | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{project_id}` |
| Members | `GET/POST /projects/{project_id}/members`, `PATCH/DELETE /projects/{project_id}/members/{user_id}` |
| Tasks | `GET/POST /projects/{project_id}/tasks`, `GET/PATCH/DELETE /tasks/{task_id}` |
| Import | `POST /webhooks/tasks/import` |

Task creation accepts `title` (1–240 characters), optional `description` (up to 10,000), `status`, `priority` (0–4), `assignee_id`, and `due_at`. A successful task response includes those values plus IDs and timestamps. `PATCH` is partial: only supplied fields change, and sending `description: null`, `assignee_id: null`, or `due_at: null` clears that field. Deletes return `204` with no body.

## Errors are part of the contract

Expected domain failures use RFC 9457-style `application/problem+json`. For example, an unauthenticated request returns `401` and a Bearer challenge:

```json
{"type":"https://taskbox.dev/problems/authentication_required","title":"Authentication Required","status":401,"detail":"authentication required","instance":"http://127.0.0.1:8000/api/v1/me","code":"authentication_required"}
```

Malformed JSON fields are `422` with an `errors` array; missing resources are `404`; insufficient membership or role is `403`; duplicate email or membership is `409`. Clients should branch on `code`, not scrape `detail` text.

## Checkpoint and pitfalls

Create a project, create one task with priority `2`, list it, patch it to `done`, and delete it. Verify status codes and confirm the delete response has an empty body. Then try the same task-create request as a viewer: it must be `403`. Common mistakes are using the old `/joke`-style paths, forgetting the `/api/v1` prefix, treating `204` as JSON, and assuming a project ID alone is authorization.

For production, set `TASKBOX_DATABASE_URL`, `TASKBOX_JWT_SECRET`, and `TASKBOX_WEBHOOK_SECRET` explicitly. The development defaults are convenient, but the default JWT secret is intentionally marked “dev-only” and must never protect a deployed service.

## A route-first debugging method

When a request fails, inspect the request in layers. A `404` from the web server may mean the path is wrong; a TaskBox `404` problem document means the route matched but a project, task, or membership was absent. A `422` means FastAPI rejected the body or query values before the use case ran. A `401` means the identity boundary failed, while a `403` means identity succeeded and project policy rejected the action. This classification makes `curl -i` and the problem `code` more useful than guessing from a generic status message.

For repeatable smoke tests, create a temporary SQLite database, register test users, capture IDs from responses, and pass those IDs into later commands. Avoid hard-coding UUIDs or relying on creation order. The same sequence can then run against the required PostgreSQL lab to expose adapter differences while preserving the HTTP contract.
