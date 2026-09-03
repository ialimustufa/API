"""Create headers and a body for TaskBox's raw-body HMAC webhook endpoint.

Set TASKBOX_PROJECT_ID and TASKBOX_ACTOR_ID from a TaskBox project before
sending the printed body to POST /api/v1/webhooks/tasks/import.
"""

import hashlib
import hmac
import json
import os
import uuid

secret = os.getenv("TASKBOX_WEBHOOK_SECRET", "dev-webhook-secret").encode()
event_id = os.getenv("TASKBOX_WEBHOOK_EVENT_ID", f"evt-{uuid.uuid4()}")
body = json.dumps(
    {
        "project_id": os.environ["TASKBOX_PROJECT_ID"],
        "actor_id": os.environ["TASKBOX_ACTOR_ID"],
        "tasks": [{"title": "Imported vendor task", "priority": 2}],
    },
    separators=(",", ":"),
).encode()
signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

print(f"X-Webhook-Event-ID: {event_id}")
print(f"X-Webhook-Signature: sha256={signature}")
print(body.decode())
