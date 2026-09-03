---
title: "Module 10: Webhooks and events"
description: Authenticate, replay-protect, and process incoming events.
---

Verify an HMAC signature over `timestamp.raw_body` before JSON parsing, enforce a small timestamp window, and compare signatures in constant time. Require a stable event ID and persist an idempotency record before side effects. A valid duplicate should be acknowledged safely; invalid signatures should not reveal parsing or account details. Queue slow work after fast verification and return a bounded response.

Complete [Lab 10](/labs/10-webhooks-events/) and generate a header with `course/examples/webhooks/sign.py`.
