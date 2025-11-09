#!/usr/bin/env python3
"""
Асинхронный обработчик GSFX-файлов для FastAPI.
Принимает UploadFile, извлекает XML и возвращает их содержимое в JSON-представлении.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, UploadFile

from ..gsfx_to_json import (
    extract_with_7z,
    extract_with_zip,
    find_xml_files,
    try_decode_xml_bytes,
)
from ..utils.compat_asyncio import to_thread

try:  # pragma: no cover - доступность зависит от окружения выполнения
    import xmltodict  # type: ignore
except ImportError:  # pragma: no cover - перехватываем позже
    xmltodict = None  # type: ignore[assignment]


def _process_gsfx_file(gsfx_path: Path, original_name: str) -> Dict[str, Any]:
    if xmltodict is None:
        raise ImportError("Модуль xmltodict недоступен. Установите зависимость `xmltodict`.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        extracted_dir = Path(tmp_dir) / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        extracted = extract_with_zip(gsfx_path, extracted_dir)
        if not extracted:
            extracted = extract_with_7z(gsfx_path, extracted_dir)

        if not extracted:
            raise ValueError(
                "Не удалось распаковать GSFX. Убедитесь, что файл является ZIP-совместимым "
                "либо установлена утилита 7-Zip (`7z` или `7za`)."
            )

        xml_files = find_xml_files(extracted_dir)
        if not xml_files:
            raise ValueError("В архиве GSFX не обнаружены XML-файлы.")

        files: Dict[str, Any] = {}
        for xml_path in xml_files:
            data_bytes = xml_path.read_bytes()
            xml_text = try_decode_xml_bytes(data_bytes)
            json_payload = xmltodict.parse(xml_text)
            rel_path = xml_path.relative_to(extracted_dir).as_posix()
            files[rel_path] = json_payload

        return {
            "source_filename": original_name,
            "xml_file_count": len(xml_files),
            "files": files,
        }


async def convert_gsfx_upload_to_json(gsfx_file: UploadFile) -> Dict[str, Any]:
    """
    Конвертирует GSFX-файл, полученный через UploadFile, в словарь с JSON-данными.
    """
    if gsfx_file is None:
        raise HTTPException(status_code=400, detail="Файл GSFX обязателен для загрузки.")

    filename = gsfx_file.filename or "uploaded.gsfx"
    suffix = Path(filename).suffix or ".gsfx"

    payload = await gsfx_file.read()
    await gsfx_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный GSFX-файл пуст.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(payload)
        tmp_path = Path(tmp_file.name)

    try:
        result = await to_thread(_process_gsfx_file, tmp_path, filename)
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        raise HTTPException(status_code=500, detail="Неожиданная ошибка при обработке GSFX.") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return result


__all__ = ["convert_gsfx_upload_to_json"]

