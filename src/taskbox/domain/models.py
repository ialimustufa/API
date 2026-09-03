"""Framework-independent TaskBox domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from .errors import ValidationError


def _id(value: UUID | str | None) -> str:
    """Return a canonical UUID string, generating one when omitted."""

    if value is None:
        return str(uuid4())
    try:
        return str(UUID(str(value)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValidationError("id must be a UUID") from exc


def _required(value: str, name: str, *, max_length: int | None = None) -> str:
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        raise ValidationError(f"{name} is required")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters")
    return value


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class WebhookReceiptStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass(slots=True)
class User:
    email: str
    password_hash: str
    display_name: str
    id: str = field(default_factory=lambda: _id(None))
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = _id(self.id)
        self.email = _required(self.email, "email", max_length=320).lower()
        if "@" not in self.email:
            raise ValidationError("email must be valid")
        self.password_hash = _required(self.password_hash, "password_hash")
        self.display_name = _required(self.display_name, "display_name", max_length=120)
        self.status = UserStatus(self.status)


@dataclass(slots=True)
class Project:
    name: str
    owner_id: str
    description: str | None = None
    id: str = field(default_factory=lambda: _id(None))
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = _id(self.id)
        self.owner_id = _id(self.owner_id)
        self.name = _required(self.name, "name", max_length=160)
        if self.description is not None and len(self.description) > 2000:
            raise ValidationError("description must be at most 2000 characters")


@dataclass(slots=True)
class Membership:
    project_id: str
    user_id: str
    role: ProjectRole = ProjectRole.VIEWER
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.project_id = _id(self.project_id)
        self.user_id = _id(self.user_id)
        self.role = ProjectRole(self.role)


@dataclass(slots=True)
class Task:
    project_id: str
    title: str
    created_by: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: int = 0
    assignee_id: str | None = None
    due_at: datetime | None = None
    id: str = field(default_factory=lambda: _id(None))
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = _id(self.id)
        self.project_id = _id(self.project_id)
        self.created_by = _id(self.created_by)
        if self.assignee_id is not None:
            self.assignee_id = _id(self.assignee_id)
        self.title = _required(self.title, "title", max_length=240)
        if self.description is not None and len(self.description) > 10000:
            raise ValidationError("description must be at most 10000 characters")
        self.status = TaskStatus(self.status)
        if (
            not isinstance(self.priority, int)
            or isinstance(self.priority, bool)
            or not 0 <= self.priority <= 4
        ):
            raise ValidationError("priority must be an integer between 0 and 4")


@dataclass(slots=True)
class WebhookReceipt:
    """Idempotency record for a signed external task import."""

    event_id: str
    signature: str
    payload_hash: str
    id: str = field(default_factory=lambda: _id(None))
    status: WebhookReceiptStatus = WebhookReceiptStatus.RECEIVED
    received_at: datetime | None = None
    processed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = _id(self.id)
        self.event_id = _required(self.event_id, "event_id", max_length=255)
        self.signature = _required(self.signature, "signature", max_length=512)
        self.payload_hash = _required(self.payload_hash, "payload_hash", max_length=128)
        self.status = WebhookReceiptStatus(self.status)


__all__ = [
    "Membership",
    "Project",
    "ProjectRole",
    "Task",
    "TaskStatus",
    "User",
    "UserStatus",
    "WebhookReceipt",
    "WebhookReceiptStatus",
]
