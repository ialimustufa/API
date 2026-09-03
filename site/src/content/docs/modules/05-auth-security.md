---
title: "Module 5: Authentication and security"
description: Protect APIs without leaking account information.
---

Authentication answers “who is calling?” Authorization answers “what may that caller do?” Keep those decisions separate. In TaskBox, a client exchanges credentials for a short-lived JWT, then sends that token on protected requests. A route dependency validates the token and supplies the current principal; the application service checks that principal’s role for the project being changed.

## Learning objectives

By the end of this chapter you should be able to:

- hash and verify passwords without storing plaintext;
- issue and validate JWTs with explicit claims and algorithm configuration;
- distinguish `401 Unauthorized` from `403 Forbidden`;
- add request limits and audit trails without exposing secrets.

## The authentication boundary

The Lab 05 solution exposes `POST /api/v1/auth/token` and `GET /api/v1/me`. A successful token response contains an access token, its type, and an expiry. The token’s `sub` identifies the user, while `iat` records issuance time and `exp` limits its lifetime. Do not put passwords, signing keys, or sensitive profile data in claims: JWT payloads are encoded, not encrypted.

Passwords are one-way material. Argon2 deliberately makes guessing expensive, so store an Argon2 hash and use the password verifier to compare a login attempt. A missing username and a wrong password should produce the same vague failure; otherwise an attacker can enumerate accounts.

For protected routes, missing, malformed, expired, or wrongly signed credentials are authentication failures. Return `401` and `WWW-Authenticate: Bearer`. Once a valid identity exists, an insufficient role is an authorization failure: return `403`. Keep that distinction consistent in OpenAPI and tests.

## Validate deliberately

JWT validation must fix the accepted algorithm and key, rather than trusting an `alg` value supplied by a token. Load the signing secret from an environment variable, fail startup if a production secret is absent, and use a different secret in development and tests. Keep access tokens short-lived; use a separate, carefully designed refresh-token flow if the product needs long sessions.

The conceptual dependency looks like this:

```python
def current_user(authorization: str = Header(default="")) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized()
    try:
        claims = jwt.decode(token, settings.jwt_secret,
                            algorithms=[settings.jwt_algorithm])
        return users.get_by_id(claims["sub"])
    except (JWTError, KeyError, UserNotFound):
        raise unauthorized()
```

The exact library call may differ, but the invariants do not: validate the scheme, signature, algorithm, required claims, and expiry; map all malformed credential cases to the same response; and never log the token.

## Authorization and abuse controls

A role check belongs close to the operation that knows its resource scope. An owner can delete a project, an editor can change tasks, and a viewer can only read. Never accept a role from the request body as proof of permission. Load project membership from trusted state and check it before the write.

Bound input sizes and pagination limits. Apply a per-client or per-account rate limit to login and other expensive endpoints, returning `429` with a useful retry signal. Use dependency pinning and vulnerability checks. Audit security-relevant events (login success/failure, role changes, webhook verification) with user ID, request ID, outcome, and timestamp—but not passwords, bearer tokens, or complete request bodies.

## Practice and verification

Run the lab from its directory, as shown in its README:

```bash
cd course/labs/05-auth-security
uv run uvicorn solution.app:app --reload --port 8005
```

Request a token and call `/api/v1/me` with `Authorization: Bearer TOKEN`. Verify success, no header, wrong credentials, an expired token, an unknown user, and a token signed with a different key. Each invalid credential case should be `401` with the bearer challenge; a valid viewer attempting an owner-only action should be `403`.

Exercise: add a protected route that returns only the current user’s safe fields, write tests for every failure class, and record which events your audit log intentionally omits. See the [Lab 05 source and README](https://github.com/ialimustufa/API/tree/main/course/labs/05-auth-security).

## Pitfalls and next steps

Common mistakes are long-lived tokens, accepting multiple algorithms by accident, returning different messages for “unknown user” and “wrong password,” and authorizing from client-supplied IDs. TLS is still required in deployment: JWT validation does not protect a token sent over an untrusted connection.

Next, continue to [Module 6: Durable persistence](../06-persistence/) and make identity and role state survive a process restart.
