#!/usr/bin/env bash
set -euo pipefail

# Экспортирует volume ollama в архив ./artifacts/ollama-models.tgz

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
mkdir -p "${ARTIFACTS_DIR}"

echo "[cache] Exporting volume 'ollama' to ${ARTIFACTS_DIR}/ollama-models.tgz"
docker run --rm \
  -v ollama:/data \
  -v "${ARTIFACTS_DIR}:/backup" \
  alpine:3.20 \
  sh -lc "tar czf /backup/ollama-models.tgz -C /data . && ls -lh /backup/ollama-models.tgz"

echo "[cache] Done"


