---
title: Cursor pagination
description: Return stable pages while data changes.
---

TaskBox list endpoints use cursor pagination. A request supplies `limit` (default 50, maximum 100) and receives an `items` array plus `next_cursor`. The cursor is an opaque continuation token: clients store it and send it back, but do not parse or manufacture it.

## The contract

Projects, members, and tasks all follow the same shape:

```bash
curl -sS -G "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/tasks" \
  -H "Authorization: Bearer $TOKEN" --data-urlencode 'limit=2' \
  --data-urlencode 'status=todo'
```

```json
{
  "items": [{"id":"...","project_id":"...","title":"One","status":"todo","priority":0}],
  "next_cursor": "eyJzb3J0X2tleSI6IjIw..."
}
```

When there are no more results, `next_cursor` is `null`. Continue with URL encoding (cursors contain URL-safe Base64, but encoding is still correct):

```bash
curl -sS -G "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/tasks" \
  -H "Authorization: Bearer $TOKEN" --data-urlencode 'limit=2' \
  --data-urlencode "cursor=$NEXT_CURSOR"
```

The same pattern applies to `GET /api/v1/projects`, filtered to projects visible to the caller, and `GET /api/v1/projects/{project_id}/members`.

## Why a cursor?

Offset pagination (`page=3`) becomes unreliable when rows are inserted or deleted between requests: an insertion can shift every later row, producing duplicates or skips. SQLite orders TaskBox rows by `(created_at, id)`. The adapter fetches one extra row (`limit + 1`), returns only the requested number, and encodes the extra row's sort key and ID as the next cursor. The next query asks for rows strictly after that pair:

```text
created_at > cursor_time
OR (created_at = cursor_time AND id > cursor_id)
```

The UUID tie-breaker makes ordering deterministic even when timestamps match. This is a continuation boundary, not a promise that the entire collection is frozen. A newly inserted row that sorts before the cursor may be intentionally absent from the current traversal; clients can start a fresh traversal when they need a current snapshot.

## Filters are part of the traversal

Task lists support `status` (`todo`, `in_progress`, `done`, `archived`) and `assignee_id`. Keep the filter values unchanged while following a cursor. A cursor created for one filter is not a general bookmark for another filter, even though the current codec is intentionally small and opaque. If a UI changes status, restart at `cursor` omitted rather than reusing the old continuation.

`limit` is validated by FastAPI: values below 1 or above 100 produce `422`. A malformed or undecodable cursor produces `400`:

```json
{"type":"https://taskbox.dev/problems/invalid_cursor","title":"Invalid Cursor","status":400,"detail":"cursor is invalid","instance":"...","code":"invalid_cursor"}
```

Handle this as a restartable client error: discard the cursor and fetch the first page, or ask the user to refresh.

## A robust client loop

Pseudocode for a consumer is:

```text
cursor = absent
do:
  response = GET(endpoint, limit=50, cursor if present, same filters)
  process(response.items)
  cursor = response.next_cursor
while cursor is not null
```

Do not loop on a cursor forever: retain the last cursor, cap retries, and surface repeated failures. Process items idempotently when possible because a retry after a network timeout cannot tell whether the server responded. For a UI, show a “Load more” action and disable it while the request is in flight; for exports, persist the cursor and filter set together.

## Exercise and production notes

Create five tasks, request `limit=2`, follow both returned cursors, and assert that every ID appears once. Insert another task between page requests and observe that the original traversal remains ordered. Then change `status` while reusing a cursor and compare it with a fresh traversal; this demonstrates why the filter is part of the client state.

The SQLite implementation has indexes for the cursor paths (`projects`/members and `tasks(project_id, created_at, id)`). A PostgreSQL lab should preserve the same ordering and composite comparison semantics. Do not expose the Base64 JSON as a documented schema: changing its encoding is an implementation detail, and accepting client-edited sort keys would make pagination unsafe or confusing.

## Observability and consistency

Log the endpoint, requested limit, filter names, result count, and whether a next cursor was emitted, but do not log the cursor itself if it could reveal internal timestamps or identifiers. Measure page latency separately from total export duration. If a page fails, retry the same request with the same cursor; do not advance locally until the response is successfully processed. For long-running exports, remember that deletions and edits can still change what a later page contains. If an immutable audit export is required, take a database snapshot or export by a stable versioned relation instead of promising snapshot semantics from this cursor API.

Cursor values are endpoint data, not credentials. They can still be used to probe ordering if exposed, so authorize every page request exactly as you authorize the first page. In particular, do not cache a project task page across users without including the authenticated principal and filter set in the cache key.
