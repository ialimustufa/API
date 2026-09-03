---
title: Build an API you can trust
description: A practical course in production-minded Python APIs.
template: splash
hero:
  tagline: Python 3.13 · FastAPI · SQLite · PostgreSQL
  actions:
    - text: Start the course
      link: ./setup/
      icon: right-arrow
    - text: See the TaskBox API
      link: ./taskbox/domain-and-routes/
      icon: external
---

TaskBox is a small, complete API that gives you room to practice the decisions that matter in real services: authentication, authorization, persistence, pagination, and webhooks.

Start with [environment setup](./setup/), complete [Prerequisite 00: Postman foundations](./modules/00-postman-prerequisite/), then follow the numbered chapters in order. The required prerequisite appears before Lab 01 and brings the complete course to 43 hours. The
course uses a deliberately small reference application so each boundary is
inspectable: HTTP contracts at the edge, domain rules in the middle, and
replaceable adapters at the infrastructure boundary.

## What you will build

- A FastAPI service with a clean, versioned HTTP surface.
- JWT authentication and project-scoped roles.
- SQLite-first development with a PostgreSQL and Docker lab.
- Cursor pagination and signed webhook imports.

The lessons are designed to be read alongside the repository code. Each chapter names the contract first, then leaves you with a focused implementation exercise.

## Persistence path

The default path is SQLite-first: run locally with one durable file, inspect
constraints and transactions, and practice migrations without starting a
database service. Then complete the separate PostgreSQL transition lab in
`course/labs/07-operations/`, where Docker Compose adds a healthy database
dependency and a disposable PostgreSQL instance. Root Compose is intentionally
different: it runs the SQLite app on local port 8000 with a named volume.

Local site links begin at `/`; the deployed GitHub Pages site is prefixed with
`/API/`.

## Learning outcomes

By the end, you should be able to explain a versioned API contract, enforce
project-scoped roles, persist and paginate data safely, verify signed imports,
and describe a migration and readiness sequence suitable for deployment.
