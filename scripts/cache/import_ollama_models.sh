#!/usr/bin/env bash
set -euo pipefail

# Импортирует архив ./artifacts/ollama-models.tgz в volume ollama

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
ARCHIVE="${ARTIFACTS_DIR}/ollama-models.tgz"

if [ ! -f "$ARCHIVE" ]; then
  echo "[cache] Archive not found: $ARCHIVE"
  exit 1
fi

echo "[cache] Importing $ARCHIVE into volume 'ollama'"
docker run --rm \
  -v ollama:/data \
  -v "${ARTIFACTS_DIR}:/backup" \
  alpine:3.20 \
  sh -lc "rm -rf /data/* && tar xzf /backup/ollama-models.tgz -C /data && ls -lah /data | head -50"

echo "[cache] Done"


