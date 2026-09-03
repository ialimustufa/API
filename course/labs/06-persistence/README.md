# Lab 06: SQLite-first persistence

Replace process-local state with a durable SQLite repository. The solution
uses SQLAlchemy 2.0, creates a `tasks` table at startup, and keeps HTTP models
separate from database rows. Set `TASKBOX_DATABASE_URL` to a file path to
persist data between restarts.

```bash
uv run uvicorn solution.app:app --reload --port 8006
curl -X POST http://127.0.0.1:8006/api/v1/tasks -H 'content-type: application/json' -d '{"title":"write migration"}'
curl http://127.0.0.1:8006/api/v1/tasks
```

The starter leaves repository methods incomplete. Notice the transaction
boundary: commit writes, rollback is automatic on an exception, and reads do
not mutate state. In a production service, use a reviewed, version-controlled
schema-change process rather than `create_all`; this repository intentionally
ships no migration CLI or migration history.
