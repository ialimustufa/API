---
title: Environment setup
description: Install the tools used throughout the course.
---

## Prerequisites

Use Node 24 LTS and npm for the documentation site. The Python course baseline is Python 3.13 (supported range `>=3.13,<3.15`) managed with `uv`.

From the repository root, create the frozen Python environment and start TaskBox:

```bash
uv sync --all-groups --frozen
uv run uvicorn taskbox.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive OpenAPI UI. The liveness
and readiness probes are available at `/healthz` and `/readyz`.

The documentation site lives in `site/`. Use the committed lockfile:

```bash
cd site
npm ci
npm run dev
```

Open `http://localhost:4321/` locally. The production GitHub Pages build uses
the repository prefix, so it is served from `/API/` after deployment.
