"""Errors raised by the TaskBox domain.

The application layer can translate these exceptions to RFC 9457 problem
details without coupling the domain to FastAPI (or any other web framework).
"""

from __future__ import annotations


class TaskBoxError(Exception):
    """Base class for expected, client-visible domain failures."""

    code = "taskbox_error"
    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class ValidationError(TaskBoxError):
    code = "validation_error"
    status_code = 422


class AuthenticationError(TaskBoxError):
    code = "authentication_required"
    status_code = 401


class AuthorizationError(TaskBoxError):
    code = "forbidden"
    status_code = 403


class NotFoundError(TaskBoxError):
    code = "not_found"
    status_code = 404


class ConflictError(TaskBoxError):
    code = "conflict"
    status_code = 409


class InvalidCursorError(TaskBoxError):
    code = "invalid_cursor"
    status_code = 400


class InvalidWebhookSignatureError(TaskBoxError):
    code = "invalid_webhook_signature"
    status_code = 401


class DuplicateWebhookError(ConflictError):
    code = "duplicate_webhook"


class PersistenceError(TaskBoxError):
    code = "persistence_error"
    status_code = 500


__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "DuplicateWebhookError",
    "InvalidCursorError",
    "InvalidWebhookSignatureError",
    "NotFoundError",
    "PersistenceError",
    "TaskBoxError",
    "ValidationError",
]
