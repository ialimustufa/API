"""Small thread-safe in-memory repository used by the teaching API."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .models import Joke


class JokeStore:
    """Repository with per-instance state so app factories remain isolated."""

    def __init__(self, seed: list[Joke] | None = None) -> None:
        self._lock = RLock()
        self._jokes: dict[int, Joke] = {joke.id: joke for joke in (seed or default_jokes())}
        self._next_id = max(self._jokes, default=-1) + 1

    def list(self, *, author: str | None = None, query: str | None = None) -> list[Joke]:
        author_term = author.casefold() if author else None
        query_term = query.casefold() if query else None
        with self._lock:
            result = list(self._jokes.values())
        if author_term:
            result = [item for item in result if author_term in item.author.casefold()]
        if query_term:
            result = [
                item
                for item in result
                if query_term in item.author.casefold() or query_term in item.joke.casefold()
            ]
        return sorted(result, key=lambda item: item.id)

    def get(self, joke_id: int) -> Joke | None:
        with self._lock:
            return self._jokes.get(joke_id)

    def random(self, *, author: str | None = None, query: str | None = None) -> Joke | None:
        # Deterministic selection of the first matching record is friendlier to
        # examples and tests than making randomness part of the API contract.
        return next(iter(self.list(author=author, query=query)), None)

    def create(self, *, author: str, joke: str, source: str | None) -> Joke:
        with self._lock:
            item = Joke(self._next_id, author, joke, source)
            self._jokes[item.id] = item
            self._next_id += 1
            return item

    def replace(self, joke_id: int, *, author: str, joke: str, source: str | None) -> Joke | None:
        with self._lock:
            current = self._jokes.get(joke_id)
            if current is None:
                return None
            updated = replace(current, author=author, joke=joke, source=source)
            self._jokes[joke_id] = updated
            return updated

    def delete(self, joke_id: int) -> bool:
        with self._lock:
            return self._jokes.pop(joke_id, None) is not None


def default_jokes() -> list[Joke]:
    """Neutral, original seed records for demonstrations."""

    return [
        Joke(
            0,
            "Course Bot",
            "Why did the API answer quickly? It had a good route.",
            None,
        ),
        Joke(
            1,
            "Course Bot",
            "A well-shaped request is a small act of kindness.",
            None,
        ),
    ]
