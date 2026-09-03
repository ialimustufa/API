---
title: Cursor pagination
description: Return stable pages while data changes.
---

Cursor pagination uses an opaque continuation token rather than a page number. Order by a deterministic key, return a `next_cursor` only when more results remain, and validate malformed cursors as client errors.
