FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "taskbox.main:app", "--host", "0.0.0.0", "--port", "8000"]
