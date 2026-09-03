"""A dependency-free client for TaskBox-style JSON endpoints."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000/api/v1/notes"


def request(method: str, url: str, payload: dict | None = None) -> tuple[int, object]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {} if data is None else {"content-type": "application/json"}
    try:
        with urlopen(Request(url, data=data, headers=headers, method=method)) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


if __name__ == "__main__":
    status, note = request("POST", BASE_URL, {"title": "Client example", "body": "Hello API"})
    print(f"POST {status}: {note}")
    status, notes = request("GET", BASE_URL)
    print(f"GET {status}: {notes}")
