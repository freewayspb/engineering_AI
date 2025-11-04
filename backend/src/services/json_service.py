from __future__ import annotations

import json

import asyncio
import tempfile
from pathlib import Path
from .compat_asyncio import to_thread

from fastapi import HTTPException, UploadFile

from .console_json_ollama import run_console_json_ollama
from .dxf_console_service import convert_dxf_upload_to_json

async def process_json_query(json_file: str, question: str) -> dict:
    filename = json_file or "uploaded.json"
    suffix = Path(filename).suffix.lower()

    intermediate_path: Path | None = None

    if suffix in {".dxf", ".dwg"}:
        converted_payload = await convert_dxf_upload_to_json(json_file)

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".json", delete=False
        ) as converted_file:
            json.dump(converted_payload, converted_file, indent=2, ensure_ascii=False)
            intermediate_path = Path(converted_file.name)

        try:
            raw_bytes = intermediate_path.read_bytes()
        except FileNotFoundError as exc:  # pragma: no cover - unexpected filesystem failure
            raise HTTPException(
                status_code=500,
                detail="Failed to materialize DXF conversion output.",
            ) from exc
    else:
        raw_bytes = await json_file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Uploaded JSON file is empty")

    try:
        parsed_json = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid UTF-8 JSON") from exc
    finally:
        if intermediate_path is not None:
            intermediate_path.unlink(missing_ok=True)

    serialized_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)

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

