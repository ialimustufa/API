---
title: "Module 10: Webhooks and events"
description: Authenticate, replay-protect, and process incoming events.
---

An inbound webhook is an unauthenticated network boundary until your service proves otherwise. JSON parsing is not proof of origin, and a valid signature does not make processing safe to repeat. This module combines authenticity, freshness, idempotency, and bounded work into one reliable receiver.

## Learning objectives

- verify an HMAC over the exact raw request bytes;
- reject stale, malformed, or replayed requests safely;
- persist event identity before performing side effects;
- acknowledge quickly while keeping slow work retryable.

## Verify bytes before JSON

The sender signs `timestamp.raw_body` with a shared secret. Read the request body once, parse the header, and compute the expected HMAC over those exact bytes. Whitespace, key ordering, and character encoding changes can alter the digest, so never parse and reserialize before verification. Compare signatures with a constant-time function such as `hmac.compare_digest`.

Lab 10 uses an `X-TaskBox-Signature` value shaped like `t=...,v1=...`. Reject missing fields, unsupported versions, non-numeric timestamps, and requests outside a small clock-skew window. A timestamp is replay protection only within that window; the event ID closes the remaining gap.

```python
signed = f"{timestamp}.".encode() + raw_body
expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, supplied):
    raise invalid_signature()
if abs(time.time() - timestamp) > settings.webhook_tolerance:
    raise stale_request()
```

Use one stable failure response for invalid signatures and avoid revealing whether parsing would have succeeded. Never log the secret, complete signed payload, or an Authorization-like header.

## Idempotent processing

Providers retry on timeouts and 5xx responses, and network failures can occur after your side effect but before your acknowledgment. Require a stable event ID. In the same durable store used by the application, insert an idempotency record with a uniqueness constraint before applying the side effect. If insertion reports a duplicate, acknowledge the valid event without applying it again.

The ordering matters: verification, timestamp check, event-ID validation, durable deduplication, then business action. A transaction can record “received” and update TaskBox state atomically when the action is local. For slow or external work, enqueue an outbox/job after the record is committed and make the worker idempotent too.

## Fast acknowledgment and observability

Do not hold the HTTP request open while making an email call or importing a large object graph. Return a bounded success response once the event is durably accepted. Emit a request ID, event ID, event type, verification result, and processing outcome in structured logs. Metrics should distinguish invalid signatures, stale requests, duplicates, accepted events, and failed jobs. Those categories tell an operator whether an incident is an attack, a provider retry storm, or an application defect.

## Practice and verification

Run the timestamped Lab 10 signer in [course/examples/webhooks/sign.py](https://github.com/ialimustufa/API/blob/main/course/examples/webhooks/sign.py) only against the Lab 10 solution. It emits `X-TaskBox-Signature: t=...,v1=...`, which is intentionally different from the TaskBox reference API. For TaskBox, use [course/examples/webhooks/sign_taskbox.py](https://github.com/ialimustufa/API/blob/main/course/examples/webhooks/sign_taskbox.py); it emits the event-ID and raw-body HMAC headers documented on the TaskBox signed-webhooks page. Test a valid event, a changed body, wrong secret, stale timestamp, malformed header, missing ID, and the same valid event twice. The duplicate should be acknowledged safely and should create only one side effect.

Exercise: add a durable event status (`received`, `processed`, `failed`) and a retry worker with bounded attempts. Document whether a permanently failed event can be replayed manually and how an operator proves that replay is safe.

## Pitfalls and next steps

Typical mistakes are verifying parsed JSON, using ordinary equality for signatures, allowing unlimited timestamp skew, marking an event processed after a non-idempotent side effect, and returning 200 for an invalid signature. Keep secrets in environment configuration and rotate them with an overlap plan when providers support multiple active secrets.

Next, integrate these guarantees in [Module 11: Capstone and deployment](../11-capstone-deployment/).
