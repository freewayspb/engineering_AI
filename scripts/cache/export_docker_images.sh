#!/usr/bin/env bash
set -euo pipefail

# Экспортирует используемые образы в ./artifacts/docker-images.tar

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
mkdir -p "${ARTIFACTS_DIR}"

IMAGES=(
  "ollama/ollama:latest"
  "ba-ai-gost-backend:ci"
)

echo "[cache] Saving images to ${ARTIFACTS_DIR}/docker-images.tar"
docker save -o "${ARTIFACTS_DIR}/docker-images.tar" "${IMAGES[@]}"
ls -lh "${ARTIFACTS_DIR}/docker-images.tar"
echo "[cache] Done"


