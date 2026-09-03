from fastapi import FastAPI
app = FastAPI(title="TaskBox webhook lab")
@app.post("/api/v1/webhooks/import")
async def import_event():
    # TODO: verify the raw body signature, timestamp, and event-id idempotency.
    raise NotImplementedError
