---
title: "Module 9: Realtime delivery"
description: Choose WebSockets or SSE from the interaction model.
---

Realtime is a delivery contract, not simply “an endpoint that stays open.” Decide whether the client sends commands over the connection, whether events can be replayed, how long a connection may live, and what happens when a consumer is slow or offline.

## Learning objectives

- choose WebSockets or Server-Sent Events (SSE) from the interaction shape;
- track connections and clean them up on disconnect;
- define event names, payload versions, heartbeats, and backpressure;
- build clients that reconnect without duplicating visible work.

## Two useful shapes

WebSockets are bidirectional. A browser or service can send a command and receive updates on the same connection, which suits collaboration, presence, and interactive task editing. The client must handle close codes, authentication lifetime, and reconnect behavior. A WebSocket is not automatically durable: an event sent while a client is disconnected is gone unless the server provides a replay mechanism.

SSE is one-way server-to-browser delivery over ordinary HTTP. The server writes `text/event-stream` frames containing an event name, optional ID, and data. Browsers provide `EventSource` with automatic reconnection and `Last-Event-ID`, making SSE a good fit for notifications, progress, and dashboards. When the browser must send commands, use normal HTTP alongside the stream.

## Connection lifecycle

The Lab 09 solution broadcasts task updates through both transports and sends an SSE heartbeat. Keep a set of active connections, add a client after successful handshake, and remove it in a `finally` block. Treat a failed send as a disconnect; never leave a dead socket in the registry.

```python
clients: set[WebSocket] = set()

async def websocket_endpoint(socket: WebSocket):
    await socket.accept()
    clients.add(socket)
    try:
        while True:
            message = await socket.receive_json()
            await broadcast({"type": "task.updated", "data": message})
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(socket)
```

Bound every queue. A slow consumer must be disconnected, sampled, or served from a bounded replay buffer; it must not grow process memory forever. Heartbeats keep intermediaries from closing idle connections and let both sides detect failure. Include an event version so clients can evolve independently, and use stable IDs when deduplication or replay matters.

## Practice and verification

Run the lab and clients:

```bash
cd course/labs/09-realtime
uv run uvicorn solution.app:app --port 8009
websocat ws://127.0.0.1:8009/ws
curl -N http://127.0.0.1:8009/events
```

The Python clients live in [course/examples/realtime](https://github.com/ialimustufa/API/tree/main/course/examples/realtime). Connect two clients, send a JSON task update, and confirm both receive it. Close one client and check that later broadcasts do not fail. Leave an SSE client idle long enough to observe heartbeats. Inspect response content types and verify a bounded queue policy.

Exercise: add an event ID and a reconnect cursor. Decide whether replay is required for TaskBox; if it is, document retention and what happens when the cursor is older than the retained history. Add tests for duplicate delivery because reconnects make duplicates normal.

Design the wire format before adding more event types. A useful envelope includes `id`, `type`, `version`, `occurred_at`, and `data`; clients can ignore fields they do not understand and dispatch by type. Separate a task update from a connection error so a client does not accidentally render an operational message as domain data. For multiple API instances, an in-process set is insufficient: use a shared broker or explicitly document the single-instance limit.

## Pitfalls and next steps

Do not use an unbounded list of connections, assume disconnects are orderly, or send arbitrary internal objects as JSON. Authenticate the handshake, authorize subscriptions, cap message size, and apply origin and rate checks where appropriate. A reverse proxy also needs explicit idle and buffering settings for streams.

Next, apply the same authenticity and retry thinking to inbound traffic in [Module 10: Webhooks and events](../10-webhooks-events/).
