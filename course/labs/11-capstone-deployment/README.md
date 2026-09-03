# Lab 11: TaskBox capstone and deployment

Assemble the course: JWT authentication, project roles, SQLite/PostgreSQL
repositories, cursor pagination, signed webhook imports, health probes, and
observability. Write an API contract test for every route and document one
failure mode and recovery action.

Acceptance checklist: migrations run before traffic, secrets are environment-
provided, readiness checks dependencies, webhook retries are idempotent, and
pagination order is deterministic. Use the Compose file from Lab 07 for the
PostgreSQL deployment rehearsal. Submit an architecture diagram, threat model,
migration command, rollback plan, and curl smoke test.
