# Client examples

These examples show the same API from a caller’s point of view. Start a lab
server first, then run the Python example with `uv run python python_client.py`
or copy the curl commands. The Python client uses only the standard library;
HTTPX is shown separately for projects that already use it.

The examples assume the CRUD service is listening on `http://127.0.0.1:8000`.
Change `BASE_URL` when your service uses another port.
