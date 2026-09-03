"""TaskBox FastAPI composition root."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from taskbox.adapters.security import (
    Argon2PasswordHasher,
    HMACWebhookSignatureVerifier,
    JWTTokenIssuer,
)
from taskbox.adapters.sqlite import SQLiteDatabase
from taskbox.api.routes import router
from taskbox.application.services import (
    AuthApplicationService,
    ProjectApplicationService,
    TaskApplicationService,
    WebhookImportApplicationService,
)
from taskbox.domain.errors import TaskBoxError


def _problem(
    request: Request,
    status_code: int,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://taskbox.dev/problems/{code}",
        "title": code.replace("_", " ").title(),
        "status": status_code,
        "detail": detail,
        "instance": str(request.url),
        "code": code,
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        body,
        status_code=status_code,
        media_type="application/problem+json",
        headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
    )


def create_app(
    *,
    database_url: str | None = None,
    jwt_secret: str | None = None,
    webhook_secret: str | None = None,
) -> FastAPI:
    app = FastAPI(title="TaskBox API", version="1.0.0")
    db = SQLiteDatabase(database_url or os.getenv("TASKBOX_DATABASE_URL", "sqlite:///taskbox.db"))
    tokens = JWTTokenIssuer(
        jwt_secret or os.getenv("TASKBOX_JWT_SECRET", "dev-only-change-me"),
        expires_seconds=int(os.getenv("TASKBOX_JWT_EXPIRES", "3600")),
    )
    from types import SimpleNamespace

    factory = db.transaction
    app.state.database = db
    app.state.services = SimpleNamespace(
        token_expires=tokens.expires_seconds,
        auth=AuthApplicationService(factory, Argon2PasswordHasher(), tokens),
        projects=ProjectApplicationService(factory),
        tasks=TaskApplicationService(factory),
        webhooks=WebhookImportApplicationService(
            factory,
            HMACWebhookSignatureVerifier(
                webhook_secret or os.getenv("TASKBOX_WEBHOOK_SECRET", "dev-webhook-secret")
            ),
        ),
    )
    app.include_router(router)

    @app.exception_handler(TaskBoxError)
    async def domain_error(request: Request, exc: TaskBoxError):
        return _problem(request, exc.status_code, exc.detail, exc.code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {
                "loc": list(error.get("loc", [])),
                "msg": error.get("msg", "invalid value"),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        return _problem(request, 422, "request validation failed", "validation_error", errors)

    @app.get("/healthz", tags=["Auth"])
    @app.get("/livez", tags=["Auth"], include_in_schema=False)
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["Auth"], include_in_schema=False)
    async def readyz():
        db.connection.execute("SELECT 1")
        return {"status": "ok"}

    return app


app = create_app()

__all__ = ["app", "create_app"]
