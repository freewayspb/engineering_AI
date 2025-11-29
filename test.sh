#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 \"<question>\" <json_file>" >&2
  exit 64
fi

QUESTION="$1"
JSON_FILE="$2"
JSON_QUERY_URL="${JSON_QUERY_URL:-http://localhost:8080/json-query}"

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required but not installed." >&2
  exit 127
fi

if [[ ! -f "$JSON_FILE" ]]; then
  echo "Error: JSON file not found: $JSON_FILE" >&2
  exit 66
fi

curl -sS -X POST "$JSON_QUERY_URL" \
  -F "json_file=@${JSON_FILE}" \
  --form-string "question=${QUESTION}"

