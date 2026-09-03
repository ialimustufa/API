# Lab 02: FastAPI basics

Build a small, typed API and inspect the generated OpenAPI docs. The starter
has the route and model skeletons; implement the TODOs before looking at the
solution.

From this directory run `uv run uvicorn solution.app:app --reload` (or use the
equivalent command in your environment), then open `/docs`. The project root
declares FastAPI and Uvicorn; no additional package is required for this lab.

Try `GET /api/v1/greetings?name=Ada` and `POST /api/v1/greetings` with
`{"name":"Ada"}`. FastAPI validates the request and serializes the response.
