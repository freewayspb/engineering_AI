#!/usr/bin/env bash
set -euo pipefail

BASE_MODEL=${BASE_MODEL:-"llama3.1:8b"}

echo "[1/4] Pull base model: ${BASE_MODEL}"
ollama pull "${BASE_MODEL}" || true

echo "[2/4] Pull deepseek-r1 model (for JSON queries)"
if ollama pull "deepseek-r1" 2>/dev/null; then
    echo "  ✓ deepseek-r1 installed"
elif ollama pull "deepseek-r1:8b" 2>/dev/null; then
    echo "  ✓ deepseek-r1:8b installed, creating alias 'deepseek-r1'"
    # Создаем алиас для совместимости с кодом
    echo "FROM deepseek-r1:8b" | ollama create deepseek-r1 -f - 2>/dev/null || echo "  ⚠ Alias creation skipped (may already exist)"
else
    echo "  ⚠ Warning: deepseek-r1 model not found. Trying alternative..."
    if ollama pull "deepseek-r1:1.5b" 2>/dev/null; then
        echo "  ✓ deepseek-r1:1.5b installed, creating alias 'deepseek-r1'"
        echo "FROM deepseek-r1:1.5b" | ollama create deepseek-r1 -f - 2>/dev/null || echo "  ⚠ Alias creation skipped"
    else
        echo "  ✗ Failed to install deepseek-r1"
    fi
fi

echo "[3/4] Pull llava model (for vision queries)"
if ollama pull "llava" 2>/dev/null; then
    echo "  ✓ llava installed"
else
    echo "  ⚠ Warning: llava model installation failed"
fi

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
      echo "Creating model ${name} (temp modelfile: $temp)"
  ollama create "$name" -f "$temp" || true
  rm -f "$temp"
}

gen_and_create agent-classify    "${ROOT_DIR}/prompts/classify.system"     0.2
gen_and_create agent-doc-extract "${ROOT_DIR}/prompts/doc_extract.system"  0.1
gen_and_create agent-qa          "${ROOT_DIR}/prompts/qa.system"           0.3

echo "Done. Models installed:"
echo "  - Base: ${BASE_MODEL}"
echo "  - deepseek-r1 (for JSON queries)"
echo "  - llava (for vision queries)"
echo "  - agent-classify"
echo "  - agent-doc-extract"
echo "  - agent-qa"


