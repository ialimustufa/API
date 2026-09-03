from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(length) or b"{}")
        query = body.get("query", "")
        if "tasks" not in query:
            payload = {"errors": [{"message": "Only the tasks query is available"}]}; code = 400
        else:
            payload = {"data": {"tasks": [{"id": "1", "title": "Learn GraphQL"}]}}; code = 200
        raw = json.dumps(payload).encode(); self.send_response(code); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
if __name__ == "__main__": HTTPServer(("127.0.0.1", 8010), Handler).serve_forever()
