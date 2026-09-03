---
title: SQLite first
description: Build and inspect a durable local TaskBox database before adding a database service.
---

SQLite is TaskBox's first persistence target because it shortens the feedback loop: there is no server to install, the database is one file, and data survives an application restart. “First” does not mean “throwaway”. The same repository ports, transaction boundaries, constraints, and cursor ordering should remain meaningful when the PostgreSQL lab changes only the adapter and connection URL.

## Local workflow

Run from the repository root (the directory containing `pyproject.toml`):

```bash
uv sync --all-groups --frozen
cp .env.example .env             # optional; inspect and edit local values
uv run uvicorn taskbox.main:app --reload
```

The default local URL is `sqlite:///taskbox.db` (or `TASKBOX_DATABASE_URL`). With `sqlite:///./taskbox.db`, the file is relative to the process working directory. Start from the repository root if you want `./taskbox.db`; launching elsewhere can create a second database. Use `http://127.0.0.1:8000`, inspect `http://127.0.0.1:8000/docs`, create data through the authenticated routes, restart Uvicorn, and verify the rows remain.

For an isolated exercise database:

```bash
TASKBOX_DATABASE_URL=sqlite:///./tmp/lesson.db \
  uv run uvicorn taskbox.main:app --reload --port 8010
```

The adapter creates parent directories for a file URL and enables foreign-key enforcement. `sqlite:///:memory:` is useful for a short test, but is ephemeral and process-local.

## Persistence boundary

HTTP models and domain objects should not know whether a row came from SQLite or PostgreSQL. Application services depend on repository protocols in `src/taskbox/ports/repositories.py`; the SQLite adapter implements those protocols.

- Repositories translate rows to domain objects and back.
- Services enforce authorization and business rules.
- A `UnitOfWork` groups changes that must commit or roll back together.
- List methods return an opaque cursor page, not database-specific offsets.

This gives the course a concrete test: changing the persistence adapter must not change route semantics or project-role behavior.

## Schema, constraints, and migrations

The local adapter executes its embedded schema on startup with `CREATE TABLE IF NOT EXISTS`. That is convenient reference-app bootstrap, not a migration history. The portable schema is also checked in as `migrations/001_initial.sql`; it defines users, projects, memberships, tasks, webhook receipts, foreign keys, uniqueness, status checks, and cursor indexes. Read both when changing persistence so the adapter stays aligned with the migration source.

For a real schema change, write a forward migration rather than editing an existing migration or relying on `create_all`. Plan old and new shapes, backfill existing rows, add constraints after data is valid, and document rollback (or why it is irreversible). Apply it to a disposable copy first and test both empty and populated databases.

## Transactions and failure behavior

Use a unit of work around a multi-write operation. Normal exit commits; an exception rolls back. A failed task creation must not leave a task without its project relationship, and webhook import must not process the same event twice. Reads should not mutate state. SQLite serializes the adapter's critical section, but that does not remove the need for a clear commit boundary.

```bash
sqlite3 taskbox.db '.tables'
sqlite3 taskbox.db 'PRAGMA foreign_keys;'
sqlite3 taskbox.db 'SELECT id, title, status FROM tasks ORDER BY created_at, id;'
```

If `sqlite3` is unavailable, inspect with the Python standard library or repository tests. Make a copy before destructive exercises.

## Exercises

1. Create two tasks, restart Uvicorn, and confirm both remain. Record the URL and file location.
2. Attempt a task with a missing project. Explain which foreign key protects the invariant.
3. Write an operation that creates a membership and related record in one unit of work. Force an exception between writes and prove neither row remains.
4. Map each index in `migrations/001_initial.sql` to a list query. Explain why `(created_at, id)` is a stable cursor tie-breaker.

The implementation exercise in `course/labs/06-persistence/` intentionally starts incomplete. Keep starter code incomplete when teaching; validate the solution against persistence, rollback, uniqueness, and cursor tests.

## Troubleshooting

**The API starts empty.** Check `TASKBOX_DATABASE_URL`, current directory, and whether `:memory:` was used. Print the resolved path before deleting anything.

**`database is locked`.** Stop duplicate dev servers, close inspection processes, and keep transactions short. Do not hold a unit of work open during an HTTP call.

**A foreign-key test passes unexpectedly.** Confirm the local adapter and connection-specific `PRAGMA foreign_keys` are active.

**A schema edit did not apply.** `IF NOT EXISTS` does not alter an existing table. Use a new migration/backfill on a copy, or recreate a disposable lesson database.

## Outcome

You can start TaskBox from a clean checkout, identify its SQLite file, survive a restart, explain repository and unit-of-work boundaries, and describe a forward migration that preserves data. Next is the separate PostgreSQL transition lab.
