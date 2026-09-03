import hashlib, hmac, os, time
from fastapi import FastAPI, HTTPException, Request
app = FastAPI(title="TaskBox webhook lab")
SECRET = os.getenv("TASKBOX_WEBHOOK_SECRET", "dev-webhook-secret"); seen: set[str] = set()
def verify(raw: bytes, header: str, now: int | None = None):
    try:
        values = dict(part.split("=", 1) for part in header.split(",")); timestamp = int(values["t"]); signature = values["v1"]
    except (KeyError, ValueError): raise HTTPException(400, "Malformed signature")
    if abs((now or int(time.time())) - timestamp) > 300: raise HTTPException(400, "Expired signature")
    expected = hmac.new(SECRET.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature): raise HTTPException(401, "Invalid signature")
@app.post("/api/v1/webhooks/import")
async def import_event(request: Request):
    raw = await request.body(); verify(raw, request.headers.get("x-taskbox-signature", "")); event = await request.json(); event_id = event.get("id")
    if not event_id: raise HTTPException(400, "Event id is required")
    if event_id in seen: return {"accepted": True, "duplicate": True}
    seen.add(event_id); return {"accepted": True, "duplicate": False}
