from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskbox.domain.models import User

bearer = HTTPBearer(auto_error=False)


def services(request: Request):
    return request.app.state.services


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), request: Request = None
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return request.app.state.services.auth.current_user(credentials.credentials)
    except Exception as exc:
        # Domain error handlers are installed on the app; preserving the domain
        # exception gives the RFC 9457 response its stable code.
        from taskbox.domain.errors import AuthenticationError

        if isinstance(exc, AuthenticationError):
            raise
        raise AuthenticationError("authentication required") from exc


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), request: Request = None
) -> User | None:
    if not credentials:
        return None
    return current_user(credentials, request)


__all__ = ["current_user", "optional_user", "services"]
