"""SQLite persistence adapters.

The repositories intentionally implement the small protocols in
``taskbox.ports.repositories``.  SQLite is the default development store;
the SQL is portable enough for the PostgreSQL lab to use as a guide.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, TypeVar

from taskbox.domain.errors import InvalidCursorError, PersistenceError
from taskbox.domain.models import (
    Membership,
    Project,
    ProjectRole,
    Task,
    TaskStatus,
    User,
    UserStatus,
    WebhookReceipt,
    WebhookReceiptStatus,
)
from taskbox.ports.repositories import Page

_T = TypeVar("_T")

REFERENCE_SCHEMA = files("taskbox.adapters").joinpath("reference_schema.sql").read_text()


def utcnow() -> datetime:
    return datetime.now(UTC)


def dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class CursorCodec:
    """Small opaque, URL-safe cursor codec used by all list repositories."""

    def encode(self, *, sort_key: str, entity_id: str) -> str:
        import base64
        import json

        raw = json.dumps({"sort_key": sort_key, "id": entity_id}, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    def decode(self, cursor: str) -> tuple[str, str]:
        import base64
        import json

        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            value = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
            sort_key, entity_id = value["sort_key"], value["id"]
            if (
                not isinstance(sort_key, str)
                or not isinstance(entity_id, str)
                or not sort_key
                or not entity_id
            ):
                raise ValueError
            return sort_key, entity_id
        except Exception as exc:
            raise InvalidCursorError("cursor is invalid") from exc


class SQLiteDatabase:
    def __init__(self, url: str = "sqlite:///taskbox.db") -> None:
        self.url = url
        if url in {":memory:", "sqlite:///:memory:"}:
            target = ":memory:"
            kwargs: dict[str, Any] = {"check_same_thread": False}
        elif url.startswith("sqlite:///"):
            target = url.removeprefix("sqlite:///")
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            kwargs = {"check_same_thread": False}
        else:
            raise ValueError("only SQLite database URLs are supported by the local adapter")
        self.connection = sqlite3.connect(target, **kwargs)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(REFERENCE_SCHEMA)
        self.connection.commit()
        self.lock = threading.RLock()
        self.cursor_codec = CursorCodec()

    def close(self) -> None:
        self.connection.close()

    def transaction(self) -> SQLiteUnitOfWork:
        return SQLiteUnitOfWork(self)

    def run(self, fn: Callable[[sqlite3.Connection], _T]) -> _T:
        with self.lock:
            try:
                return fn(self.connection)
            except sqlite3.Error as exc:
                raise PersistenceError(str(exc)) from exc


class SQLiteUnitOfWork:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database
        self.connection = database.connection
        self.users = SQLiteUserRepository(database)
        self.projects = SQLiteProjectRepository(database)
        self.memberships = SQLiteMembershipRepository(database)
        self.tasks = SQLiteTaskRepository(database)
        self.webhook_receipts = SQLiteWebhookReceiptRepository(database)

    def __enter__(self) -> SQLiteUnitOfWork:
        self.database.lock.acquire()
        self.connection.execute("BEGIN")
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        try:
            if exc_type:
                self.rollback()
            else:
                self.commit()
        finally:
            self.database.lock.release()

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()


class _Repository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.db = database

    @property
    def conn(self) -> sqlite3.Connection:
        return self.db.connection

    def _run(self, fn: Callable[[sqlite3.Connection], _T]) -> _T:
        return self.db.run(fn)

    def _cursor(self, cursor: str | None) -> tuple[str, str] | None:
        return self.db.cursor_codec.decode(cursor) if cursor else None


class SQLiteUserRepository(_Repository):
    def get(self, user_id: str) -> User | None:
        return self._run(
            lambda c: self._from_row(
                c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            )
        )

    def get_by_email(self, email: str) -> User | None:
        return self._run(
            lambda c: self._from_row(
                c.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
            )
        )

    def save(self, user: User) -> User:
        now = user.created_at or utcnow()
        updated = user.updated_at or now
        self._run(
            lambda c: c.execute(
                "INSERT INTO users(id,email,password_hash,display_name,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,password_hash=excluded.password_hash,display_name=excluded.display_name,status=excluded.status,updated_at=excluded.updated_at",
                (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.display_name,
                    user.status.value,
                    iso(now),
                    iso(updated),
                ),
            )
        )
        user.created_at, user.updated_at = now, updated
        return user

    @staticmethod
    def _from_row(row: sqlite3.Row | None) -> User | None:
        return (
            User(
                id=row["id"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                status=UserStatus(row["status"]),
                created_at=dt(row["created_at"]),
                updated_at=dt(row["updated_at"]),
            )
            if row
            else None
        )


class SQLiteProjectRepository(_Repository):
    def get(self, project_id: str) -> Project | None:
        return self._run(
            lambda c: self._from_row(
                c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            )
        )

    def list_for_user(
        self, user_id: str, *, cursor: str | None = None, limit: int = 50
    ) -> Page[Project]:
        mark = self._cursor(cursor)
        params: list[Any] = [user_id]
        extra = ""
        if mark:
            extra = " AND (p.created_at > ? OR (p.created_at = ? AND p.id > ?))"
            params.extend([mark[0], mark[0], mark[1]])
        params.append(limit + 1)

        def read(c: sqlite3.Connection) -> Page[Project]:
            rows = c.execute(
                f"SELECT DISTINCT p.* FROM projects p JOIN memberships m ON m.project_id=p.id WHERE m.user_id=?{extra} ORDER BY p.created_at,p.id LIMIT ?",
                params,
            ).fetchall()
            items = [self._from_row(row) for row in rows[:limit]]
            next_cursor = (
                self.db.cursor_codec.encode(
                    sort_key=rows[limit]["created_at"], entity_id=rows[limit]["id"]
                )
                if len(rows) > limit
                else None
            )
            return Page(items, next_cursor)

        return self._run(read)

    def save(self, project: Project) -> Project:
        now = project.created_at or utcnow()
        updated = project.updated_at or now
        self._run(
            lambda c: c.execute(
                "INSERT INTO projects(id,owner_id,name,description,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET owner_id=excluded.owner_id,name=excluded.name,description=excluded.description,updated_at=excluded.updated_at",
                (
                    project.id,
                    project.owner_id,
                    project.name,
                    project.description,
                    iso(now),
                    iso(updated),
                ),
            )
        )
        project.created_at, project.updated_at = now, updated
        return project

    def delete(self, project_id: str) -> None:
        self._run(lambda c: c.execute("DELETE FROM projects WHERE id=?", (project_id,)))

    @staticmethod
    def _from_row(row: sqlite3.Row | None) -> Project | None:
        return (
            Project(
                id=row["id"],
                owner_id=row["owner_id"],
                name=row["name"],
                description=row["description"],
                created_at=dt(row["created_at"]),
                updated_at=dt(row["updated_at"]),
            )
            if row
            else None
        )


class SQLiteMembershipRepository(_Repository):
    def get(self, project_id: str, user_id: str) -> Membership | None:
        return self._run(
            lambda c: self._from_row(
                c.execute(
                    "SELECT * FROM memberships WHERE project_id=? AND user_id=?",
                    (project_id, user_id),
                ).fetchone()
            )
        )

    def list_for_project(
        self, project_id: str, *, cursor: str | None = None, limit: int = 50
    ) -> Page[Membership]:
        mark = self._cursor(cursor)
        params: list[Any] = [project_id]
        extra = ""
        if mark:
            extra = " AND (m.created_at > ? OR (m.created_at = ? AND m.user_id > ?))"
            params.extend([mark[0], mark[0], mark[1]])
        params.append(limit + 1)

        def read(c: sqlite3.Connection) -> Page[Membership]:
            rows = c.execute(
                f"SELECT * FROM memberships m WHERE project_id=?{extra} ORDER BY created_at,user_id LIMIT ?",
                params,
            ).fetchall()
            items = [self._from_row(r) for r in rows[:limit]]
            nxt = (
                self.db.cursor_codec.encode(
                    sort_key=rows[limit]["created_at"], entity_id=rows[limit]["user_id"]
                )
                if len(rows) > limit
                else None
            )
            return Page(items, nxt)

        return self._run(read)

    def save(self, membership: Membership) -> Membership:
        now = membership.created_at or utcnow()
        updated = membership.updated_at or now
        self._run(
            lambda c: c.execute(
                "INSERT INTO memberships(project_id,user_id,role,created_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(project_id,user_id) DO UPDATE SET role=excluded.role,updated_at=excluded.updated_at",
                (
                    membership.project_id,
                    membership.user_id,
                    membership.role.value,
                    iso(now),
                    iso(updated),
                ),
            )
        )
        membership.created_at, membership.updated_at = now, updated
        return membership

    def delete(self, project_id: str, user_id: str) -> None:
        self._run(
            lambda c: c.execute(
                "DELETE FROM memberships WHERE project_id=? AND user_id=?", (project_id, user_id)
            )
        )

    @staticmethod
    def _from_row(row: sqlite3.Row | None) -> Membership | None:
        return (
            Membership(
                project_id=row["project_id"],
                user_id=row["user_id"],
                role=ProjectRole(row["role"]),
                created_at=dt(row["created_at"]),
                updated_at=dt(row["updated_at"]),
            )
            if row
            else None
        )


class SQLiteTaskRepository(_Repository):
    def get(self, task_id: str) -> Task | None:
        return self._run(
            lambda c: self._from_row(
                c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            )
        )

    def list_for_project(
        self,
        project_id: str,
        *,
        cursor: str | None = None,
        limit: int = 50,
        status: TaskStatus | None = None,
        assignee_id: str | None = None,
    ) -> Page[Task]:
        mark = self._cursor(cursor)
        params: list[Any] = [project_id]
        where = ""
        if status:
            where += " AND status=?"
            params.append(status.value)
        if assignee_id:
            where += " AND assignee_id=?"
            params.append(assignee_id)
        if mark:
            where += " AND (created_at > ? OR (created_at = ? AND id > ?))"
            params.extend([mark[0], mark[0], mark[1]])
        params.append(limit + 1)

        def read(c: sqlite3.Connection) -> Page[Task]:
            rows = c.execute(
                f"SELECT * FROM tasks WHERE project_id=?{where} ORDER BY created_at,id LIMIT ?",
                params,
            ).fetchall()
            items = [self._from_row(r) for r in rows[:limit]]
            nxt = (
                self.db.cursor_codec.encode(
                    sort_key=rows[limit]["created_at"], entity_id=rows[limit]["id"]
                )
                if len(rows) > limit
                else None
            )
            return Page(items, nxt)

        return self._run(read)

    def save(self, task: Task) -> Task:
        now = task.created_at or utcnow()
        updated = task.updated_at or now
        self._run(
            lambda c: c.execute(
                "INSERT INTO tasks(id,project_id,created_by,assignee_id,title,description,status,priority,due_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET assignee_id=excluded.assignee_id,title=excluded.title,description=excluded.description,status=excluded.status,priority=excluded.priority,due_at=excluded.due_at,updated_at=excluded.updated_at",
                (
                    task.id,
                    task.project_id,
                    task.created_by,
                    task.assignee_id,
                    task.title,
                    task.description,
                    task.status.value,
                    task.priority,
                    iso(task.due_at),
                    iso(now),
                    iso(updated),
                ),
            )
        )
        task.created_at, task.updated_at = now, updated
        return task

    def delete(self, task_id: str) -> None:
        self._run(lambda c: c.execute("DELETE FROM tasks WHERE id=?", (task_id,)))

    @staticmethod
    def _from_row(row: sqlite3.Row | None) -> Task | None:
        return (
            Task(
                id=row["id"],
                project_id=row["project_id"],
                created_by=row["created_by"],
                assignee_id=row["assignee_id"],
                title=row["title"],
                description=row["description"],
                status=TaskStatus(row["status"]),
                priority=row["priority"],
                due_at=dt(row["due_at"]),
                created_at=dt(row["created_at"]),
                updated_at=dt(row["updated_at"]),
            )
            if row
            else None
        )


class SQLiteWebhookReceiptRepository(_Repository):
    def get_by_event_id(self, event_id: str) -> WebhookReceipt | None:
        return self._run(
            lambda c: self._from_row(
                c.execute("SELECT * FROM webhook_receipts WHERE event_id=?", (event_id,)).fetchone()
            )
        )

    def save(self, receipt: WebhookReceipt) -> WebhookReceipt:
        received = receipt.received_at or utcnow()
        self._run(
            lambda c: c.execute(
                "INSERT INTO webhook_receipts(id,event_id,signature,payload_hash,status,received_at,processed_at,error,metadata) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    receipt.id,
                    receipt.event_id,
                    receipt.signature,
                    receipt.payload_hash,
                    receipt.status.value,
                    iso(received),
                    iso(receipt.processed_at),
                    receipt.error,
                    json.dumps(receipt.metadata),
                ),
            )
        )
        receipt.received_at = received
        return receipt

    def mark_processed(
        self, event_id: str, *, status: str, processed_at: datetime, error: str | None = None
    ) -> WebhookReceipt:
        self._run(
            lambda c: c.execute(
                "UPDATE webhook_receipts SET status=?,processed_at=?,error=? WHERE event_id=?",
                (status, iso(processed_at), error, event_id),
            )
        )
        value = self.get_by_event_id(event_id)
        if not value:
            raise PersistenceError("webhook receipt disappeared")
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row | None) -> WebhookReceipt | None:
        return (
            WebhookReceipt(
                id=row["id"],
                event_id=row["event_id"],
                signature=row["signature"],
                payload_hash=row["payload_hash"],
                status=WebhookReceiptStatus(row["status"]),
                received_at=dt(row["received_at"]),
                processed_at=dt(row["processed_at"]),
                error=row["error"],
                metadata=json.loads(row["metadata"] or "{}"),
            )
            if row
            else None
        )


__all__ = [
    "CursorCodec",
    "SQLiteDatabase",
    "SQLiteUnitOfWork",
    "SQLiteUserRepository",
    "SQLiteProjectRepository",
    "SQLiteMembershipRepository",
    "SQLiteTaskRepository",
    "SQLiteWebhookReceiptRepository",
]
