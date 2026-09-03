import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
log = logging.getLogger("taskbox")
url = os.getenv("TASKBOX_DATABASE_URL", "sqlite:///./taskbox-ops.db")
engine = create_engine(
    url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
)
app = FastAPI(title="TaskBox operations lab")


@app.middleware("http")
async def request_context(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id", os.urandom(8).hex())
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request_failed request_id=%s path=%s", request_id, request.url.path)
        raise
    response.headers["x-request-id"] = request_id
    log.info(
        "request_complete request_id=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
    )
    return response


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
