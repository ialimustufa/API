---
title: Authentication
description: Issue and use JWT access tokens.
---

Clients authenticate once, receive a short-lived JWT, and send it as a Bearer token on protected requests. Keep signing secrets outside source control and make expiry explicit.

The completed lesson will cover token issuance, validation, and the errors clients should handle.
