from __future__ import annotations

from pathlib import Path
from typing import Optional
import base64

from fastapi import HTTPException, UploadFile

from .ollama_service import call_ollama


async def process_vision_query(image_file: UploadFile, question: str) -> dict:
    if image_file is None:
        raise HTTPException(status_code=400, detail="Требуется загрузить изображение")

    data = await image_file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail=f"Файл '{image_file.filename or 'изображение'}' пустой",
        )

    try:
        encoder_data = base64.b64encode(data).decode("utf-8")

        payload = {
            "model": "llama3.2-vision",
            "stream": False,
            "prompt": "Опиши что видно на изображении?",
            "images": [encoder_data],
        }

        ollama_response = await call_ollama("/api/generate", payload)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при запросе к Ollama: {exc}",
        ) from exc

    return {
        "model": "llama3.2-vision",
        "response": ollama_response.get("response"),
    }

