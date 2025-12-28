from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .console_json_ollama import run_console_json_ollama
from .json_file_router import load_raw_json_data

logger = logging.getLogger(__name__)

async def process_json_query(json_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    if json_file is None:
        raise HTTPException(status_code=400, detail="Файл не предоставлен. Загрузите JSON файл для обработки.")

    filename = json_file.filename or "unknown"
    logger.info("Processing JSON query for file: %s, question: %s", filename, question[:100] if question else "")

    try:
        routed_payload = await load_raw_json_data(json_file)
        logger.debug("File loaded successfully: %s, content length: %d", filename, len(routed_payload.content))
    except HTTPException:
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        error_msg = str(exc)
        logger.error("Error loading file %s: %s: %s", filename, error_type, error_msg, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при чтении файла '{filename}' ({error_type}): {error_msg}"
        ) from exc

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
        temp_file.write(routed_payload.content)
        temp_path = Path(temp_file.name)

    try:
        logger.debug("Calling Ollama with temp file: %s", temp_path)
        result = await run_console_json_ollama(
            question,
            str(temp_path),
            response_language,
            instruction=routed_payload.instruction,
            original_filename=routed_payload.filename,
        )
        logger.debug("Ollama response received for file: %s", filename)
    except HTTPException:
        # Пробрасываем HTTPException как есть
        raise
    except FileNotFoundError as exc:
        logger.error("Temp file not found: %s", temp_path, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Временный файл не найден: {str(exc)}"
        ) from exc
    except UnicodeDecodeError as exc:
        logger.error("Unicode decode error for file: %s", filename, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Файл '{filename}' содержит некорректные символы (не UTF-8): {str(exc)}"
        ) from exc
    except ConnectionError as exc:
        logger.error("Connection error to Ollama for file: %s", filename, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Не удалось подключиться к Ollama: {str(exc)}"
        ) from exc
    except TimeoutError as exc:
        logger.error("Timeout error for file: %s", filename, exc_info=True)
        raise HTTPException(
            status_code=504,
            detail=f"Превышено время ожидания ответа от модели: {str(exc)}"
        ) from exc
    except Exception as exc:
        error_type = type(exc).__name__
        error_msg = str(exc)
        logger.error("Unexpected error processing file %s: %s: %s", filename, error_type, error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Неожиданная ошибка при обработке файла '{filename}' ({error_type}): {error_msg}"
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

