#!/usr/bin/env bash
set -euo pipefail

# Импортирует образы из ./artifacts/docker-images.tar

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
ARCHIVE="${ARTIFACTS_DIR}/docker-images.tar"

if [ ! -f "$ARCHIVE" ]; then
  echo "[cache] Archive not found: $ARCHIVE"
  exit 1
fi

echo "[cache] Loading images from $ARCHIVE"
docker load -i "$ARCHIVE"
echo "[cache] Done"


