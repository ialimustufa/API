---
title: Signed webhooks
description: Import events safely with a signed request.
---

TaskBox imports external tasks through `POST /api/v1/webhooks/tasks/import`. The endpoint authenticates the bytes first, validates the JSON shape second, checks project authorization, and records the event ID so a delivery retry cannot create the same tasks twice. This ordering is the important lesson: never interpret an unverified message as business data.

## The wire contract

The sender supplies two required headers:

* `X-Webhook-Event-ID`: a stable, unique ID for this delivery event.
* `X-Webhook-Signature`: an HMAC-SHA256 digest, optionally prefixed with `sha256=`.

The signature is calculated over the exact raw request body with `TASKBOX_WEBHOOK_SECRET`. The body must be an object containing a `project_id` and a non-empty `tasks` array. Each task needs a title; it may also contain `description`, `status`, `priority`, `assignee_id`, and `due_at`.

For a local test, prepare compact JSON and sign those exact bytes (whitespace changes the digest):

```bash
PAYLOAD='{"project_id":"PROJECT_UUID","actor_id":"OWNER_UUID","tasks":[{"title":"Import from vendor","priority":2}]}'
SIG=$(printf '%s' "$PAYLOAD" | openssl dgst -sha256 -hmac "$TASKBOX_WEBHOOK_SECRET" -hex | awk '{print $2}')
curl -i -X POST http://127.0.0.1:8000/api/v1/webhooks/tasks/import \
  -H 'Content-Type: application/json' \
  -H 'X-Webhook-Event-ID: vendor-2025-0001' \
  -H "X-Webhook-Signature: sha256=$SIG" \
  -H "Authorization: Bearer $TOKEN" \
  --data "$PAYLOAD"
```

The successful response is `202`:

```json
{"event_id":"vendor-2025-0001","imported":1}
```

The optional Bearer token matters. If no token is supplied, the service can use `actor_id` from the verified body; without either actor, it returns `401`. The actor must be an owner or editor of the target project. A viewer is authenticated but receives `403`.

### Capstone threat-model note

TaskBox uses one shared development secret, so a valid signature proves only that a sender knows that secret; it does not establish a distinct sender identity. In particular, an unauthenticated but correctly signed payload can name any project owner or editor in `actor_id`. This is acceptable only for the controlled lab. A production receiver should either require Bearer authentication for the acting user or map a per-sender secret/key identity to an allowed actor or project scope. Do not treat `actor_id` from the body as independent authorization.

## Verification and idempotency

TaskBox uses constant-time HMAC comparison and strips only the optional `sha256=` prefix. A wrong secret, altered body, or malformed signature returns `401` with `code: "invalid_webhook_signature"`:

```json
{"type":"http://127.0.0.1:8000/problems/invalid_webhook_signature","title":"Invalid Webhook Signature","status":401,"detail":"webhook signature is invalid","instance":"...","code":"invalid_webhook_signature"}
```

Only after verification does the service decode JSON. Invalid JSON or a missing project/tasks list is `422` with `code: "validation_error"`; a nonexistent project is `404`. Task field validation (for example, priority outside 0–4) also fails as a domain validation error.

After authorization, the service creates a `WebhookReceipt` containing the event ID, signature, SHA-256 payload hash, and processing timestamps. The event ID is unique. Replaying the same event—even with a different payload—returns `409` and `code: "duplicate_webhook"`:

```json
{"type":"http://127.0.0.1:8000/problems/duplicate_webhook","title":"Duplicate Webhook","status":409,"detail":"webhook event has already been received","instance":"...","code":"duplicate_webhook"}
```

The receipt and imported tasks are committed in one unit of work. If task validation fails midway, the transaction must roll back so a later corrected retry is not incorrectly blocked by a receipt. The receipt status model (`received`, `processed`, `failed`) provides an audit trail for production retry tooling.

## Replay resistance in production

The current course endpoint signs the raw body and deduplicates by event ID. It does not currently require a timestamp header or enforce a freshness window, so a stolen valid body could be replayed under a new event ID. A production extension should include a signed timestamp, reject messages outside a small clock-skew window, cap body size, and enforce event-ID uniqueness at the database boundary. Rotate webhook secrets with an overlap period, and keep secrets out of logs and source control.

Do not parse and re-serialize JSON before verifying: key order, spaces, and newline bytes are part of the signed message. Use HTTPS, restrict who can reach the endpoint where possible, and record safe metadata (event ID, hash, status) rather than sensitive payloads.

## Checkpoint

Send one valid import and verify exactly one task appears. Send the same event ID twice and assert the second response is `409` with no extra task. Change one byte without changing the signature and expect `401`; sign the changed bytes and expect validation or authorization according to its content. Try a viewer token and then omit both token and `actor_id`. These tests exercise authenticity, authorization, idempotency, and failure ordering.

## Sender-side retry design

A sender should treat `202` as accepted, persist the event ID, and retry transient `5xx` responses with exponential backoff. A `401`, `403`, `404`, or `422` generally needs operator attention or a corrected message, not an immediate infinite retry. A `409 duplicate_webhook` is usually a successful outcome for a retry: the receiver has already recorded that event, so the sender can mark its delivery complete after optionally reconciling the imported task count.

Use a fresh event ID for a genuinely new business event, never for a transport retry. If the same event must be reprocessed after a permanent failure, define an explicit administrative replay operation rather than bypassing the uniqueness constraint. Keep the receiver's response body small and use the receipt table as the source of truth for support investigations.
