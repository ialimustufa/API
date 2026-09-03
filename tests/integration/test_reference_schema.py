"""Database-level checks for the reference SQLite bootstrap DDL."""

from __future__ import annotations

import pytest

from taskbox.adapters.sqlite import SQLiteDatabase
from taskbox.domain.errors import PersistenceError


def test_reference_schema_enforces_checks_and_installs_query_indexes() -> None:
    database = SQLiteDatabase("sqlite:///:memory:")
    try:
        with pytest.raises(PersistenceError):
            database.run(
                lambda connection: connection.execute(
                    "INSERT INTO users VALUES "
                    "('bad', 'bad@example.com', 'hash', 'Bad', 'unknown', 'now', 'now')"
                )
            )

        database.run(
            lambda connection: connection.execute(
                "INSERT INTO users VALUES "
                "('user', 'user@example.com', 'hash', 'User', 'active', 'now', 'now')"
            )
        )
        database.run(
            lambda connection: connection.execute(
                "INSERT INTO projects VALUES ('project', 'user', 'Project', NULL, 'now', 'now')"
            )
        )
        for statement in (
            "INSERT INTO memberships VALUES ('project', 'user', 'invalid', 'now', 'now')",
            "INSERT INTO tasks VALUES "
            "('task', 'project', 'user', NULL, 'Task', NULL, 'invalid', 0, NULL, 'now', 'now')",
            "INSERT INTO tasks VALUES "
            "('task', 'project', 'user', NULL, 'Task', NULL, 'todo', 5, NULL, 'now', 'now')",
            "INSERT INTO webhook_receipts VALUES "
            "('receipt', 'event', 'sig', 'hash', 'invalid', 'now', NULL, NULL, '{}')",
        ):
            with pytest.raises(PersistenceError):
                database.run(lambda connection, sql=statement: connection.execute(sql))

        indexes = database.run(
            lambda connection: {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
            }
        )
        assert {
            "idx_projects_owner",
            "idx_memberships_user",
            "idx_tasks_project_cursor",
            "idx_tasks_project_status",
            "idx_webhook_receipts_status",
        } <= indexes
    finally:
        database.close()
