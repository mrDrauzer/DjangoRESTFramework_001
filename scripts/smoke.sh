#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

echo "[smoke] Checking base URL: ${BASE_URL}"

check() {
  local url="$1"
  echo "[smoke] GET ${url}"
  curl -fsS -m 10 -o /dev/null "$url"
}

check "${BASE_URL}/"
check "${BASE_URL}/api/docs/"

echo "[smoke] OK: ${BASE_URL} is responsive"
