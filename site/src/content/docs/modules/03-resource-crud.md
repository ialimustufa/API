---
title: "Module 3: Resource-oriented CRUD"
description: Build predictable resource lifecycles and state transitions.
---

CRUD is simple only when its contract is vague. Production APIs must define who chooses IDs, which
fields are mutable, how missing resources behave, and whether concurrent updates can overwrite one
another.

## Create

TaskBox creates projects under the authenticated user and automatically creates an owner
membership. The server assigns UUIDs and timestamps. A client submits only writable fields:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"API course","description":"Track course work"}'
```

Creation is a transaction: the project and owner membership must both persist, or neither should.

## Read and list

An item route returns one representation. A collection returns an envelope so pagination metadata
can evolve without changing the top-level type:

```json
{
  "items": [{"id": "...", "name": "API course"}],
  "next_cursor": null
}
```

Project reads are membership-scoped. Avoid leaking whether a private project exists to users who
should not know about it; choose and document a consistent `403` or `404` policy.

## Update

TaskBox uses `PATCH` for partial updates. It distinguishes a field omitted from the request from a
field explicitly set to `null`. Pydantic's `model_fields_set` preserves that distinction.

Validate the result after applying changes. A model that was valid when loaded can become invalid
after mutation—for example, a name containing only spaces.

## Delete

A successful delete returns `204` with an empty body. Database foreign-key rules determine what
happens to memberships and tasks. Destructive behavior must be documented and tested; production
systems may choose soft deletion when audit or recovery requirements demand it.

## Authorization matrix

| Operation | Owner | Editor | Viewer |
| --- | ---: | ---: | ---: |
| Read project/tasks | ✓ | ✓ | ✓ |
| Create/update tasks | ✓ | ✓ | — |
| Update project | ✓ | — | — |
| Manage members | ✓ | — | — |
| Delete project | ✓ | — | — |

The service layer owns these checks so an alternative transport cannot bypass them.

## Lab

Complete `course/labs/03-crud/README.md`. Test the happy path and at least these failures: malformed
input, unknown ID, duplicate value, forbidden role, and empty `204` response. Then trace one request
from FastAPI route to application service, repository, SQLite transaction, and serialized response.
