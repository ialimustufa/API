---
title: "Module 1: HTTP and API design"
description: Turn product behavior into a predictable HTTP contract.
---

Complete [Prerequisite 00: Postman foundations](../00-postman-prerequisite/) before beginning this module.

An API is a contract between independently changing programs. Good API design starts before
framework code: identify the resources, decide which state transitions are allowed, and describe
the success and failure responses a client can depend on.

## Learning objectives

By the end of this module, you should be able to:

- model nouns as resources and actions as state changes;
- choose HTTP methods and status codes deliberately;
- distinguish safe, idempotent, and non-idempotent operations;
- design stable JSON representations and RFC 9457 error responses; and
- write an OpenAPI contract before implementing a server.

## Resources and routes

TaskBox has users, projects, memberships, tasks, and webhook receipts. Routes express ownership
and containment where it helps a client understand scope:

```text
POST   /api/v1/auth/register
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
POST   /api/v1/projects/{project_id}/tasks
PATCH  /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}
```

Use `POST` when the server assigns a new resource identifier, `GET` for a safe read, `PATCH` for a
partial update, and `DELETE` for removal. A successful create returns `201 Created`; a successful
delete returns `204 No Content` with no JSON body.

## Status codes are part of the contract

Clients should not need to parse prose to understand the result. TaskBox uses:

| Status | Meaning |
| --- | --- |
| `200` | Read or update succeeded |
| `201` | A resource was created |
| `202` | A webhook was accepted for processing |
| `204` | Deletion succeeded; no response body |
| `401` | Authentication is missing or invalid |
| `403` | The authenticated user lacks permission |
| `404` | The addressed resource does not exist |
| `409` | Current state conflicts with the request |
| `422` | The request shape or domain value is invalid |

Expected failures use `application/problem+json`. The stable `code` is for program logic; `detail`
is for humans:

```json
{
  "type": "http://127.0.0.1:8000/problems/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "your project role cannot perform this action",
  "instance": "http://localhost:8000/api/v1/projects/.../tasks",
  "code": "forbidden"
}
```

## Idempotency

Repeating a safe `GET` should not change state. `PUT` and `DELETE` are defined to be idempotent:
repeating the same operation has the same intended effect. `POST` normally is not idempotent, so
webhook imports use `X-Webhook-Event-ID` as an idempotency key. The server records an event before
performing side effects and rejects a replay with `409 duplicate_webhook`.

## Lab

Open `course/labs/01-http-api-design/README.md`. Complete the starter OpenAPI document, compare it
with the solution, and run the small standard-library server. Check that every response has a
documented status, media type, and schema.

Before continuing, explain why authentication failure is `401` while insufficient project role is
`403`, and why a deleted resource should not return `200` with an arbitrary message body.
