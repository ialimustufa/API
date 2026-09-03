# Prerequisite Lab 00: Postman foundations with TaskBox

This required prerequisite establishes the Postman workflow used throughout **API Engineering with TaskBox**. Complete it before Lab 01. You will work with the repository's existing file-backed `TaskBox API` collection rather than creating a replacement or changing request behavior.

**Estimated time:** 3 hours

## Learning objectives

By the end, you can:

- navigate the local workspace, collection, folders, requests, and saved examples;
- compose and send HTTP requests, then inspect status, headers, body, timing, and test results;
- explain variable resolution and choose an appropriate scope;
- keep secrets out of shared collection files and use local session/environment values;
- recognize request-level and inherited Bearer authorization;
- read before-request and after-response scripts without weakening their assertions;
- distinguish saved examples from live responses;
- run the TaskBox workflow in dependency order and diagnose failures;
- use collection and request descriptions as course documentation.

## Prerequisites

- Clone/open this repository in Postman with the repository root as the local workspace folder.
- Install Python 3.13+ and `uv`; run `uv sync --all-groups --frozen` from the repository root.
- Have the Postman desktop app available. Node 24 LTS is needed only to preview the course site.
- Use only a disposable local TaskBox database and non-production identities. The supplied owner example is `Ali Mustufa` / `ali.shaikh@example.com`.

No prior request scripting experience is required. Basic familiarity with HTTP methods and JSON is helpful.

## 1. Start TaskBox and verify the target

From the repository root:

```bash
uv sync --all-groups --frozen
uv run uvicorn taskbox.main:app --reload
```

Keep that terminal open. TaskBox listens at `http://127.0.0.1:8000`; generated API documentation is at `http://127.0.0.1:8000/docs`.

In Postman, open **TaskBox API > Health > Health check** and select **Send**. Inspect all response areas:

1. status is `200 OK`;
2. body is `{"status":"ok"}`;
3. `Content-Type` is JSON;
4. response timing is displayed;
5. the request and collection after-response tests pass.

Repeat with **Liveness check** and **Readiness check**. Liveness checks the process; readiness also checks the configured database connection.

**Expected outcome:** all three requests return 200 and their tests pass. A connection error means the local server is not reachable at the resolved `base_url`.

## 2. Map the local workspace and collection

The source of truth in this filesystem workspace is:

```text
postman/collections/TaskBox API/
├── .resources/definition.yaml
├── Health/
├── Auth/
├── Projects/
├── Members/
├── Tasks/
└── Webhooks/
```

Open these items in Postman and compare them with their files:

- `.resources/definition.yaml` contains collection description, variables, and collection-level scripts.
- Each folder's `.resources/definition.yaml` contains folder documentation, order, and sometimes inherited authorization.
- `*.request.yaml` files contain methods, URLs, parameters, bodies, authorization overrides, scripts, and example-directory references.
- `.resources/<request>.resources/examples/*.example.yaml` contains saved request/response examples.

Do not put request files inside `.resources/`, and do not edit generated IDs. Local changes are real repository changes: review them before committing.

**Exercise:** locate **Register owner**, **Create project**, and **Import tasks** in both the sidebar and filesystem. Identify their HTTP method, URL, body, scripts, and order value.

## 3. Requests, variables, and scopes

Open **Register owner**. Its URL is `{{base_url}}/api/v1/auth/register`, and its JSON body uses `owner_email`, `owner_password`, and `owner_display_name`. Hover or inspect each variable to confirm its resolved value before sending.

The collection defines reusable defaults including:

- configuration/input: `base_url`, owner/member identity fields, and `webhook_secret`;
- runtime state: `owner_id`, `member_id`, `owner_access_token`, `member_access_token`, `project_id`, `task_id`, `cursor`, and `webhook_event_id`.

Use the narrowest practical scope:

| Scope | Use in this course |
| --- | --- |
| Local/temporary | one-off experimentation that must not persist |
| Data/iteration | values supplied to one collection run |
| Environment | machine- or deployment-specific values such as a different base URL; secrets should be local/session-only |
| Collection | shared TaskBox defaults and workflow state used by these requests |
| Global | avoid for this course because it can silently affect unrelated collections |

