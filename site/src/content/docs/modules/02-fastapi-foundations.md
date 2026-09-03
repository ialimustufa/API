---
title: "Module 2: FastAPI foundations"
description: Implement typed HTTP boundaries and generated API documentation.
---

FastAPI turns Python type information and Pydantic models into request validation, response
serialization, and an OpenAPI document. The framework is the transport layer—not the business
model. Keep route functions small and move permission and state-transition rules into services.

## Start a minimal API

Install the frozen project environment and run TaskBox:

```bash
uv sync --all-groups --frozen
uv run uvicorn taskbox.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. FastAPI generates this interface from the same route and schema
definitions used at runtime.

## Request and response models

A request model defines what a caller may send. A response model defines what the API promises to
return. They should usually be different: a registration request accepts a password, while the
user response must never expose `password_hash`.

```python
class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=120)

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    status: UserStatus
```

Validation at the boundary prevents malformed data from reaching application logic. TaskBox
translates FastAPI validation failures into the same RFC 9457 structure used for domain errors.

## Dependency injection

Dependencies resolve authentication and application services. Protected routes depend on
`current_user`; the dependency verifies the Bearer token and loads an active user. Routes then pass
that user ID to a service that enforces project membership and role rules.

```python
@router.get("/projects")
def list_projects(
    user: User = Depends(current_user),
    svc=Depends(services),
):
    return svc.projects.list(actor_id=user.id)
```

This boundary makes policy explicit and allows tests to construct an app with an isolated database
and secrets.

## Application factory

`taskbox.main.create_app()` is the composition root. It wires database repositories, password
hashing, JWT handling, webhook verification, routes, and error handlers. Production uses the
module-level `app`; tests call the factory with `sqlite:///:memory:` and dedicated secrets.

## Lab

Work through `course/labs/02-fastapi-basics/README.md`. Implement the starter greeting and echo
routes, then compare with the solution. Inspect `/openapi.json` and answer:

1. Which validation constraints appear in the schema?
2. What happens when a required field is absent?
3. Which internal fields are excluded by the response model?

Finish by adding one bounded query parameter and testing both its accepted and rejected values.
