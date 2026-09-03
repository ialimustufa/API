# API Engineering Course

This repository is a beginner-to-production course for designing, building, testing, and operating APIs.

The new course uses Python, FastAPI, SQLite, and a TaskBox capstone. It includes runnable labs, generated OpenAPI contracts, authentication, webhooks, observability, and deployment exercises.

## Start here

1. Install Python 3.13+, Node 24 LTS, and `uv`.
2. Run `uv sync --all-groups --frozen`.
3. Start TaskBox with `uv run uvicorn taskbox.main:app --reload`.
4. Open the API docs at `http://127.0.0.1:8000/docs`.
5. Follow the 40-hour sequence in [`course/course-map.yml`](course/course-map.yml).
6. Start the course site with `cd site && npm ci && npm run dev`.

Local site routes start at `http://localhost:4321/`. The GitHub Pages build uses
`/API/`, so the deployed setup page is `https://ialimustufa.github.io/API/setup/`.

## Verify everything

```bash
uv run pytest
uv run ruff check .
uv run python scripts/validate_course_map.py
uv run python scripts/check_openapi_contract.py
cd site
npm ci
npm run check
npm run build
```

## Run with Docker

The root Compose stack deploys the SQLite-first TaskBox API with a persistent
Docker volume:

```bash
docker compose up --build
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

Set `TASKBOX_JWT_SECRET` and `TASKBOX_WEBHOOK_SECRET` to long random values in
`.env` before exposing the API. The PostgreSQL transition is a separate required
exercise in [`course/labs/07-operations`](course/labs/07-operations/).

## License

Authored course and application code is MIT licensed. Historical third-party material retains its original provenance; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Legacy

The original course materials are preserved under [`legacy/`](legacy/).
