from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from .ollama_service import call_ollama
from .file_handlers.image_upload_service import convert_upload_image_to_base64


async def process_vision_query(image_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    encoder_data = await convert_upload_image_to_base64(image_file)

    # Формируем промпт в зависимости от языка ответа
    # Используем вопрос пользователя, если он предоставлен, иначе используем стандартный промпт
    if question and question.strip():
        # Очищаем вопрос от старых формулировок
        cleaned_question = question.strip()
        # Заменяем старые формулировки на более понятные
        if "самари" in cleaned_question.lower() or "самари файла" in cleaned_question.lower():
            if response_language == "ru":
                cleaned_question = "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."
            else:
                cleaned_question = "Describe in detail what is shown in this image. Describe all interface elements, text, colors and structure."
        base_prompt = cleaned_question
    else:
        if response_language == "ru":
            base_prompt = "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."
        elif response_language == "en":
            base_prompt = "Describe in detail what is shown in this image. Describe all interface elements, text, colors and structure."
        else:
            base_prompt = "Describe in detail what is shown in this image. Describe all interface elements, text, colors and structure."
    
    # Формируем финальный промпт с учетом языка
    if response_language == "ru":
        prompt = f"Опиши это изображение на русском языке. {base_prompt}"
    elif response_language == "en":
        prompt = f"Describe this image in English. {base_prompt}"
    elif response_language == "auto":
        prompt = base_prompt
    else:
        # По умолчанию русский
        prompt = f"Опиши это изображение на русском языке. {base_prompt}"

    # Используем более легкую модель llava (4.7 GB), так как llama3.2-vision требует слишком много памяти (10.9 GB)
    payload = {
        "model": "llava",
        "stream": False,
        "prompt": prompt,
        "images": [encoder_data],
        "options": {
            "temperature": 0.5,  # Снижаем температуру для более детерминированных ответов
            "num_predict": 500,  # Увеличиваем максимальную длину ответа
        }
    }

    try:
        ollama_response = await call_ollama("/api/generate", payload)
    except HTTPException:
        # Пробрасываем HTTPException как есть
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при обращении к Ollama для обработки изображения: {str(exc)}"
        ) from exc

    response_text = ollama_response.get("response", "").strip()
    
    if not response_text:
        raise HTTPException(
            status_code=502,
            detail="Модель вернула пустой ответ. Возможно, модель llava не установлена или произошла ошибка при генерации."
        )

    return {
        "model": "llava",
        "response": response_text,
        "prompt": prompt,
    }

