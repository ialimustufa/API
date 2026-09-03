---
title: Signed webhooks
description: Import events safely with a signed request.
---

Webhook imports should authenticate the message before parsing its business meaning. Verify the signature against the raw request body, enforce a timestamp window, and make event handling idempotent.
