# Lab 07: Operations and deployment

Make failure visible and startup repeatable. Add `/healthz` (process health),
`/readyz` (dependency readiness), structured request IDs, and graceful shutdown.
Then run the provided Compose file with the API and PostgreSQL services.

```bash
uv run uvicorn solution.app:app --port 8007
docker compose up --build
```

The starter intentionally has empty probes and no request ID middleware.
Health endpoints should be cheap, authenticated business routes should not be
used as probes, and readiness must return a non-2xx response when the database
cannot be reached.
