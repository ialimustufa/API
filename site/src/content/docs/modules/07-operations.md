---
title: "Module 7: Operations"
description: Make health, failure, and deployment behavior observable.
---

Separate liveness (`/healthz`) from readiness (`/readyz`). Liveness answers whether the process can serve; readiness checks dependencies and returns `503` when traffic should stop. Propagate an `X-Request-ID`, emit structured logs with duration and status, and shut down gracefully. Compose healthchecks must gate API startup on database readiness. Secrets and database URLs are runtime configuration.

Run [Lab 07](/labs/07-operations/) locally and rehearse the PostgreSQL startup failure.
