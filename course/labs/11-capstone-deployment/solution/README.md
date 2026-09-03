# TaskBox reference checklist

Configure `TASKBOX_DATABASE_URL`, `TASKBOX_JWT_SECRET`, and
`TASKBOX_WEBHOOK_SECRET`. Before deploy, run `uv run pytest`, `uv run ruff check
.`, apply migrations, and verify `/healthz` and `/readyz`. A complete capstone
returns 503 for a failed database probe, 401 for expired tokens, 403 for
unauthorized project access, and does not duplicate replayed webhook IDs.
