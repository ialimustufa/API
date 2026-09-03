"""Service and infrastructure ports for the TaskBox application layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Protocol

from taskbox.domain.models import Membership, Project, Task, User

from .repositories import Page


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenIssuer(Protocol):
    def issue(
        self,
        *,
        subject: str,
        claims: Mapping[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> str: ...

    def verify(self, token: str) -> Mapping[str, Any]: ...


class CursorCodec(Protocol):
    def encode(self, *, sort_key: str, entity_id: str) -> str: ...

    def decode(self, cursor: str) -> tuple[str, str]: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_id(self) -> str: ...


class WebhookSignatureVerifier(Protocol):
    def verify(self, *, payload: bytes, signature: str) -> bool: ...


class AuthService(Protocol):
    def register(self, *, email: str, password: str, display_name: str) -> User: ...

    def authenticate(self, *, email: str, password: str) -> str: ...

    def current_user(self, token: str) -> User: ...


class ProjectService(Protocol):
    def create(self, *, actor_id: str, name: str, description: str | None = None) -> Project: ...

    def list(
        self, *, actor_id: str, cursor: str | None = None, limit: int = 50
    ) -> Page[Project]: ...

    def add_member(
        self, *, actor_id: str, project_id: str, user_id: str, role: str
    ) -> Membership: ...


class TaskService(Protocol):
    def create(
        self,
        *,
        actor_id: str,
        project_id: str,
        title: str,
        description: str | None = None,
        **fields: Any,
    ) -> Task: ...

    def get(self, *, actor_id: str, task_id: str) -> Task: ...

    def list(
        self,
        *,
        actor_id: str,
        project_id: str,
        cursor: str | None = None,
        limit: int = 50,
        **filters: Any,
    ) -> Page[Task]: ...


class WebhookImportService(Protocol):
    def import_tasks(
        self, *, payload: bytes, signature: str, event_id: str, actor_id: str | None = None
    ) -> Sequence[Task]: ...


__all__ = [
    "AuthService",
    "Clock",
    "CursorCodec",
    "IdGenerator",
    "PasswordHasher",
    "ProjectService",
    "TaskService",
    "TokenIssuer",
    "WebhookImportService",
    "WebhookSignatureVerifier",
]
