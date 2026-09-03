---
title: Projects and roles
description: Apply project-scoped authorization.
---

Authorization belongs at the project boundary. A user may have different roles in different projects, so every protected operation must resolve both the principal and project membership. TaskBox keeps this policy in application services rather than scattering role checks through route functions.

## Membership is the relationship

Creating a project automatically creates an `owner` membership for its creator. The other roles are `editor` and `viewer`:

| Role | Read project/tasks | Create or edit tasks | Change project/members | Delete project |
| --- | --- | --- | --- | --- |
| owner | yes | yes | yes | yes |
| editor | yes | yes | no | no |
| viewer | yes | no | no | no |

All three can list members, but membership itself is required. A random authenticated user cannot guess a project UUID and read it. The service first checks that the project exists, then checks the actor's membership, then applies the role set for the operation.

## Invite and manage members

First register a second user and save that user's returned `id` as `USER_ID`. As the owner, add them:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/members" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"$USER_ID\",\"role\":\"editor\"}"
```

The response is `201` with `project_id`, `user_id`, `role`, and timestamps. `owner` cannot be assigned through this route because the project has one canonical owner. Use `GET /projects/{project_id}/members` to inspect current membership. Update an editor to viewer with:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/members/$USER_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H 'Content-Type: application/json' \
  -d '{"role":"viewer"}'
```

Only the owner can add, update, or remove members. Removing the owner returns a conflict; removing a missing membership returns `404`. Re-adding an existing member returns `409`, making retries visible rather than silently changing policy.

## See the policy in task routes

An editor can create a task:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/tasks" \
  -H "Authorization: Bearer $EDITOR_TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Prepare release notes","priority":1}'
```

A viewer can list the same project and tasks, but the identical create request returns `403`:

```json
{"type":"https://taskbox.dev/problems/forbidden","title":"Forbidden","status":403,"detail":"your project role cannot perform this action","instance":"...","code":"forbidden"}
```

Task updates and deletes use `/api/v1/tasks/{task_id}` rather than nesting the project ID. That is safe because the service loads the task, obtains its `project_id`, and performs the same membership check. Never implement this route by checking only that the task ID exists.

Project `PATCH` and `DELETE`, and all member mutations, use the owner role set. `PATCH /projects/{id}` is partial: omit `description` to preserve it, or send `description: null` to clear it. Names must remain non-empty and at most 160 characters.

## Multi-tenant thinking

Treat `project_id` as a tenant boundary in logs, queries, caches, and background jobs. Every repository query should include the project or user scope. A common vulnerability is fetching a task globally and authorizing it against a caller-selected project ID; TaskBox avoids that by deriving the project from the fetched task. Add tests for cross-project IDs, non-members, and role downgrades.

## Checkpoint

Create two users and one project. Add the second user as `viewer`, prove they can `GET /projects/{id}` and `GET /projects/{id}/tasks`, and prove they receive `403` on task creation. As owner, promote them to `editor`, repeat creation, then demote them and confirm future writes fail. Finally attempt to assign `owner` through the membership endpoint and confirm the validation failure. This exercise tests both positive permissions and revocation.

Pitfalls: treating authentication as authorization; trusting a role supplied by the client; allowing an editor to edit project metadata; forgetting that owner membership is created atomically with a project; and returning `404` for every forbidden object without deciding whether your product wants resource enumeration resistance. TaskBox's current service distinguishes missing projects (`404`) from non-members (`403`), so clients and tests should follow that contract.

## Policy changes and auditability

Role changes are ordinary writes and update the membership timestamp. A production UI should show who made a change, when it took effect, and what the previous role was; the current TaskBox model is the authorization source but does not yet expose an audit-event route. Add audit records in the same transaction as membership changes so a successful permission change always has a corresponding record. If a user is removed while a request is in flight, the next authorization check should win: do not cache “editor” decisions longer than your stated policy allows.

For background jobs, carry the initiating user and project IDs explicitly. Never let a worker infer a tenant from an untrusted task payload, and never reuse an owner credential for every project. A narrow service identity plus an explicit project policy is easier to review and revoke.
