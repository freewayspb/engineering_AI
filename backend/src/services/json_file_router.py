from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, UploadFile

from .dxf_console_service import convert_dxf_upload_to_json

Handler = Callable[[UploadFile], Awaitable[dict[str, Any]]]

HANDLER_MAP: Dict[str, Handler] = {
    ".dxf": convert_dxf_upload_to_json,
    ".dwg": convert_dxf_upload_to_json,
}


async def load_raw_json_data(json_file: UploadFile) -> bytes:
    if json_file is None:
        raise HTTPException(status_code=400, detail="JSON file is required")

    filename = json_file.filename or "uploaded.json"
    suffix = Path(filename).suffix.lower()

    handler = HANDLER_MAP.get(suffix)

    if handler is None:
        raw_bytes = await json_file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Uploaded JSON file is empty")
        return raw_bytes

    converted_payload = await handler(json_file)

    return json.dumps(converted_payload, indent=2, ensure_ascii=False);

