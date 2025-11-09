from __future__ import annotations

import json

import tempfile
from pathlib import Path
from .utils.compat_asyncio import to_thread

from fastapi import HTTPException, UploadFile

from .console_json_ollama import run_console_json_ollama
from .json_file_router import load_raw_json_data

async def process_json_query(json_file: UploadFile, question: str) -> dict:
    if json_file is None:
        raise HTTPException(status_code=400, detail="JSON file is required")

    serialized_json = await load_raw_json_data(json_file)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
        temp_file.write(serialized_json)
        temp_path = Path(temp_file.name)

    try:
        result = await to_thread(
            run_console_json_ollama,
            question,
            str(temp_path),
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "model": result.get("model", "deepseek-r1"),
        "response": result.get("response"),
        "prompt": result.get("prompt"),
    }

