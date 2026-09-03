"""Persistence ports used by TaskBox application services.

Implementations may use SQLite, PostgreSQL, or an in-memory fake.  The domain
never imports a database driver; these protocols are the stable seam for the
course's persistence labs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeVar

from taskbox.domain.models import Membership, Project, Task, TaskStatus, User, WebhookReceipt

EntityT = TypeVar("EntityT")


@dataclass(frozen=True, slots=True)
class Page[EntityT]:
    """A cursor page; the cursor is opaque to callers."""

    items: Sequence[EntityT]
    next_cursor: str | None = None


class UserRepository(Protocol):
    def get(self, user_id: str) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def save(self, user: User) -> User: ...


class ProjectRepository(Protocol):
    def get(self, project_id: str) -> Project | None: ...

    def list_for_user(
        self, user_id: str, *, cursor: str | None = None, limit: int = 50
    ) -> Page[Project]: ...

    def save(self, project: Project) -> Project: ...

    def delete(self, project_id: str) -> None: ...


class MembershipRepository(Protocol):
    def get(self, project_id: str, user_id: str) -> Membership | None: ...

    def list_for_project(
        self, project_id: str, *, cursor: str | None = None, limit: int = 50
    ) -> Page[Membership]: ...

    def save(self, membership: Membership) -> Membership: ...

    def delete(self, project_id: str, user_id: str) -> None: ...


class TaskRepository(Protocol):
    def get(self, task_id: str) -> Task | None: ...

    def list_for_project(
        self,
        project_id: str,
        *,
        cursor: str | None = None,
        limit: int = 50,
        status: TaskStatus | None = None,
        assignee_id: str | None = None,
    ) -> Page[Task]: ...

    def save(self, task: Task) -> Task: ...

    def delete(self, task_id: str) -> None: ...


class WebhookReceiptRepository(Protocol):
    def get_by_event_id(self, event_id: str) -> WebhookReceipt | None: ...

    def save(self, receipt: WebhookReceipt) -> WebhookReceipt: ...

    def mark_processed(
        self,
        event_id: str,
        *,
        status: str,
        processed_at: datetime,
        error: str | None = None,
    ) -> WebhookReceipt: ...


class UnitOfWork(Protocol):
    """Transaction boundary for operations that touch multiple repositories."""

    users: UserRepository
    projects: ProjectRepository
    memberships: MembershipRepository
    tasks: TaskRepository
    webhook_receipts: WebhookReceiptRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


__all__ = [
    "MembershipRepository",
    "Page",
    "ProjectRepository",
    "TaskRepository",
    "UnitOfWork",
    "UserRepository",
    "WebhookReceiptRepository",
]
