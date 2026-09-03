from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from taskbox.api.dependencies import current_user, optional_user, services
from taskbox.api.schemas import (
    LoginRequest,
    MembershipCreate,
    MembershipResponse,
    MembershipUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RegisterRequest,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TokenResponse,
    UserResponse,
)
from taskbox.domain.models import TaskStatus, User

router = APIRouter(prefix="/api/v1")


def page(items, cursor):
    return {"items": items, "next_cursor": cursor}


@router.post("/auth/register", response_model=UserResponse, status_code=201, tags=["Auth"])
def register(body: RegisterRequest, svc=Depends(services)):  # noqa: F405
    return svc.auth.register(
        email=str(body.email), password=body.password, display_name=body.display_name
    )


@router.post("/auth/token", response_model=TokenResponse, tags=["Auth"])
def token(body: LoginRequest, svc=Depends(services)):  # noqa: F405
    return {
        "access_token": svc.auth.authenticate(email=str(body.email), password=body.password),
        "token_type": "bearer",
        "expires_in": svc.token_expires,
    }


@router.get("/me", response_model=UserResponse, tags=["Auth"])
def me(user: User = Depends(current_user)):
    return user


@router.get("/projects", tags=["Projects"])
def list_projects(
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    svc=Depends(services),
):
    result = svc.projects.list(actor_id=user.id, cursor=cursor, limit=limit)
    return page(list(result.items), result.next_cursor)


@router.post("/projects", response_model=ProjectResponse, status_code=201, tags=["Projects"])
def create_project(body: ProjectCreate, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.projects.create(actor_id=user.id, name=body.name, description=body.description)


@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
def get_project(project_id: str, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.projects.get(actor_id=user.id, project_id=project_id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
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


@router.delete("/projects/{project_id}", status_code=204, tags=["Projects"])
def delete_project(project_id: str, user: User = Depends(current_user), svc=Depends(services)):
    svc.projects.delete(actor_id=user.id, project_id=project_id)
    return Response(status_code=204)


@router.get("/projects/{project_id}/members", tags=["Projects"])
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
    "/projects/{project_id}/members/{user_id}", response_model=MembershipResponse, tags=["Projects"]
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


@router.delete("/projects/{project_id}/members/{user_id}", status_code=204, tags=["Projects"])
def remove_member(
    project_id: str, user_id: str, user: User = Depends(current_user), svc=Depends(services)
):
    svc.projects.remove_member(actor_id=user.id, project_id=project_id, user_id=user_id)
    return Response(status_code=204)


@router.get("/projects/{project_id}/tasks", tags=["Tasks"])
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
    "/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"]
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


@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: str, user: User = Depends(current_user), svc=Depends(services)):  # noqa: F405
    return svc.tasks.get(actor_id=user.id, task_id=task_id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(
    task_id: str, body: TaskUpdate, user: User = Depends(current_user), svc=Depends(services)
):  # noqa: F405
    return svc.tasks.update(
        actor_id=user.id, task_id=task_id, **{k: getattr(body, k) for k in body.model_fields_set}
    )


@router.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"])
def delete_task(task_id: str, user: User = Depends(current_user), svc=Depends(services)):
    svc.tasks.delete(actor_id=user.id, task_id=task_id)
    return Response(status_code=204)


@router.post("/webhooks/tasks/import", status_code=202, tags=["Webhooks"])
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
    return {"event_id": x_webhook_event_id, "imported": len(imported), "duplicate": False}


__all__ = ["router"]
