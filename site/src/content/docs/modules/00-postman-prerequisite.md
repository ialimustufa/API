---
title: "Prerequisite 00: Postman foundations"
description: Learn the local TaskBox collection workflow before Lab 01.
---

Complete this required three-hour prerequisite before Module 1. It uses the repository's existing file-backed **TaskBox API** collection and does not change request behavior.

## Learning objectives

You will learn to navigate the local workspace and collection, send and inspect requests, resolve variable scopes, protect secrets, understand authorization inheritance, read scripts/tests, compare examples with live responses, and run dependent requests in a safe order.

## Setup

From the repository root:

```bash
uv sync --all-groups --frozen
uv run uvicorn taskbox.main:app --reload
```

TaskBox runs at `http://127.0.0.1:8000`. Open **TaskBox API > Health > Health check** in Postman, send it, and verify the 200 status, JSON body, headers, timing, and passing test results.

## Practical path

1. Compare the Postman sidebar with `postman/collections/TaskBox API/`: collection and folder metadata live in `.resources/definition.yaml`, requests in `*.request.yaml`, and examples in request-specific `.resources` directories.
2. Inspect `{{base_url}}` and the owner/member variables. Use environment values only for machine/deployment overrides; avoid globals and avoid duplicating all collection values.
3. Keep real passwords, JWTs, webhook secrets, and API keys in local/session values, never committed shared files. Repository defaults are disposable local examples only.
4. Compare request-level `noauth`, owner/member Bearer auth, and the inherited owner auth on Projects, Members, Tasks, and Webhooks.
5. Read collection and request after-response tests. Observe how registration/token/project/task scripts capture IDs and tokens. Read the webhook before-request HMAC script.
6. Compare saved examples with live responses. Examples are static documentation; live sends contact TaskBox, run scripts, and can update workflow variables.
7. Bootstrap owner and member identities, create a project, configure membership, create tasks, and import a signed event. Preserve dependency order and run destructive cleanup last.
8. Read collection/folder descriptions when each later course module directs you to the TaskBox companion requests.

## Required lab

The complete lesson—including objectives, scope table, hands-on exercises, expected outcomes, troubleshooting, security guidance, knowledge checks, and completion checklist—is in:

`course/labs/00-postman-prerequisite/README.md`

Do every exercise there before opening `course/labs/01-http-api-design/README.md`.

## Expected outcome

You can explain what a request resolves and sends, where its authorization comes from, which script updates downstream state, why an example is not a live result, and which request must run next. You can diagnose 401, 403, 404, 409, and 422 outcomes without weakening existing assertions.

## Security checkpoint

Do not commit populated tokens or real secrets, expose the development service, reset a database you do not own, or paste credentials into saved headers/examples. Review scripts before running them and use a disposable local database and identities.
