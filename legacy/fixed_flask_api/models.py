"""Data objects and boundary validation for the corrected jokes API."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


class ValidationError(ValueError):
    """A client supplied value did not satisfy the API contract."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class MalformedJSONError(ValidationError):
    """The request body could not be decoded as JSON (HTTP 400)."""


@dataclass(frozen=True, slots=True)
class Joke:
    id: int
    author: str
    joke: str
    source: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "author": self.author,
            "joke": self.joke,
            "source": self.source,
        }


def validate_joke_payload(payload: object) -> dict[str, str | None]:
    """Validate and normalize a create/replace payload.

    Keeping this validation dependency-free makes the archived example easy to
    run in a notebook while retaining the same boundary rules as the course.
    """

    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    allowed = {"author", "joke", "source"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(str(value) for value in unknown)}.")

    values: dict[str, str | None] = {}
    for field, maximum in (("author", 120), ("joke", 5000)):
        value = payload.get(field)
        if not isinstance(value, str):
            raise ValidationError(f"'{field}' must be a string.", field)
        value = value.strip()
        if not value:
            raise ValidationError(f"'{field}' must not be empty.", field)
        if len(value) > maximum:
            raise ValidationError(f"'{field}' must be at most {maximum} characters.", field)
        values[field] = value

    source = payload.get("source")
    if source is not None:
        if not isinstance(source, str):
            raise ValidationError("'source' must be a string or null.", "source")
        source = source.strip()
        parsed = urlsplit(source)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("'source' must be an absolute HTTP(S) URL.", "source")
    values["source"] = source
    return values
