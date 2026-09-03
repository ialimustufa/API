#!/usr/bin/env sh
set -eu
base="${API_BASE_URL:-http://127.0.0.1:8000/api/v1/notes}"
curl --fail-with-body -sS -X POST "$base" \
  -H 'content-type: application/json' \
  -d '{"title":"curl example","body":"Hello API"}'
printf '\n'
curl --fail-with-body -sS "$base"
printf '\n'
