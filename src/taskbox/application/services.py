"""Application use cases and authorization policy for TaskBox."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from taskbox.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DuplicateWebhookError,
    NotFoundError,
    ValidationError,
)
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
from taskbox.ports.repositories import Page, UnitOfWork
from taskbox.ports.services import PasswordHasher, TokenIssuer, WebhookSignatureVerifier


def _now() -> datetime:
    return datetime.now(UTC)


class AuthApplicationService:
    def __init__(
        self, uow_factory: Callable[[], UnitOfWork], hasher: PasswordHasher, tokens: TokenIssuer
    ) -> None:
        self.uow_factory, self.hasher, self.tokens = uow_factory, hasher, tokens

    def register(self, *, email: str, password: str, display_name: str) -> User:
        if len(password) < 8:
            raise ValidationError("password must be at least 8 characters")
        with self.uow_factory() as uow:
            if uow.users.get_by_email(email):
                raise ConflictError("email is already registered")
            user = User(
                email=email, password_hash=self.hasher.hash(password), display_name=display_name
            )
            user.created_at = user.updated_at = _now()
            return uow.users.save(user)

    def authenticate(self, *, email: str, password: str) -> str:
        with self.uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if (
                not user
                or user.status is not UserStatus.ACTIVE
                or not self.hasher.verify(password, user.password_hash)
            ):
                raise AuthenticationError("invalid email or password")
            return self.tokens.issue(subject=user.id)

    def current_user(self, token: str) -> User:
        claims = self.tokens.verify(token)
        with self.uow_factory() as uow:
            user = uow.users.get(str(claims["sub"]))
            if not user or user.status is not UserStatus.ACTIVE:
                raise AuthenticationError("user is not active")
            return user


class ProjectApplicationService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self.uow_factory = uow_factory

    def _membership(
        self,
        uow: UnitOfWork,
        actor_id: str,
        project_id: str,
        *,
        roles: set[ProjectRole] | None = None,
    ) -> Membership:
        if not uow.projects.get(project_id):
            raise NotFoundError("project not found")
        member = uow.memberships.get(project_id, actor_id)
        if not member:
            raise AuthorizationError("you are not a member of this project")
        if roles and member.role not in roles:
            raise AuthorizationError("your project role cannot perform this action")
        return member

    def create(self, *, actor_id: str, name: str, description: str | None = None) -> Project:
        with self.uow_factory() as uow:
            if not uow.users.get(actor_id):
                raise NotFoundError("user not found")
            project = Project(name=name, owner_id=actor_id, description=description)
            project.created_at = project.updated_at = _now()
            uow.projects.save(project)
            membership = Membership(
                project_id=project.id,
                user_id=actor_id,
                role=ProjectRole.OWNER,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            uow.memberships.save(membership)
            return project

    def get(self, *, actor_id: str, project_id: str) -> Project:
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id)
            project = uow.projects.get(project_id)
            assert project
            return project

    def list(self, *, actor_id: str, cursor: str | None = None, limit: int = 50) -> Page[Project]:
        with self.uow_factory() as uow:
            return uow.projects.list_for_user(actor_id, cursor=cursor, limit=limit)

    def update(
        self,
        *,
        actor_id: str,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        description_set: bool = False,
    ) -> Project:
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id, roles={ProjectRole.OWNER})
            project = uow.projects.get(project_id)
            assert project
            if name is not None:
                project.name = name.strip()
            if description_set:
                project.description = description
            project.updated_at = _now()
            # Re-run domain validation after a patch.
            project = Project(
                id=project.id,
                owner_id=project.owner_id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            return uow.projects.save(project)

    def delete(self, *, actor_id: str, project_id: str) -> None:
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id, roles={ProjectRole.OWNER})
            uow.projects.delete(project_id)

    def add_member(self, *, actor_id: str, project_id: str, user_id: str, role: str) -> Membership:
        try:
            project_role = ProjectRole(role)
        except ValueError as exc:
            raise ValidationError("role is invalid") from exc
        if project_role is ProjectRole.OWNER:
            raise ValidationError("owner role is reserved for the project owner")
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id, roles={ProjectRole.OWNER})
            if not uow.users.get(user_id):
                raise NotFoundError("user not found")
            if uow.memberships.get(project_id, user_id):
                raise ConflictError("user is already a member")
            m = Membership(
                project_id=project_id,
                user_id=user_id,
                role=project_role,
                created_at=_now(),
                updated_at=_now(),
            )
            return uow.memberships.save(m)

    def list_members(
        self, *, actor_id: str, project_id: str, cursor: str | None = None, limit: int = 50
    ) -> Page[Membership]:
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id)
            return uow.memberships.list_for_project(project_id, cursor=cursor, limit=limit)

    def update_member(
        self, *, actor_id: str, project_id: str, user_id: str, role: str
    ) -> Membership:
        try:
            project_role = ProjectRole(role)
        except ValueError as exc:
            raise ValidationError("role is invalid") from exc
        if project_role is ProjectRole.OWNER:
            raise ValidationError("owner role cannot be assigned")
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id, roles={ProjectRole.OWNER})
            m = uow.memberships.get(project_id, user_id)
            if not m:
                raise NotFoundError("membership not found")
            m.role, m.updated_at = project_role, _now()
            return uow.memberships.save(m)

    def remove_member(self, *, actor_id: str, project_id: str, user_id: str) -> None:
        with self.uow_factory() as uow:
            self._membership(uow, actor_id, project_id, roles={ProjectRole.OWNER})
            m = uow.memberships.get(project_id, user_id)
            if not m:
                raise NotFoundError("membership not found")
            if m.role is ProjectRole.OWNER:
                raise ConflictError("project owner cannot be removed")
            uow.memberships.delete(project_id, user_id)


class TaskApplicationService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self.uow_factory = uow_factory

    @staticmethod
    def _member(
        uow: UnitOfWork, actor_id: str, project_id: str, roles: set[ProjectRole] | None = None
    ) -> Membership:
        if not uow.projects.get(project_id):
            raise NotFoundError("project not found")
        m = uow.memberships.get(project_id, actor_id)
        if not m:
            raise AuthorizationError("you are not a member of this project")
        if roles and m.role not in roles:
            raise AuthorizationError("your project role cannot perform this action")
        return m

    def create(
        self,
        *,
        actor_id: str,
        project_id: str,
        title: str,
        description: str | None = None,
        **fields: Any,
    ) -> Task:
        with self.uow_factory() as uow:
            self._member(uow, actor_id, project_id, {ProjectRole.OWNER, ProjectRole.EDITOR})
            assignee = fields.get("assignee_id")
            if assignee and not uow.users.get(assignee):
                raise NotFoundError("assignee not found")
            task = Task(
                project_id=project_id,
                created_by=actor_id,
                title=title,
                description=description,
                status=fields.get("status", TaskStatus.TODO),
                priority=fields.get("priority", 0),
                assignee_id=assignee,
                due_at=fields.get("due_at"),
                created_at=_now(),
                updated_at=_now(),
            )
            return uow.tasks.save(task)

    def get(self, *, actor_id: str, task_id: str) -> Task:
        with self.uow_factory() as uow:
            task = uow.tasks.get(task_id)
            if not task:
                raise NotFoundError("task not found")
            self._member(uow, actor_id, task.project_id)
            return task

    def list(
        self,
        *,
        actor_id: str,
        project_id: str,
        cursor: str | None = None,
        limit: int = 50,
        **filters: Any,
    ) -> Page[Task]:
        with self.uow_factory() as uow:
            self._member(uow, actor_id, project_id)
            return uow.tasks.list_for_project(
                project_id,
                cursor=cursor,
                limit=limit,
                status=filters.get("status"),
                assignee_id=filters.get("assignee_id"),
            )

    def update(self, *, actor_id: str, task_id: str, **changes: Any) -> Task:
        with self.uow_factory() as uow:
            task = uow.tasks.get(task_id)
            if not task:
                raise NotFoundError("task not found")
            self._member(uow, actor_id, task.project_id, {ProjectRole.OWNER, ProjectRole.EDITOR})
            if (
                "assignee_id" in changes
                and changes["assignee_id"]
                and not uow.users.get(changes["assignee_id"])
            ):
                raise NotFoundError("assignee not found")
            for key, value in changes.items():
                if value is not None or key in {"description", "assignee_id", "due_at"}:
                    setattr(task, key, value)
            task.updated_at = _now()
            task = Task(
                id=task.id,
                project_id=task.project_id,
                created_by=task.created_by,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                assignee_id=task.assignee_id,
                due_at=task.due_at,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            return uow.tasks.save(task)

    def delete(self, *, actor_id: str, task_id: str) -> None:
        with self.uow_factory() as uow:
            task = uow.tasks.get(task_id)
            if not task:
                raise NotFoundError("task not found")
            self._member(uow, actor_id, task.project_id, {ProjectRole.OWNER, ProjectRole.EDITOR})
            uow.tasks.delete(task_id)


class WebhookImportApplicationService:
    def __init__(
        self, uow_factory: Callable[[], UnitOfWork], verifier: WebhookSignatureVerifier
    ) -> None:
        self.uow_factory, self.verifier = uow_factory, verifier

    def import_tasks(
        self, *, payload: bytes, signature: str, event_id: str, actor_id: str | None = None
    ) -> Sequence[Task]:
        if not self.verifier.verify(payload=payload, signature=signature):
            from taskbox.domain.errors import InvalidWebhookSignatureError

            raise InvalidWebhookSignatureError("webhook signature is invalid")
        try:
            body = json.loads(payload)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValidationError("request body must be valid JSON") from exc
        if (
            not isinstance(body, dict)
            or not body.get("project_id")
            or not isinstance(body.get("tasks"), list)
            or not body["tasks"]
        ):
            raise ValidationError("project_id and a non-empty tasks list are required")
        with self.uow_factory() as uow:
            prior = uow.webhook_receipts.get_by_event_id(event_id)
            if prior:
                raise DuplicateWebhookError("webhook event has already been received")
            actor = actor_id or body.get("actor_id")
            if not actor:
                raise AuthenticationError("webhook import requires an authenticated actor")
            project = uow.projects.get(body["project_id"])
            if not project:
                raise NotFoundError("project not found")
            member = uow.memberships.get(project.id, actor)
            if not member or member.role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
                raise AuthorizationError("your project role cannot import tasks")
            receipt = WebhookReceipt(
                event_id=event_id,
                signature=signature,
                payload_hash=hashlib.sha256(payload).hexdigest(),
                received_at=_now(),
            )
            uow.webhook_receipts.save(receipt)
            result: list[Task] = []
            for data in body["tasks"]:
                if not isinstance(data, dict) or not data.get("title"):
                    raise ValidationError("each imported task requires a title")
                task = Task(
                    project_id=project.id,
                    created_by=actor,
                    title=data["title"],
                    description=data.get("description"),
                    status=data.get("status", TaskStatus.TODO),
                    priority=data.get("priority", 0),
                    assignee_id=data.get("assignee_id"),
                    due_at=data.get("due_at"),
                    created_at=_now(),
                    updated_at=_now(),
                )
                result.append(uow.tasks.save(task))
            uow.webhook_receipts.mark_processed(
                event_id, status=WebhookReceiptStatus.PROCESSED.value, processed_at=_now()
            )
            return result


__all__ = [
    "AuthApplicationService",
    "ProjectApplicationService",
    "TaskApplicationService",
    "WebhookImportApplicationService",
]
