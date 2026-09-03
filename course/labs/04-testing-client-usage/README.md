# Lab 04: Testing and client usage

Use an in-process FastAPI client to test behavior without starting a server,
then call the same API over HTTP with a small client. The solution depends on
the project’s declared FastAPI, HTTPX, and pytest dependencies.

Run the tests with `uv run pytest solution/test_app.py -q`. Start the CRUD API
from Lab 03 in another terminal and run `uv run python client.py` from this
directory. The starter test contains TODO assertions; the solution shows
status-code, validation, and round-trip assertions.
