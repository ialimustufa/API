---
title: PostgreSQL with Docker
description: Move the API to PostgreSQL in the repeatable course lab.
---

This page describes the **PostgreSQL transition lab only**. It is not required for the SQLite-first workflow. The lab lives at `course/labs/07-operations/` (the course's Lab 07) and uses its own Compose file, API port, and database service. Complete SQLite first so changing storage is an infrastructure exercise rather than a domain rewrite.

## Lab 07 workflow

From the repository root, inspect and start the lab stack:

```bash
cd course/labs/07-operations
docker compose config
docker compose up --build
```

The lab starts `db` from `postgres:16-alpine`, waits for its `pg_isready` health check, then starts `api`. The API listens on port 8000 internally and is published at `http://127.0.0.1:8007`. Its container-to-container URL is `postgresql+psycopg://taskbox:taskbox-dev-only@db:5432/taskbox`; `db` is the Compose service name, not `localhost`.

In a second terminal:

```bash
curl -i http://127.0.0.1:8007/healthz
curl -i http://127.0.0.1:8007/readyz
curl http://127.0.0.1:8007/docs
docker compose ps
docker compose logs --tail=100 db api
```

Stop with `Ctrl-C`, or use `docker compose down`. This lab declares no database volume, so `down` removes containers and their writable database state. Treat it as disposable training data.

## Root Compose is different

The root `compose.yaml` is a local SQLite container workflow, not Lab 07's PostgreSQL stack:

```bash
cd /path/to/API
docker compose up --build
```

It starts only `app`, publishes `http://127.0.0.1:8000`, sets `TASKBOX_DATABASE_URL=sqlite:////data/taskbox.db`, and stores the file in the named `taskbox_data` volume. It does not start PostgreSQL, use port 8007, or run the lab Compose file. `docker compose down -v` removes that named volume and its SQLite data; use it only intentionally.

## Migration thinking

Use a reviewed, versioned PostgreSQL schema-change process before traffic. The reference app's SQLite bootstrap DDL is not a deployable migration history and must not be copied into PostgreSQL as a deployment step. Apply the schema change, verify constraints and indexes, then start the app: database reachable → schema change succeeds → API starts → readiness passes.

The initial SQL uses portable `TEXT` for UUID strings and ISO-8601 UTC timestamps, keeping domain behavior comparable. Still check engine-specific behavior: foreign-key enforcement, uniqueness, transaction isolation, timestamp ordering, and cursor query plans. Compatibility means preserving the application contract, not pretending engines are identical.

## Exercises

1. Run `docker compose config` and annotate the dependency graph. Why does `depends_on` use `condition: service_healthy`?
2. Break the password or host in `TASKBOX_DATABASE_URL`, restart the API, and distinguish DNS, authentication, and schema failures from logs.
3. Apply the schema, register a user, create a project and task, then restart only the API. Confirm rows remain while `db` runs.
4. Compare cursor-paginated task queries in SQLite and PostgreSQL. Keep route responses, authorization, and cursor shape unchanged.
5. Interrupt a multi-write operation and inspect for partial state. Write a rollback and retry note.

## Troubleshooting

**`Connection refused`.** Check `docker compose ps` and wait for `db` to become healthy. Startup ordering cannot repair a failed health check.

**The app tries `localhost:5432`.** Inside Compose, use host `db`; localhost is the API container itself.

**Wrong service or port.** Run Lab 07 commands in `course/labs/07-operations/`. Root Compose intentionally uses service `app` and port 8000.

**Data disappeared.** Lab 07 has no persistent volume. Root Compose data is in `taskbox_data`; avoid `down -v` unless deletion is intentional.

**Readiness fails.** Inspect API logs, verify URL and credentials, and confirm the expected schema is present in database `taskbox`. Process health does not prove dependency readiness.

## Outcome

You can explain the SQLite-to-PostgreSQL seam, bring up the correct Lab 07 stack, diagnose startup/readiness failures, apply schema before traffic, and preserve TaskBox routes while changing databases. Documentation links begin at `/` locally; deployed GitHub Pages uses `/API/`.
