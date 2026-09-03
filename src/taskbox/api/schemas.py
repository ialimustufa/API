from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from taskbox.domain.models import ProjectRole, TaskStatus, UserStatus


class RegisterRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("value is not a valid email address")
        return value.lower()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("value is not a valid email address")
        return value.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class MembershipCreate(BaseModel):
    user_id: str
    role: ProjectRole


class MembershipUpdate(BaseModel):
    role: ProjectRole


class Membership(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: str
    user_id: str
    role: ProjectRole
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus = TaskStatus.TODO
    priority: int = Field(default=0, ge=0, le=4)
    assignee_id: str | None = None
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=0, le=4)
    assignee_id: str | None = None
    due_at: datetime | None = None


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    created_by: str
    assignee_id: str | None = None
    title: str
    description: str | None = None
    status: TaskStatus
    priority: int
    due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PageResponse(BaseModel):
    items: list
    next_cursor: str | None


class ProjectPage(BaseModel):
    items: list[Project]
    next_cursor: str | None


class MembershipPage(BaseModel):
    items: list[Membership]
    next_cursor: str | None


class TaskPage(BaseModel):
    items: list[Task]
    next_cursor: str | None


class PageInfo(BaseModel):
    next_cursor: str | None


class Health(BaseModel):
    status: Literal["ok"]


class WebhookImportResponse(BaseModel):
    event_id: str
    imported: int = Field(ge=0)


class WebhookImportRequest(BaseModel):
    project_id: str
    actor_id: str | None = None
    tasks: list[TaskCreate] = Field(min_length=1)


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    code: str | None = None
    errors: list[dict] | None = None


# Route imports retain their descriptive response aliases while the OpenAPI
# component names match the curated public contract.
UserResponse = User
ProjectResponse = Project
MembershipResponse = Membership
TaskResponse = Task
HealthResponse = Health


__all__ = [
    "HealthResponse",
    "LoginRequest",
    "MembershipCreate",
    "MembershipResponse",
    "MembershipUpdate",
    "PageResponse",
    "PageInfo",
    "ProjectPage",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "RegisterRequest",
    "TaskCreate",
    "TaskResponse",
    "TaskPage",
    "TaskUpdate",
    "TokenResponse",
    "UserResponse",
    "MembershipPage",
    "WebhookImportRequest",
    "WebhookImportResponse",
    "ProblemDetail",
]
