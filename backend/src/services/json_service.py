from __future__ import annotations

import json

import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .console_json_ollama import run_console_json_ollama
from .json_file_router import load_raw_json_data

async def process_json_query(json_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    if json_file is None:
        raise HTTPException(status_code=400, detail="Файл не предоставлен. Загрузите JSON файл для обработки.")

    try:
        serialized_json = await load_raw_json_data(json_file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при чтении файла: {str(exc)}"
        ) from exc

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
        temp_file.write(serialized_json)
        temp_path = Path(temp_file.name)

    try:
        result = await run_console_json_ollama(
            question,
            str(temp_path),
            response_language,
        )
    except HTTPException:
        # Пробрасываем HTTPException как есть
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Временный файл не найден: {str(exc)}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Файл содержит некорректные символы (не UTF-8): {str(exc)}"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Неожиданная ошибка при обработке файла: {str(exc)}"
        ) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if not result or not result.get("response"):
        raise HTTPException(
            status_code=502,
            detail="Модель вернула пустой ответ. Возможно, модель не установлена или произошла ошибка при генерации."
        )

    return {
        "model": result.get("model", "deepseek-r1"),
        "response": result.get("response"),
        "prompt": result.get("prompt"),
    }

