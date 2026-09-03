from fastapi import FastAPI
app = FastAPI(title="TaskBox operations lab")
@app.get("/healthz")
def health():
    # TODO: return a process-level 200 health response.
    raise NotImplementedError
@app.get("/readyz")
def ready():
    # TODO: check the configured database and return 503 when unavailable.
    raise NotImplementedError
