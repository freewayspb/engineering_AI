from __future__ import annotations

from fastapi import HTTPException, UploadFile

from .image_file_router import route_image_payload
from .ollama_service import call_ollama


async def process_vision_query(image_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    routed_payload = await route_image_payload(image_file)
    encoded_images = routed_payload.images
    document_context = routed_payload.context

    cleaned_question = question and question.strip() or "";
    cleaned_question_prefix = ""
    prompt_prefix = ""

        # Заменяем старые формулировки на более понятные
    if "самари" in cleaned_question.lower():
        if response_language == "ru":
            cleaned_question_prefix = "Опиши подробно, что изображено на этом изображении. "
        else:
            cleaned_question_prefix = "Describe in detail what is shown in this image. "


    if not cleaned_question:
        if response_language == "ru":
            cleaned_question = "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."
        elif response_language == "en":
            cleaned_question = "Describe in detail what is shown in this image. Describe all interface elements, text, colors and structure."
        else:
            cleaned_question = "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."

    if response_language == "ru":
        prompt_prefix = "Опиши это изображение на русском языке. "
    elif response_language == "en":
        prompt_prefix = f"Describe this image in English. "
    elif response_language == "auto":
        prompt_prefix = ""
    else:
        # По умолчанию русский
        prompt_prefix = "Опиши это изображение на русском языке."

    prompt = f"{prompt_prefix}{cleaned_question_prefix}{cleaned_question}"

    if document_context:
        prompt = f"{document_context}\n{prompt}"

    # Используем более легкую модель llava (4.7 GB), так как llama3.2-vision требует слишком много памяти (10.9 GB)
    payload = {
        "model": "llava",
        "stream": False,
        "prompt": prompt,
        "images": encoded_images,
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

