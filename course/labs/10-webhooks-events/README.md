# Lab 10: Signed webhooks and event processing

Verify the raw request body before decoding JSON. The solution uses HMAC
SHA-256 with a timestamped `t=...,v1=...` header, rejects stale requests, and
deduplicates event IDs so retries are safe. Never log the secret or trust an
event merely because its JSON parses successfully.
