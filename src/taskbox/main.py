"""TaskBox FastAPI composition root."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from taskbox.adapters.security import (
    Argon2PasswordHasher,
    HMACWebhookSignatureVerifier,
    JWTTokenIssuer,
)
from taskbox.adapters.sqlite import SQLiteDatabase
from taskbox.api.routes import router
from taskbox.api.schemas import HealthResponse, PageInfo, ProblemDetail, WebhookImportRequest
from taskbox.application.services import (
    AuthApplicationService,
    ProjectApplicationService,
    TaskApplicationService,
    WebhookImportApplicationService,
)
from taskbox.domain.errors import TaskBoxError

_DEFAULT_JWT_SECRET = "dev-only-change-me"
_DEFAULT_WEBHOOK_SECRET = "dev-webhook-secret"
_INSECURE_DEVELOPMENT_SECRETS = frozenset(
    {_DEFAULT_JWT_SECRET, _DEFAULT_WEBHOOK_SECRET, "change-me-in-development"}
)
_LOCAL_ENVIRONMENTS = frozenset({"development", "local", "test", "testing"})


def _configured_secret(
    explicit_value: str | None, environment_variable: str, default: str
) -> str:
    """Resolve a factory override before environment configuration."""
    if explicit_value is not None:
        return explicit_value
    return os.getenv(environment_variable, default)


def _validate_runtime_secrets(*, environment: str, jwt_secret: str, webhook_secret: str) -> None:
    """Reject unsafe secret configuration before opening the local database."""
    for setting, value in (
        ("TASKBOX_JWT_SECRET", jwt_secret),
        ("TASKBOX_WEBHOOK_SECRET", webhook_secret),
    ):
        if not value.strip():
            raise RuntimeError(f"{setting} must not be empty")
        if environment not in _LOCAL_ENVIRONMENTS and value in _INSECURE_DEVELOPMENT_SECRETS:
            raise RuntimeError(
                f"{setting} uses an insecure development value while TASKBOX_ENV={environment!r}; "
                "configure a long random secret before starting TaskBox"
            )


def _problem(
    request: Request,
    status_code: int,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"{str(request.base_url).rstrip('/')}/problems/{code}",
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
    environment = os.getenv("TASKBOX_ENV", "development").strip().lower()
    configured_jwt_secret = _configured_secret(
        jwt_secret, "TASKBOX_JWT_SECRET", _DEFAULT_JWT_SECRET
    )
    configured_webhook_secret = _configured_secret(
        webhook_secret, "TASKBOX_WEBHOOK_SECRET", _DEFAULT_WEBHOOK_SECRET
    )
    _validate_runtime_secrets(
        environment=environment,
        jwt_secret=configured_jwt_secret,
        webhook_secret=configured_webhook_secret,
    )

    app = FastAPI(
        title="TaskBox API",
        version="1.0.0",
        description="A project task API used throughout the API Engineering course.",
        servers=[{"url": "http://localhost:8000", "description": "Local development"}],
        openapi_tags=[
            {"name": tag} for tag in ("Health", "Auth", "Projects", "Tasks", "Webhooks")
        ],
    )
    db = SQLiteDatabase(database_url or os.getenv("TASKBOX_DATABASE_URL", "sqlite:///taskbox.db"))
    tokens = JWTTokenIssuer(
        configured_jwt_secret,
        expires_seconds=int(os.getenv("TASKBOX_JWT_EXPIRES", "3600")),
    )
    factory = db.transaction
    app.state.database = db
    app.state.services = SimpleNamespace(
        token_expires=tokens.expires_seconds,
        auth=AuthApplicationService(factory, Argon2PasswordHasher(), tokens),
        projects=ProjectApplicationService(factory),
        tasks=TaskApplicationService(factory),
        webhooks=WebhookImportApplicationService(
            factory,
            HMACWebhookSignatureVerifier(configured_webhook_secret),
        ),
    )
    app.include_router(router)

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        document = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        schemas = document.setdefault("components", {}).setdefault("schemas", {})
        schemas["ProblemDetail"] = ProblemDetail.model_json_schema()
        schemas["WebhookImportRequest"] = WebhookImportRequest.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        schemas["PageInfo"] = PageInfo.model_json_schema()
        # A Bearer token is accepted to select an actor but is not required for
        # this signed webhook boundary, so it has no OpenAPI security requirement.
        document["paths"]["/api/v1/webhooks/tasks/import"]["post"].pop("security", None)
        app.openapi_schema = document
        return document

    app.openapi = custom_openapi  # type: ignore[method-assign]

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

    @app.get("/healthz", response_model=HealthResponse, tags=["Health"], operation_id="healthCheck")
    @app.get("/livez", tags=["Health"], include_in_schema=False)
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["Health"], include_in_schema=False)
    async def readyz():
        db.run(lambda connection: connection.execute("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()

__all__ = ["app", "create_app"]
