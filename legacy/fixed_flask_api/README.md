# Corrected Flask jokes API

This is the repaired, dependency-light Flask 3.1 example that replaces the
original notebook's HTTP behavior. It is intentionally kept separate from the
archived notebook in `legacy/original/`.

## Run

Install Flask 3.1 in your environment, then from the repository root:

```bash
flask --app legacy.fixed_flask_api.app:create_app run --debug
```

Writes use HTTP Basic Auth. Configure a Werkzeug password hash (never commit a
password):

```bash
export LEGACY_API_USERNAME=course-admin
export LEGACY_API_PASSWORD_HASH='scrypt:32768:8:1$...'
```

The app stores records in memory; restarting it resets the sample data. Seed
record `id=0` is deliberate so clients can verify that zero is treated as a
valid identifier.

## Routes

- `GET /health/live`
- `GET /api/v1/jokes?page=1&page_size=20&author=...&q=...`
- `GET /api/v1/jokes/random`
- `GET /api/v1/jokes/{id}`
- `POST /api/v1/jokes` (Basic Auth, returns `201` and `Location`)
- `PUT /api/v1/jokes/{id}` (Basic Auth, full replacement)
- `DELETE /api/v1/jokes/{id}` (Basic Auth, empty `204`)

Errors follow RFC 9457 Problem Details using `application/problem+json`.
Basic Auth is suitable for this localhost teaching example only; use TLS and a
proper identity system in production.
