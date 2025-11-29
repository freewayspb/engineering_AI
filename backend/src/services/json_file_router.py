from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, UploadFile

from .file_handlers.arp_upload_service import convert_arp_upload_to_json
from .file_handlers.dxf_console_service import convert_dxf_upload_to_json
from .file_handlers.gsfx_upload_service import convert_gsfx_upload_to_json
from .file_handlers.pdf_upload_service import convert_pdf_upload_to_base64_images
from .file_handlers.rtf_upload_service import convert_rtf_upload_to_json
from .file_handlers.xlsx_upload_service import convert_xlsx_upload_to_json

Handler = Callable[[UploadFile], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class HandlerConfig:
    handler: Handler
    instruction: str


@dataclass(frozen=True)
class RoutedJsonPayload:
    content: str
    instruction: str
    filename: str


DEFAULT_ROUTER_INSTRUCTION = (
    "Вам предоставлены данные из файла. Используйте их, чтобы ответить на вопрос пользователя ясно и кратко."
)

HANDLER_MAP: Dict[str, HandlerConfig] = {
    ".arp": HandlerConfig(
        handler=convert_arp_upload_to_json,
        instruction=(
            "Входные данные получены из файла ARP (строительная смета). "
            "Опирайтесь на разделы, позиции и коэффициенты, чтобы отвечать на вопросы о смете."
        ),
    ),
    ".dxf": HandlerConfig(
        handler=convert_dxf_upload_to_json,
        instruction=(
            "Входные данные — JSON, сформированный из DXF/DWG. "
            "Используйте сведения о слоях, блоках и геометрии сущностей для анализа чертежа."
        ),
    ),
    ".gsfx": HandlerConfig(
        handler=convert_gsfx_upload_to_json,
        instruction=(
            "Входные данные — архив GSFX, преобразованный в набор XML-файлов в JSON-представлении. "
            "Ссылайтесь на соответствующие элементы XML при ответах."
        ),
    ),
    ".pdf": HandlerConfig(
        handler=convert_pdf_upload_to_base64_images,
        instruction=(
            "Входные данные — изображения страниц PDF, закодированные в Base64. "
            "Извлеки текст/структуру страниц и используйте их при ответе."
        ),
    ),
    ".rtf": HandlerConfig(
        handler=convert_rtf_upload_to_json,
        instruction=(
            "Входные данные — текст документа RTF в JSON-структуре. "
            "Учитывайте форматирование и текстовые блоки при формировании ответа."
        ),
    ),
    ".xlsx": HandlerConfig(
        handler=convert_xlsx_upload_to_json,
        instruction=(
            "Входные данные — таблицы XLSX, преобразованные в записи по листам. "
            "Используйте значения ячеек и структуру столбцов для анализа."
        ),
    ),
}


async def load_raw_json_data(json_file: UploadFile) -> RoutedJsonPayload:
    if json_file is None:
        raise HTTPException(status_code=400, detail="JSON file is required")

    filename = json_file.filename or "uploaded.json"
    suffix = Path(filename).suffix.lower()

    handler_config = HANDLER_MAP.get(suffix)

    if handler_config is None:
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
            serialized_content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            serialized_content = raw_bytes.decode("latin-1")
            # raise HTTPException(
            #     status_code=400,
            #     detail=f"Файл '{filename}' не является текстовым файлом в кодировке UTF-8. Для изображений используйте эндпоинт /vision-query."
            # )
        return RoutedJsonPayload(
            content=serialized_content,
            instruction=DEFAULT_ROUTER_INSTRUCTION,
            filename=filename,
        )

    converted_payload = await handler_config.handler(json_file)
    serialized_json = json.dumps(converted_payload, indent=2, ensure_ascii=False)

    return RoutedJsonPayload(
        content=serialized_json,
        instruction=handler_config.instruction,
        filename=filename,
    )

