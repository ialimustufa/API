# API Course Refresh — contributor rules

## Scope

This branch refreshes the public `ialimustufa/API` repository. The upstream baseline is
`086ce40f65fbdbce845ef463f5011def79f1c48d`. Work may be committed and pushed only from
`codex/api-course-refresh` to `origin/codex/api-course-refresh`. Do not push directly to
`main`, open a PR, change GitHub settings, manually trigger deployment workflows, or
deploy Pages.

## Frozen decisions

- Preserve the original `README.md` and `API_Basics.ipynb` byte-for-byte under
  `legacy/original/`; do not execute or rewrite the notebook.
- The corrected legacy implementation is Flask with clean `/api/v1/jokes` routes,
  in-memory state, configurable hashed Basic Auth, and RFC 9457 errors. Do not register
  the old `/joke` or `/adjoke` paths; document their mapping instead.
- The new course application is FastAPI TaskBox with SQLite-first persistence, a required
  PostgreSQL/Docker lab, JWT authentication, project roles, cursor pagination, and signed
  webhook import.
- Python learner baseline is 3.13 (`>=3.13,<3.15`) using `uv`; docs use Astro 7.3.1,
  Starlight 0.42.0, Node 24 LTS, and npm 11 or newer.

## Agent boundaries

Agents receive an exclusive path allowlist. Do not edit outside it, switch branches,
rebase/reset, or change frozen contracts. Only the integrator may modify Git metadata,
commit, or push, and only for the current `codex/api-course-refresh` branch as allowed
above. Keep starter lab code intentionally incomplete; CI validates solution code only.
If a decision is missing, report `NEEDS-DECISION` rather than redesigning a neighboring
subsystem.

## Handoff

Every agent reports `STATUS: DONE | BLOCKED | NEEDS-DECISION`, changed files, commands run,
results, contract deviations, and remaining risks. The integrator owns shared manifests,
lockfiles, composition-root wiring, cross-path fixes, commits, pushes, and final verification.
