from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from taskbox.api.dependencies import current_user, optional_user, services
from taskbox.api.schemas import (
    LoginRequest,
    MembershipCreate,
    MembershipPage,
    MembershipResponse,
    MembershipUpdate,
    ProjectCreate,
    ProjectPage,
    ProjectResponse,
    ProjectUpdate,
    RegisterRequest,
    TaskCreate,
    TaskPage,
    TaskResponse,
    TaskUpdate,
    TokenResponse,
    UserResponse,
    WebhookImportResponse,
)
from taskbox.domain.models import TaskStatus, User

router = APIRouter(prefix="/api/v1")

_PROBLEM_DESCRIPTIONS = {
    400: "Cursor is invalid or expired",
    401: "Authentication is required",
    403: "The authenticated user lacks the required project role",
    404: "Resource not found",
    409: "Resource conflicts with existing state",
    422: "Request validation failed",
}


def problems(*status_codes: int) -> dict[int, dict]:
    """Declare the RFC 9457 responses served by the application handlers."""
    return {
        code: {
            "description": _PROBLEM_DESCRIPTIONS[code],
            "content": {
                "application/problem+json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        }
        for code in status_codes
    }


def page(items, cursor):
    return {"items": items, "next_cursor": cursor}


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201,
    tags=["Auth"],
    operation_id="registerUser",
    responses=problems(409, 422),
)
def register(body: RegisterRequest, svc=Depends(services)):  # noqa: F405
    return svc.auth.register(
        email=str(body.email), password=body.password, display_name=body.display_name
    )


@router.post(
    "/auth/token",
    response_model=TokenResponse,
    tags=["Auth"],
    operation_id="createToken",
    responses=problems(401, 422),
)
def token(body: LoginRequest, svc=Depends(services)):  # noqa: F405
    return {
        "access_token": svc.auth.authenticate(email=str(body.email), password=body.password),
        "token_type": "bearer",
        "expires_in": svc.token_expires,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    tags=["Auth"],
    operation_id="getCurrentUser",
    responses=problems(401),
)
def me(user: User = Depends(current_user)):
    return user


@router.get(
    "/projects",
    response_model=ProjectPage,
    tags=["Projects"],
    operation_id="listProjects",
    responses=problems(401),
)
def list_projects(
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    svc=Depends(services),
):
    result = svc.projects.list(actor_id=user.id, cursor=cursor, limit=limit)
    return page(list(result.items), result.next_cursor)


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=201,
    tags=["Projects"],
    operation_id="createProject",
    responses=problems(401, 422),
)
def create_project(body: ProjectCreate, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.projects.create(actor_id=user.id, name=body.name, description=body.description)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Projects"],
    operation_id="getProject",
    responses=problems(401, 404),
)
def get_project(project_id: str, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.projects.get(actor_id=user.id, project_id=project_id)


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Projects"],
    operation_id="updateProject",
    responses=problems(401, 403, 404, 422),
)
def update_project(
    project_id: str, body: ProjectUpdate, user: User = Depends(current_user), svc=Depends(services)
):  # noqa: F405
    return svc.projects.update(
        actor_id=user.id,
        project_id=project_id,
        name=body.name,
        description=body.description,
        description_set="description" in body.model_fields_set,
    )


@router.delete(
    "/projects/{project_id}",
    status_code=204,
    tags=["Projects"],
    operation_id="deleteProject",
    responses=problems(401, 403, 404),
)
def delete_project(project_id: str, user: User = Depends(current_user), svc=Depends(services)):
    svc.projects.delete(actor_id=user.id, project_id=project_id)
    return Response(status_code=204)


@router.get(
    "/projects/{project_id}/members",
    response_model=MembershipPage,
    tags=["Projects"],
    operation_id="listMembers",
    responses=problems(401, 403, 404),
)
def list_members(
    project_id: str,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    svc=Depends(services),
):
    result = svc.projects.list_members(
        actor_id=user.id, project_id=project_id, cursor=cursor, limit=limit
    )
    return page(list(result.items), result.next_cursor)


