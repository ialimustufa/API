"""Configuration-driven HTTP Basic Authentication."""

from __future__ import annotations

import base64
import binascii
import hmac
import os

try:
    from werkzeug.security import check_password_hash, generate_password_hash
except ImportError:  # pragma: no cover - Flask installs Werkzeug alongside it.
    check_password_hash = None  # type: ignore[assignment]
    generate_password_hash = None  # type: ignore[assignment]


REALM = "legacy-jokes-api"


def configured_credentials(config: dict[str, object]) -> tuple[str, str | None]:
    """Read a username and a Werkzeug password hash from config/environment."""

    username = str(
        config.get("AUTH_USERNAME")
        or os.environ.get("LEGACY_API_USERNAME")
        or "admin"
    )
    password_hash = config.get("AUTH_PASSWORD_HASH") or os.environ.get(
        "LEGACY_API_PASSWORD_HASH"
    )
    # AUTH_PASSWORD is intentionally a config-only convenience for tests and
    # local exercises; deployed environments should provide the hash instead.
    password = config.get("AUTH_PASSWORD")
    if (
        not password_hash
        and isinstance(password, str)
        and password
        and generate_password_hash
    ):
        password_hash = generate_password_hash(password)
    return username, str(password_hash) if password_hash else None


def authenticate(
    authorization: str | None, username: str, password_hash: str | None
) -> bool:
    if not authorization or not password_hash or check_password_hash is None:
        return False
    scheme, separator, encoded = authorization.partition(" ")
    if separator == "" or scheme.casefold() != "basic":
        return False
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return False
    supplied_username, separator, supplied_password = decoded.partition(":")
    if separator == "":
        return False
    if not hmac.compare_digest(supplied_username, username):
        return False
    try:
        return check_password_hash(password_hash, supplied_password)
    except (ValueError, TypeError):
        # A malformed configured hash must never turn an authentication attempt
        # into an internal server error.
        return False
