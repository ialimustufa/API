---
title: "Module 7: Operations"
description: Make health, failure, and deployment behavior observable.
---

An API is not production-ready merely because its happy path works. Operators need to know whether a process is alive, whether it can serve real traffic, which request failed, and whether shutdown completed without losing work. This module turns those questions into small, testable contracts.

## Learning objectives

You will be able to:

- separate liveness from dependency readiness;
- propagate request IDs and emit useful structured logs;
- shut down gracefully and make Compose wait for PostgreSQL;
- rehearse a failed dependency and recover without guesswork.

## Probes mean different things

`GET /healthz` is liveness: the process and event loop are responsive. It should be cheap and should not require a database. A process that answers liveness but cannot reach its database is still not ready for user traffic. `GET /readyz` checks the dependencies required to serve requests and returns a non-2xx response—normally `503`—when they are unavailable. Kubernetes or another supervisor can restart an unhealthy process based on liveness and remove an unready one from service.

Never use an authenticated business route as a probe. Its schema, permissions, and latency can change independently of process health. Keep probe responses small and avoid returning connection strings or exception details.

## Request IDs and logs

Middleware should accept a client `X-Request-ID` when it is valid and bounded, or generate a new opaque ID. Return it on every response. Include it in structured log records together with method, path, status, duration, and a safe error category:

```python
started = time.perf_counter()
request_id = incoming_id() or secrets.token_hex(16)
response = await call_next(request)
response.headers["X-Request-ID"] = request_id
logger.info("request.complete", extra={
    "request_id": request_id, "status": response.status_code,
    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
})
```

Use JSON logs in deployment so a collector can filter by request ID. Redact Authorization headers, cookies, passwords, signing secrets, and full webhook bodies. A request ID is for correlation, not authentication.

## Startup, shutdown, and configuration

Runtime configuration supplies the database URL, JWT secret, and other secrets. Validate required values at startup and keep safe defaults limited to local development. A graceful shutdown stops accepting new work, lets in-flight requests finish within a deadline, closes database pools, and then exits. Make timeout behavior explicit: work that cannot finish should be retried safely by its caller or queue.

The provided Compose file demonstrates a dependency-aware startup. PostgreSQL has a healthcheck; the API waits for the database to become healthy before starting. This avoids a race, but readiness must still test the live dependency because a healthy database can fail later. Use schema changes as a separate, observable release step rather than hiding schema creation in application startup. The SQLite reference app bootstraps a local development file from reference DDL; it has no versioned migration CLI or migration history.

## Practice and verification

Run the solution locally:

```bash
cd course/labs/07-operations
uv run uvicorn solution.app:app --port 8007
curl -i http://127.0.0.1:8007/healthz
curl -i http://127.0.0.1:8007/readyz
docker compose up --build
```

Inspect both status codes and headers. Send a request with a known request ID and confirm it is echoed in the response and logs; omit it and confirm one is generated. Stop PostgreSQL or provide an invalid database URL, then verify liveness remains distinct while readiness becomes `503`. Restore the dependency and verify readiness recovers. The [Lab 07 README, solution, and Compose file](https://github.com/ialimustufa/API/tree/main/course/labs/07-operations) define the expected rehearsal.

Exercise: add a bounded shutdown timeout, a test for dependency failure, and a log assertion that proves tokens are not emitted. Document which alert should page an operator and which condition should only remove an instance from traffic.

## Pitfalls and next steps

Do not report `200` readiness after catching every database exception, let logs grow without rotation, or make health checks perform expensive migrations. Also avoid exposing stack traces to clients: preserve details in controlled logs and return a stable problem response.

Next, compare alternative protocol boundaries in [Module 8: GraphQL and gRPC](../08-graphql-grpc/).