A narrower scope with the same name overrides a broader one. Before debugging a request, inspect the resolved value and its scope rather than assuming the collection default won.

**Exercise:** create or select a local TaskBox development environment only if you need to override machine-specific values. Add `base_url=http://127.0.0.1:8000` as a local value, send **Health check**, then disable/remove the override and verify the collection value resolves again. Do not duplicate every collection variable into the environment.

## 4. Secret hygiene and authorization

The committed passwords and `dev-webhook-secret` are disposable development defaults, not production credentials. Never commit real passwords, JWTs, webhook secrets, API keys, or populated local environment exports. For non-local work, set sensitive values in an appropriate local/session value and keep the shared value empty or demonstrably non-secret. Configure long random `TASKBOX_JWT_SECRET` and `TASKBOX_WEBHOOK_SECRET` on the service before exposure.

Open **Projects** and its folder documentation. The folder supplies Bearer auth using `{{owner_access_token}}`. Requests inherit that auth unless they override it. Compare:

- **Register owner**: request-level `noauth`;
- **Get current owner**: request-level Bearer `{{owner_access_token}}`;
- **Projects** requests: folder-inherited owner Bearer token;
- **Member can list members**: request-level override with `{{member_access_token}}`.

Do not paste a token into an `Authorization` header in a saved request. Let the auth configuration resolve the variable.

**Exercise:** send **Get current owner** before token creation and observe the authentication failure. Then follow the owner bootstrap below and resend it successfully.

## 5. Scripts, tests, and runtime state

Scripts in this collection are existing executable documentation; do not remove or relax them to make a failure disappear.

- Collection after-response tests check response time, JSON content type, and TaskBox problem details.
- Request after-response tests check request-specific status/body contracts.
- Capture scripts save IDs and tokens with `pm.collectionVariables.set(...)` for later requests.
- **Import tasks** has a before-request script that substitutes the exact raw body, computes HMAC-SHA256 using `webhook_secret`, and sets `webhook_signature`.

Open **Register owner** and read its after-response script. It checks `201`, validates the public user shape, confirms credentials are absent, and captures `owner_id`. Open **Get owner token** and identify where it captures `owner_access_token`.

Send in this order:

1. **Register owner**
2. **Get owner token**
3. **Get current owner**

Inspect test results after every send and inspect the updated collection values. If registration returns `409`, the persistent database already contains that email; change the disposable `owner_email` value or intentionally start with a fresh disposable database. Do not delete data you did not create for this lab.

**Expected outcome:** `owner_id` and `owner_access_token` are populated locally, and **Get current owner** returns the registered identity.

## 6. Saved examples versus live responses

Open the saved examples attached to **Health check**, **Register owner**, and **Get owner token**. An example is static documentation/mock material: viewing it does not contact TaskBox, execute scripts, or update variables. A live response records what the running server returned now and runs the applicable tests.

Compare the live duplicate-registration `409` response with the saved **409 Conflict** example. Check status, `application/problem+json`, and the stable problem fields. Example UUIDs, timestamps, and abbreviated JWTs are illustrative and must not be copied into workflow variables.

**Exercise:** explain why a saved `201 Created` example can remain useful even when your current live registration correctly returns 409.

## 7. Run the practical workflow

Run individual requests first so you understand dependencies, then use the collection runner. Preserve folder/request order; later requests consume values captured earlier.

Recommended sequence:

1. Health: health, liveness, readiness.
2. Auth: register owner, owner token, current owner; register member, member token, current member.
3. Projects: create project before project reads/updates; its script captures `project_id`.
4. Members: add the captured member, promote to editor, and run the member authorization request.
5. Tasks: create before get/update/member-read; creation captures `task_id`; then verify editor creation.
6. Webhooks: set a fresh `webhook_event_id`, import once, and inspect the accepted response. Reusing the ID is intentionally a 409, but the saved request's success assertion expects the first 202 run.
7. Cleanup: delete tasks, remove the member, and delete the project only after all dependent assertions. Destructive requests make later project-scoped requests fail.

