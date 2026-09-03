---
title: "Module 5: Authentication and security"
description: Protect APIs without leaking account information.
---

Use short-lived JWT access tokens with `sub`, `iat`, and `exp` claims. Hash passwords with Argon2 and keep signing keys in environment configuration. A protected route should return `401` plus `WWW-Authenticate: Bearer` for missing, malformed, or expired credentials; reserve `403` for an authenticated principal lacking permission. Add rate limits, input bounds, dependency pinning, and audit logs without logging tokens or passwords.

Complete [Lab 05](/labs/05-auth-security/) and test success, missing credentials, bad credentials, expired tokens, and algorithm/key mismatch.
