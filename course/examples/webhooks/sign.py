"""Signer for the timestamped Lab 10 receiver, not the TaskBox reference API."""

import hashlib
import hmac
import json
import time

secret = b"dev-webhook-secret"
timestamp = int(time.time())
body = json.dumps({"id": "evt_1", "type": "task.created"}).encode()
signature = hmac.new(secret, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
print(f"X-TaskBox-Signature: t={timestamp},v1={signature}")
print(body.decode())
