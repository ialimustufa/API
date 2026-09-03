---
title: Authentication
description: Issue and use JWT access tokens.
---

TaskBox uses two different protections: Argon2 password hashing for stored credentials and signed, short-lived JSON Web Tokens (JWTs) for API calls. Passwords are never returned or placed in a token. A client registers once, exchanges credentials for a token, and sends `Authorization: Bearer <token>` to protected routes.

## Register safely

`POST /api/v1/auth/register` accepts `email`, `password`, and `display_name`:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"sam@example.com","password":"a-long-password","display_name":"Sam"}'
```

Email is lowercased by validation. Passwords shorter than eight characters fail with `422`; a repeated email is `409` with `code: "conflict"`. The response is `201` and contains a UUID, status (`active`), and timestamps, but no password hash.

The SQLite adapter stores the Argon2 hash. This is intentionally a port-and-adapter boundary: replacing SQLite with PostgreSQL does not require changing the HTTP route or domain model. In a real service, add rate limits, email verification, breached-password checks, and an account-recovery flow around this minimal lesson implementation.

## Issue a token

Send the same email and password to `/api/v1/auth/token`:

```bash
TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"sam@example.com","password":"a-long-password"}' | jq -r .access_token)
```

The response shape is:

```json
{"access_token":"eyJ...","token_type":"bearer","expires_in":3600}
```

The issuer signs an `HS256` token containing `sub` (the user UUID), `iat`, `exp`, and `iss: "taskbox"`. The default lifetime is 3,600 seconds and can be changed with `TASKBOX_JWT_EXPIRES`. Do not put secrets, passwords, or mutable authorization decisions in claims. TaskBox checks membership in the database for each project operation, so role changes take effect without waiting for a token refresh.

## Send and validate it

```bash
curl -sS http://127.0.0.1:8000/api/v1/me \
  -H "Authorization: Bearer $TOKEN"
curl -sS http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" -G --data-urlencode limit=10
```

`GET /me` returns the current active user. The dependency first requires a Bearer credential, then verifies the signature, issuer, expiry, and subject, and finally loads an active user. Disabled or missing users cannot continue even if an old token still verifies.

No credential, a forged token, a token signed with the wrong algorithm, an expired token, or a token for a disabled user produces `401` with `WWW-Authenticate: Bearer`. An example problem document is:

```json
{"type":"https://taskbox.dev/problems/authentication_required","title":"Authentication Required","status":401,"detail":"invalid or expired token","instance":"...","code":"authentication_required"}
```

Validation errors are different: a malformed request body is `422` and includes `errors` entries with locations such as `body.password`.

## Configuration and deployment

Set a long, random `TASKBOX_JWT_SECRET` in the deployment environment. The built-in `dev-only-change-me` fallback is for local learning only. Keep configuration out of source control, rotate secrets deliberately, use HTTPS, and avoid logging full Authorization headers. If you need immediate revocation, add a token version or denylist; short expiry alone does not revoke an already-issued token.

## Exercise

Register `SAM@EXAMPLE.COM`, then confirm `/me` reports `sam@example.com`. Try a seven-character password and repeat registration to observe `422` and `409`. Remove the Authorization header from `/me`, change one character in the token, and wait for expiry with a short `TASKBOX_JWT_EXPIRES`: all three cases should be handled as authentication failures. Checkpoint: your client should refresh or ask the user to sign in again on `401`, while treating `403` from a valid token as an authorization problem.

Common pitfalls include sending the token in a query parameter, assuming `token_type` means the token is opaque, trusting decoded claims without signature verification, and confusing a valid identity with project membership. The route's trust boundary is the verifier plus the database lookup—not merely the presence of a string that looks like a JWT.

## Designing a client session

Keep the access token in the narrowest storage available to your client. A browser application should prefer a secure, HttpOnly, SameSite cookie architecture if its deployment supports one; a command-line client can keep the token in a process environment for the duration of a run. Never print it in debug logs or paste it into issue trackers. Send `Content-Type: application/json` on requests with bodies and let the server's `401` response drive sign-in, rather than trying to decode expiry locally as an authorization decision.

Authentication is also a lifecycle. On logout, delete the local token. On a password reset or security incident, rotate the server secret or introduce a per-user token version and reject older versions. A secret rotation invalidates all existing HS256 tokens, so plan a coordinated rollout if multiple API instances are running. Verify that every instance receives the same configured secret, issuer, and expiry policy before putting it behind a load balancer.
