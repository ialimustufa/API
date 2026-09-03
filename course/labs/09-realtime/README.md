# Lab 09: WebSockets and Server-Sent Events

Choose a transport from its delivery shape. WebSockets provide bidirectional
conversation; SSE provides server-to-browser events over ordinary HTTP. The
solution broadcasts task updates to both transports and sends an SSE heartbeat.

Run `uv run uvicorn solution.app:app --port 8009`, then use `websocat
ws://127.0.0.1:8009/ws` or `curl -N http://127.0.0.1:8009/events`.
The starter leaves connection tracking and disconnect cleanup as TODOs.
