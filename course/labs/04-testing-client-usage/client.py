"""Tiny standard HTTP client; point it at the running Lab 03 server."""
import json
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000/api/v1/notes"
request = Request(
    BASE_URL,
    data=json.dumps({"title": "From a client", "body": "hi"}).encode(),
    headers={"content-type": "application/json"},
    method="POST",
)
with urlopen(request) as response:
    print(response.status, json.load(response))
