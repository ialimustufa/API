FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    TASKBOX_ENV=production \
    TASKBOX_DATABASE_URL=sqlite:////data/taskbox.db
WORKDIR /app
RUN pip install --no-cache-dir uv
RUN groupadd --system taskbox
RUN useradd --system --gid taskbox --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin taskbox
RUN install --directory --owner=taskbox --group=taskbox /data
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev
EXPOSE 8000
USER taskbox
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()"]
CMD ["/app/.venv/bin/uvicorn", "taskbox.main:app", "--host", "0.0.0.0", "--port", "8000"]
