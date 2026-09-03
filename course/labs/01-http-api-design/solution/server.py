"""A deliberately small HTTP implementation matching openapi.yaml."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body, content_type="application/json"):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/v1/hello":
            self.send_json(200, {"message": "Hello, API engineer!"})
        else:
            self.send_json(404, {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Route does not exist"}, "application/problem+json")

    def do_POST(self):
        if self.path != "/api/v1/echo":
            self.send_json(404, {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Route does not exist"}, "application/problem+json")
            return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("content-length", "0"))))
            message = data["message"]
            if not isinstance(message, str) or not 1 <= len(message) <= 200:
                raise ValueError
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            self.send_json(400, {"type": "about:blank", "title": "Bad Request", "status": 400, "detail": "message must be a non-empty string of at most 200 characters"}, "application/problem+json")
            return
        self.send_json(200, {"message": message})


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
