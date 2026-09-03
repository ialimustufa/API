# Lab 03: CRUD with an in-memory repository

Implement the four basic operations for notes. This deliberately uses an
in-memory dictionary so the focus stays on HTTP semantics; the TaskBox project
later replaces this repository with SQLite and then PostgreSQL.

Run with `uv run uvicorn solution.app:app --reload`. Explore the generated
docs at `/docs`. The starter is intentionally incomplete. A missing note must
return 404, creation 201, replacement 200, and deletion 204. `PUT` is
replace-only rather than an upsert, so replacing a missing note returns 404.
