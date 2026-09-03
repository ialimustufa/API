# API Course Refresh — contributor rules

## Scope

This branch refreshes the public `ialimustufa/API` repository. The upstream baseline is
`086ce40f65fbdbce845ef463f5011def79f1c48d`. Work is local-only: do not push, open a PR,
change GitHub settings, or deploy Pages.

## Frozen decisions

- Preserve the original `README.md` and `API_Basics.ipynb` byte-for-byte under
  `legacy/original/`; do not execute or rewrite the notebook.
- The corrected legacy implementation is Flask with clean `/api/v1/jokes` routes,
  in-memory state, configurable hashed Basic Auth, and RFC 9457 errors. Do not register
  the old `/joke` or `/adjoke` paths; document their mapping instead.
- The new course application is FastAPI TaskBox with SQLite-first persistence, a required
  PostgreSQL/Docker lab, JWT authentication, project roles, cursor pagination, and signed
  webhook import.
- Python learner baseline is 3.13 (`>=3.13,<3.15`) using `uv`; docs use Astro 6.4.8,
  Starlight 0.39.2, Node 24 LTS, and npm.

## Agent boundaries

Agents receive an exclusive path allowlist. Do not edit outside it, modify Git metadata,
switch branches, rebase/reset, change frozen contracts, or push. Keep starter lab code
intentionally incomplete; CI validates solution code only. If a decision is missing, report
`NEEDS-DECISION` rather than redesigning a neighboring subsystem.

## Handoff

Every agent reports `STATUS: DONE | BLOCKED | NEEDS-DECISION`, changed files, commands run,
results, contract deviations, and remaining risks. The integrator owns shared manifests,
lockfiles, composition-root wiring, cross-path fixes, commits, and final verification.
