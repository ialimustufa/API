from fastapi import FastAPI, WebSocket
app = FastAPI(title="TaskBox realtime lab")
@app.websocket("/ws")
async def websocket(ws: WebSocket):
    # TODO: accept, track, broadcast JSON messages, and remove disconnects.
    raise NotImplementedError
