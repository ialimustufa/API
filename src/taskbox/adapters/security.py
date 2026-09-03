"""Local security adapters: Argon2 password hashing and JWT tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import jwt
from pwdlib import PasswordHash

from taskbox.domain.errors import AuthenticationError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password, password_hash)
        except Exception:
            return False


class JWTTokenIssuer:
    def __init__(self, secret_key: str, *, algorithm: str = "HS256", expires_seconds: int = 3600, issuer: str = "taskbox") -> None:
        self.secret_key, self.algorithm, self.expires_seconds, self.issuer = secret_key, algorithm, expires_seconds, issuer

    def issue(self, *, subject: str, claims: Mapping[str, Any] | None = None, expires_at: datetime | None = None) -> str:
        now = datetime.now(timezone.utc)
        expiration = expires_at or now + timedelta(seconds=self.expires_seconds)
        payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": expiration, "iss": self.issuer}
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify(self, token: str) -> Mapping[str, Any]:
        try:
            claims = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], issuer=self.issuer)
            if not claims.get("sub"):
                raise AuthenticationError("token subject is missing")
            return claims
        except AuthenticationError:
            raise
        except jwt.PyJWTError as exc:
            raise AuthenticationError("invalid or expired token") from exc


class HMACWebhookSignatureVerifier:
    def __init__(self, secret: str) -> None:
        self.secret = secret.encode()

    def verify(self, *, payload: bytes, signature: str) -> bool:
        import hashlib
        import hmac

        expected = hmac.new(self.secret, payload, hashlib.sha256).hexdigest()
        provided = signature.removeprefix("sha256=")
        return hmac.compare_digest(expected, provided)


__all__ = ["Argon2PasswordHasher", "HMACWebhookSignatureVerifier", "JWTTokenIssuer"]
