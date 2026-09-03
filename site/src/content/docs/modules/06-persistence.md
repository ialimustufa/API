---
title: "Module 6: Durable persistence"
description: Start with SQLite and keep the repository portable.
---

SQLite is an excellent local feedback loop: one file, no service bootstrap, and durable state. Keep SQLAlchemy models behind a repository boundary, use explicit transactions, and treat schema changes as migrations. Avoid `create_all` in production. The PostgreSQL move should change configuration and migration execution, not domain behavior. Test uniqueness, rollback, foreign keys, and concurrent updates.

Complete [Lab 06](/labs/06-persistence/) before the PostgreSQL exercise.