@router.post(
    "/projects/{project_id}/members",
    response_model=MembershipResponse,
    status_code=201,
    tags=["Projects"],
    operation_id="addMember",
    responses=problems(401, 403, 404, 409),
)
def add_member(
    project_id: str,
    body: MembershipCreate,
    user: User = Depends(current_user),
    svc=Depends(services),
):  # noqa: F405
    return svc.projects.add_member(
        actor_id=user.id, project_id=project_id, user_id=body.user_id, role=body.role.value
    )


@router.patch(
    "/projects/{project_id}/members/{user_id}",
    response_model=MembershipResponse,
    tags=["Projects"],
    operation_id="updateMemberRole",
    responses=problems(401, 403, 404),
)
def update_member(
    project_id: str,
    user_id: str,
    body: MembershipUpdate,
    user: User = Depends(current_user),
    svc=Depends(services),
):  # noqa: F405
    return svc.projects.update_member(
        actor_id=user.id, project_id=project_id, user_id=user_id, role=body.role.value
    )


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=204,
    tags=["Projects"],
    operation_id="removeMember",
    responses=problems(401, 403, 404),
)
def remove_member(
    project_id: str, user_id: str, user: User = Depends(current_user), svc=Depends(services)
):
    svc.projects.remove_member(actor_id=user.id, project_id=project_id, user_id=user_id)
    return Response(status_code=204)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskPage,
    tags=["Tasks"],
    operation_id="listTasks",
    responses=problems(400, 401, 403, 404),
)
def list_tasks(
    project_id: str,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    status: TaskStatus | None = None,
    assignee_id: str | None = None,
    user: User = Depends(current_user),
    svc=Depends(services),
):  # noqa: F405
    result = svc.tasks.list(
        actor_id=user.id,
        project_id=project_id,
        cursor=cursor,
        limit=limit,
        status=status,
        assignee_id=assignee_id,
    )
    return page(list(result.items), result.next_cursor)


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=201,
    tags=["Tasks"],
    operation_id="createTask",
    responses=problems(401, 403, 404, 422),
)
def create_task(
    project_id: str, body: TaskCreate, user: User = Depends(current_user), svc=Depends(services)
):  # noqa: F405
    return svc.tasks.create(
        actor_id=user.id,
        project_id=project_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        assignee_id=body.assignee_id,
        due_at=body.due_at,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    operation_id="getTask",
    responses=problems(401, 403, 404),
)
def get_task(task_id: str, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.tasks.get(actor_id=user.id, task_id=task_id)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    operation_id="updateTask",
    responses=problems(401, 403, 404, 422),
)
def update_task(
    task_id: str, body: TaskUpdate, user: User = Depends(current_user), svc=Depends(services)
):  # noqa: F405
    return svc.tasks.update(
        actor_id=user.id, task_id=task_id, **{k: getattr(body, k) for k in body.model_fields_set}
    )


@router.delete(
    "/tasks/{task_id}",
    status_code=204,
    tags=["Tasks"],
    operation_id="deleteTask",
    responses=problems(401, 403, 404),
)
def delete_task(task_id: str, user: User = Depends(current_user), svc=Depends(services)):
    svc.tasks.delete(actor_id=user.id, task_id=task_id)
    return Response(status_code=204)


@router.post(
    "/webhooks/tasks/import",
    response_model=WebhookImportResponse,
    status_code=202,
    tags=["Webhooks"],
    operation_id="importTasksWebhook",
    responses=problems(400, 401, 409),
    openapi_extra={
        "security": [],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WebhookImportRequest"}
                }
            },
        },
    },
)
async def import_tasks(
    request: Request,
    x_webhook_event_id: str = Header(...),
    x_webhook_signature: str = Header(...),
    user: User | None = Depends(optional_user),
    svc=Depends(services),
):
    payload = await request.body()
    imported = svc.webhooks.import_tasks(
        payload=payload,
        signature=x_webhook_signature,
        event_id=x_webhook_event_id,
        actor_id=user.id if user else None,
    )
    return {"event_id": x_webhook_event_id, "imported": len(imported)}


__all__ = ["router"]
