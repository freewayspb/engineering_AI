#!/usr/bin/env bash
set -euo pipefail

BASE_MODEL=${BASE_MODEL:-"llama3.1:8b"}

echo "[1/3] Pull base model: ${BASE_MODEL}"
ollama pull "${BASE_MODEL}" || true

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

gen_and_create() {
  local name=$1
  local temp=$(mktemp)
  local system_file=$2
  local temperature=$3
  echo "FROM ${BASE_MODEL}" > "$temp"
  echo "SYSTEM \"\"\"" >> "$temp"
  cat "$system_file" >> "$temp"
  echo "\"\"\"" >> "$temp"
  echo "PARAMETER temperature ${temperature}" >> "$temp"
  echo "[2/3] Create model ${name} (temp modelfile: $temp)"
  ollama create "$name" -f "$temp" || true
  rm -f "$temp"
}

gen_and_create agent-classify    "${ROOT_DIR}/prompts/classify.system"     0.2
gen_and_create agent-doc-extract "${ROOT_DIR}/prompts/doc_extract.system"  0.1
gen_and_create agent-qa          "${ROOT_DIR}/prompts/qa.system"           0.3

echo "[3/3] Done. Models: agent-classify, agent-doc-extract, agent-qa"


