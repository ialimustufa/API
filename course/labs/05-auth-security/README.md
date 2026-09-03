# Lab 05: Authentication and security

Add a small security boundary before adding more resources. The solution issues
short-lived JWT access tokens, hashes passwords with Argon2, validates the
`Bearer` scheme, and applies a simple per-client rate limit. Secrets come from
environment variables; never commit a real signing key.

```bash
uv run uvicorn solution.app:app --reload --port 8005
curl -X POST http://127.0.0.1:8005/api/v1/auth/token \
  -H 'content-type: application/json' -d '{"username":"ada","password":"correct horse"}'
curl http://127.0.0.1:8005/api/v1/me -H "authorization: Bearer TOKEN"
```

Implement the TODOs in `starter/app.py`: password verification, token claims,
expiry handling, and the dependency that identifies the current user. Keep
authentication failures deliberately vague (401, `WWW-Authenticate: Bearer`)
so they do not disclose whether an account exists.
