---
title: "Module 11: Capstone and deployment"
description: Combine the TaskBox contracts into a production rehearsal.
---

The capstone is a rehearsal, not a feature pile. Assemble the contracts from the course into one TaskBox service and prove that its behavior remains safe under restart, retries, missing dependencies, and unauthorized access. A deployment is successful when the system is understandable and recoverable, not merely when a container starts.

## Learning objectives

By completion you should be able to:

- integrate JWT identity, project-scoped roles, repositories, pagination, and signed imports;
- write route-level contract and smoke tests;
- document a threat model, migration and rollback plan, and incident response;
- deploy with external secrets and dependency-gated readiness.

## Compose the boundaries

Start from the domain and route contracts: authenticated users can access only permitted projects; owners, editors, and viewers have explicit capabilities; task lists use deterministic cursor pagination; and webhook imports require a valid signature and stable event ID. Keep repository code behind an interface so the same behavior works with the SQLite file used locally and PostgreSQL used in deployment.

Add the operational boundary around those features. `/healthz` reports process liveness, `/readyz` reports database readiness, request IDs connect responses to structured logs, and graceful shutdown closes work cleanly. Do not hide migrations or long-running imports in a health probe.

## Threat model

Write down assets, actors, trust boundaries, and abuse cases before testing. Assets include passwords, JWT signing keys, project data, webhook secrets, and event side effects. Consider credential stuffing, token forgery, project-ID enumeration, SQL injection, replayed webhooks, oversized requests, and a compromised dependency. For every threat, name a control and a test: Argon2 and vague login errors for password guessing; fixed JWT algorithms and expiry checks for forgery; membership checks for cross-project access; raw-body HMAC plus event deduplication for webhook replay.

## Migration and rollback

The release sequence should be explicit:

```text
build -> backup/check -> migrate -> start -> readiness -> smoke test -> traffic
```

Run reviewed Alembic migrations before application traffic. Prefer additive, backward-compatible schema changes when old and new instances overlap. Define the rollback condition, who makes the decision, and whether rollback means reverting code, restoring data, or applying a compensating migration. A backup is useful only if restoration has been rehearsed.

## Verification checklist

Run the capstone from its lab directory and use the PostgreSQL Compose rehearsal from Lab 07:

```bash
cd course/labs/11-capstone-deployment
uv run pytest
cd ../07-operations
docker compose up --build
```

The [Lab 11 README and acceptance checklist](https://github.com/ialimustufa/API/tree/main/course/labs/11-capstone-deployment) require a contract test for every route, a failure mode and recovery action, an architecture diagram, a threat model, a migration command, a rollback plan, and a curl smoke test. Verify at minimum:

- missing, expired, and wrongly signed JWTs return `401`, while insufficient roles return `403`;
- data survives restart and pagination order is deterministic;
- invalid and stale webhooks are rejected, while valid retries do not duplicate work;
- readiness fails when PostgreSQL is unavailable and recovers afterward;
- secrets are environment-provided and absent from logs and images.

Exercise: kill the database during a write, restart the API, send the same webhook twice, and deploy a schema change while a previous process is still running. Capture the observed request IDs and statuses in the runbook.

## Pitfalls and handoff

Avoid a “works on my laptop” deployment that uses SQLite accidentally, bakes secrets into an image, starts traffic before migrations, or treats a 200 health response as proof of database readiness. Avoid tests that assert only successful bodies; status codes, headers, error types, ordering, and idempotency are contracts too.

Your final deliverable should let another engineer operate the service without asking how it was built: include the architecture diagram, environment variable list, migration and rollback commands, probe semantics, smoke-test commands, and one-page incident runbook. Re-run the repository’s required checks—`pytest`, `ruff`, OpenAPI contract checks, `astro-check`, and `astro-build`—before considering the course complete.

You have now connected the security, persistence, protocol, realtime, webhook, and operations lessons into one maintainable API.
