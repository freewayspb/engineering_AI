from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, UploadFile

from .file_handlers.dxf_console_service import convert_dxf_upload_to_json
from .file_handlers.gsfx_upload_service import convert_gsfx_upload_to_json
from .file_handlers.arp_upload_service import convert_arp_upload_to_json
from .file_handlers.rtf_upload_service import convert_rtf_upload_to_json
from .file_handlers.xlsx_upload_service import convert_xlsx_upload_to_json

Handler = Callable[[UploadFile], Awaitable[dict[str, Any]]]

HANDLER_MAP: Dict[str, Handler] = {
    ".dxf": convert_dxf_upload_to_json,
    ".gsfx": convert_gsfx_upload_to_json,
    ".arp": convert_arp_upload_to_json,
    ".rtf": convert_rtf_upload_to_json,
    ".xlsx": convert_xlsx_upload_to_json,
}


async def load_raw_json_data(json_file: UploadFile) -> str:
    if json_file is None:
        raise HTTPException(status_code=400, detail="JSON file is required")

    filename = json_file.filename or "uploaded.json"
    suffix = Path(filename).suffix.lower()

    handler = HANDLER_MAP.get(suffix)

    if handler is None:
        raw_bytes = await json_file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Загруженный файл пустой")
        
        # Проверяем, не является ли файл изображением
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.webp']
        if suffix in image_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Файл '{filename}' является изображением. Используйте эндпоинт /vision-query для обработки изображений."
            )
        
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"Файл '{filename}' не является текстовым файлом в кодировке UTF-8. Для изображений используйте эндпоинт /vision-query."
            )

    converted_payload = await handler(json_file)

    return json.dumps(converted_payload, indent=2, ensure_ascii=False)

