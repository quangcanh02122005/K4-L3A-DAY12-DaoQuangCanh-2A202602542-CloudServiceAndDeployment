#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://k4-l3a-day12-daoquangcanh-2a202602542-cloudservi-production.up.railway.app}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${DEPLOY_API_KEY:?Hãy đặt DEPLOY_API_KEY trong .env}"

echo "=== Test /health ==="
curl -s "$BASE_URL/health"

echo -e "\n\n=== Test /ready ==="
curl -s "$BASE_URL/ready"

echo -e "\n\n=== Test /ask ==="
curl -s -X POST "$BASE_URL/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DEPLOY_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question": "Hello!"}'

echo ""
