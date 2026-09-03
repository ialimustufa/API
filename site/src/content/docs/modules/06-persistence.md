---
title: "Module 6: Durable persistence"
description: Start with SQLite and keep the repository portable.
---

An in-memory list is useful while learning HTTP, but it disappears on restart and cannot coordinate multiple workers. This module introduces a durable boundary without coupling TaskBox’s domain to one database vendor. SQLite is the first feedback loop; PostgreSQL is the deployment target.

## Learning objectives

You will learn to:

- map domain objects to SQLAlchemy 2.0 rows without leaking ORM details into handlers;
- define transaction and rollback behavior explicitly;
- enforce uniqueness and foreign keys in the database;
- move from a SQLite file to PostgreSQL through configuration and migrations.

## Repository boundary

The route should parse an HTTP request, call a repository or service, and serialize a response. It should not build SQL statements or return an ORM object directly. A repository can expose operations such as `create_task`, `get_task`, and `list_tasks`; its implementation owns sessions, query construction, and row-to-domain mapping. This boundary keeps a future PostgreSQL driver change out of the API contract.

The Lab 06 solution stores tasks in a `tasks` table and keeps HTTP models separate from rows. A file URL such as `sqlite:///./taskbox.db` makes state visible between process restarts. Enable SQLite foreign keys on each connection and use a separate session per request. Reads must not commit or mutate state.

## Transactions are behavior

A write has a clear unit of work: validate input, add or update rows, commit once, and return the committed representation. If any step raises, roll back before the session is reused. A uniqueness violation should become a stable API conflict rather than a half-written object. The important shape is:

```python
def create_task(session: Session, data: TaskCreate) -> Task:
    row = TaskRow(title=data.title)
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DuplicateTask()
    session.refresh(row)
    return to_domain(row)
```

Do not treat `create_all` as a migration system. It cannot describe renames, data backfills, or rollback intent. In production, generate and review Alembic revisions, run them as a release step before traffic, and record the schema version. Design migrations to be compatible with the code versions that may overlap during rollout.

## SQLite first, PostgreSQL next

SQLite has no service bootstrap and is ideal for local tests, but its locking and concurrency model differ from PostgreSQL. PostgreSQL provides stronger multi-process concurrency and production-oriented operational features. The domain behavior should remain unchanged when only `TASKBOX_DATABASE_URL` changes. Use a PostgreSQL URL supplied by environment configuration; never hard-code credentials in source or Compose files.

Check types and queries for portability. Avoid relying on SQLite’s permissive typing, implicit ordering, or a transaction behavior that PostgreSQL does not share. Every list query needs an explicit order. For cursor pagination, order by a stable tuple such as `(created_at, id)` and index the columns used by the filter.

## Practice and verification

Run the lab from its directory:

```bash
cd course/labs/06-persistence
uv run uvicorn solution.app:app --reload --port 8006
curl -X POST http://127.0.0.1:8006/api/v1/tasks \
  -H 'content-type: application/json' -d '{"title":"write migration"}'
curl http://127.0.0.1:8006/api/v1/tasks
```

Restart the server and confirm the task remains. Test duplicate data, a failed write followed by a successful write, invalid foreign keys, and two updates to the same row. Inspect the database schema rather than assuming model declarations produced the desired constraints. The [Lab 06 README and source](https://github.com/ialimustufa/API/tree/main/course/labs/06-persistence) identify the intentionally incomplete starter methods.

Exercise: add a `completed` field through a reviewed migration, backfill existing rows, and prove that old data remains readable. Then point the app at PostgreSQL during the Lab 07 Compose rehearsal and run the same API contract tests.

## Pitfalls and next steps

Frequent errors include one global session, committing inside a read, swallowing rollback errors, relying on `create_all` in production, and forgetting indexes or deterministic ordering. Treat database errors as data and operational signals: log a request ID and safe error category, not SQL containing secrets.

Next, read [Module 7: Operations](../07-operations/) to make database failure visible to orchestration and operators.
