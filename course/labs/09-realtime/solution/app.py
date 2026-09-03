import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
app = FastAPI(title="TaskBox realtime lab")
clients: set[WebSocket] = set()
async def broadcast(event: dict):
    dead = set()
    for client in clients:
        try: await client.send_json(event)
        except Exception: dead.add(client)
    clients.difference_update(dead)
@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept(); clients.add(ws)
    try:
        while True: await broadcast({"event": "task.updated", "data": await ws.receive_json()})
    except WebSocketDisconnect: clients.discard(ws)
async def events():
    while True:
        yield "event: heartbeat\ndata: {}\n\n"; await asyncio.sleep(15)
@app.get("/events")
async def sse(): return StreamingResponse(events(), media_type="text/event-stream", headers={"cache-control": "no-cache"})
