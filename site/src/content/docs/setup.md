---
title: Environment setup
description: Install the tools and establish a reliable local workflow for the course.
---

## Prerequisites

Use Python 3.13 (supported range `>=3.13,<3.15`) and `uv` for the API. Use Node 24 LTS and npm for the documentation site. Docker Desktop or another Docker Engine is needed only for the separate PostgreSQL transition lab.

```bash
python --version
uv --version
node --version
npm --version
docker --version
docker compose version
```

## API setup from the repository root

All commands assume the repository root, containing `pyproject.toml`, `uv.lock`, and `src/`:

```bash
uv sync --all-groups --frozen
cp .env.example .env       # optional; never commit real secrets
uv run uvicorn taskbox.main:app --reload
```

The frozen sync installs locked course dependencies and development tools. The server is local at `http://127.0.0.1:8000`; OpenAPI is `/docs`, process health is `/healthz`, and dependency readiness is `/readyz`. Stop it with `Ctrl-C`.

The default database is a durable SQLite file. Set `TASKBOX_DATABASE_URL` for an isolated file:

```bash
TASKBOX_DATABASE_URL=sqlite:///./tmp/setup-check.db \
  uv run uvicorn taskbox.main:app --reload --port 8010
```

## Verify the first feedback loop

In another terminal:

```bash
curl -i http://127.0.0.1:8000/healthz
curl -i http://127.0.0.1:8000/readyz
curl http://127.0.0.1:8000/openapi.json > /tmp/taskbox-openapi.json
uv run pytest
```

Then register a user and exercise the route examples in the TaskBox chapters. Restart the server and confirm SQLite data remains. For clean state, remove only a disposable lesson database you intentionally created.

## Begin the course

After setup, complete [Prerequisite 00: Postman foundations](../modules/00-postman-prerequisite/) and its practical lab at `course/labs/00-postman-prerequisite/README.md`. It is a required three-hour part of the course and must appear before Lab 01. Use the local file-backed `TaskBox API` collection under `postman/collections/TaskBox API/`; do not create a duplicate collection.

## Reference material

Work through the prerequisite and numbered course modules in order. When you need implementation details for the course application, start with the [TaskBox API domain and routes](../taskbox/domain-and-routes/), then use the neighboring reference pages for authentication, project roles, cursor pagination, and signed webhooks.

For storage guidance, begin with [SQLite-first persistence](../persistence/sqlite-first/). Use [PostgreSQL with Docker](../persistence/postgresql/) when you reach the database transition lab.

## Documentation site

The site is in `site/`. Keep the committed npm lockfile in sync:

```bash
cd site
npm ci
npm run dev
```

Open `http://localhost:4321/`. Use relative links for internal documentation routes. For example, `./setup/` from the home page resolves to `/setup/` locally and `/API/setup/` in production. Avoid both root-absolute `/setup/` links and hard-coded `/API/setup/` links so local preview and GitHub Pages use the same source.

Build before sharing documentation changes:

```bash
npm run build
```

## Optional Docker workflows

The root Compose file runs the SQLite-backed app and publishes port 8000:

```bash
cd /path/to/API
docker compose up --build
```

It stores `/data/taskbox.db` in named volume `taskbox_data`. The PostgreSQL workflow is separate: use `course/labs/07-operations/` and its Compose file, which publishes port 8007. See the persistence chapters before switching between them.

## Troubleshooting setup

**`uv sync --frozen` fails.** Confirm Python 3.13 is selected; do not edit the lockfile to bypass an incompatible interpreter.

**Port 8000 or 4321 is busy.** Stop the old process or choose a different development port.

**The API cannot import `taskbox`.** Run Uvicorn with `uv run` from the root, not from `site/` or a copied directory.

**The site has stale content.** Restart Astro after changing configuration, then run `npm run build` to surface broken links or frontmatter errors.

**Docker is unavailable.** SQLite development and the docs site do not require Docker; install/start it only for the PostgreSQL lab.

## Outcome

A correct setup installs from the frozen lockfile, runs and tests TaskBox on SQLite, previews and builds the docs, and distinguishes local `/` URLs from deployed `/API/` URLs.