For a runner pass, select only a coherent sequence. The collection contains both first-run success requests and behavior demonstrations whose expected status depends on prior state; do not mistake an intentionally replayed request for a clean-run success case. Review each failure in context.

**Expected outcome:** captured IDs connect the workflow, owner/editor authorization behaves as documented, and non-destructive success requests pass. Record any deliberate conflict or cleanup behavior separately.

## 8. Documentation and course usage

Read the collection description and each folder description before the corresponding course module. During later labs:

- use **Health** for operations and smoke checks;
- use **Auth** and member-specific requests for authentication/authorization work;
- use **Projects** and **Tasks** for HTTP design, CRUD, testing, and persistence;
- use **Webhooks** for signed, idempotent import behavior;
- use saved examples and test results as evidence, not as a replacement for pytest, OpenAPI, lint, or site checks.

When implementation behavior changes in a later exercise, update the contract, request, tests, examples, and documentation together only when the exercise explicitly calls for that change. Preserve current request behavior in this prerequisite.

## Troubleshooting

**Connection refused or wrong host.** Confirm Uvicorn is running and inspect the resolved `base_url`, including environment overrides.

**401 on a protected request.** Run registration/token bootstrap, confirm the correct token variable is populated, and check whether request-level auth overrides folder auth.

**403 with a valid token.** Authentication succeeded but the identity lacks the required project role. Confirm membership setup and whether owner or member auth is active.

**404 on project/task routes.** Confirm `project_id` or `task_id` was captured and that cleanup did not already delete the resource.

**409 during registration.** The durable SQLite database already contains the email. Use another disposable address or a deliberately isolated database.

**409 duplicate webhook.** `webhook_event_id` is an idempotency key. Use a new value only for a genuinely new lab event.

**422 response.** Inspect the JSON body, resolved variables, and field constraints; do not weaken the test before understanding the response.

**Tests parse the wrong response shape.** Start from a clean/coherent sequence. A request expecting success may receive a problem response when a prerequisite failed.

## Security guidance

- Keep the service bound to local development unless it is configured for exposure.
- Never reuse the example passwords or development secrets outside disposable local data.
- Keep real secret values in local/session scope; do not commit them in collection or environment files.
- Treat access tokens and webhook signatures as credentials; do not paste them into screenshots, examples, logs, or documentation.
- Do not reset or delete a database unless you created it as disposable lab state.
- Review scripts before running collections obtained from any source; scripts can read and modify scoped values and requests.

## Knowledge check

1. Why can an environment `base_url` change a request that already has a collection `base_url`?
2. What is the difference between a saved example and a live response?
3. Which script phase signs the webhook body, and why must signing happen after substitution?
4. Why does **Create project** have to run before project-scoped requests?
5. How does request-level member auth differ from folder-inherited owner auth?
6. Why should a 403 not be fixed by obtaining a syntactically valid token alone?
7. Which values are safe to share, and which must remain local/session-only?
8. Why should cleanup requests run last?

## Practical completion checklist

- [ ] TaskBox starts locally and all three Health requests return 200 with passing tests.
- [ ] I can find collection, folder, request, example, and definition files in the local workspace.
- [ ] I can explain variable precedence and inspect the resolved scope of `base_url`.
- [ ] I kept real secrets/tokens out of shared files and understand local/session values.
- [ ] I can identify no-auth, request Bearer auth, and inherited folder Bearer auth.
- [ ] I inspected collection/request tests and the webhook before-request script.
- [ ] I distinguished saved examples from live responses.
- [ ] I bootstrapped an owner and verified captured ID/token workflow state.
- [ ] I ran or carefully staged a coherent TaskBox workflow in dependency order.
- [ ] I can use the collection documentation to choose requests for later modules.
- [ ] I answered the knowledge check and recorded any unresolved troubleshooting notes.

Completion of this checklist is required before starting `course/labs/01-http-api-design/`.
