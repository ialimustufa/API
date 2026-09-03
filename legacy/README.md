# Legacy API Basics course

This directory preserves the original API Basics teaching material for historical
reference. The notebook and its README are copied byte-for-byte from the original
repository; they are intentionally not edited or re-run.

## Open the archived notebook

[Open API_Basics.ipynb in Google Colab](https://colab.research.google.com/github/ialimustufa/API/blob/main/legacy/original/API_Basics.ipynb)

The archived [README](original/README.md) is the original introduction. The new
course and maintained examples live at the repository root and in `course/`.

## Why this material is archived

The notebook is useful as a historical introduction, but it is not a maintained
production example. In particular:

- It installs the unmaintained `flask-restful`/`flask-ngrok` workflow; ngrok
  tunnelling is unnecessary for local learning and should not be used as a
  deployment strategy.
- It embeds demonstration credentials (`ali`/`iali.dev` and `public`/`public`)
  in source code. Never reuse them.
- The API uses mutable global state, accepts client-supplied IDs, and has no
  isolation between tests or requests.
- `id=0` is treated as if no ID was supplied, so the seeded joke with ID 0
  cannot be retrieved deterministically.
- Several handlers return inconsistent response shapes/status codes (including
  a body with `204`), use string identity comparison, and can report success
  when a delete did not remove a resource.
- Validation, error responses, authentication coverage, and URL handling are
  incomplete; notebook outputs may also be stale.

The maintained corrected Flask implementation is in `legacy/fixed_flask_api/`.
It is a compatibility teaching example, with configuration-injected Basic Auth,
isolated storage, validation, and consistent HTTP responses.

## Migration from the archived routes

| Archived route | Maintained route | Notes |
| --- | --- | --- |
| `GET /` | `GET /health/live` | Use a machine-readable health response. |
| `GET /joke` or `GET /joke/<id>` | `GET /api/v1/jokes` or `GET /api/v1/jokes/<joke_id>` | ID 0 is now handled correctly; collections are paginated. |
| `POST /joke` or `/adjoke` | `POST /api/v1/jokes` | ID is server-generated; HTTP Basic Auth is required. |
| `PUT /joke` or `/adjoke` | `PUT /api/v1/jokes/<joke_id>` | The resource ID belongs in the path; returns `200`. |
| `DELETE /joke/<id>` or `/adjoke/<id>` | `DELETE /api/v1/jokes/<joke_id>` | Returns `204` with no response body. |
| *(none)* | `GET /api/v1/jokes/random` | Returns `404` when the store is empty. |

The old routes are deliberately not registered by the corrected app. Use the
new API as the source for future lessons.
