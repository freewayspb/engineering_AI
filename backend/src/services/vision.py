from __future__ import annotations

from fastapi import HTTPException, UploadFile

from .image_file_router import route_image_payload
from .ollama_service import call_ollama


def _sanitize_question(question: str | None) -> str:
    return question.strip() if question else ""


def _build_cleaned_question_prefix(cleaned_question: str, response_language: str) -> str:
    if "самари" not in cleaned_question.lower():
        return ""

    if response_language == "ru":
        return "Опиши подробно, что изображено на этом изображении. "

    return "Describe in detail what is shown in this image. "


def _build_cleaned_question(cleaned_question: str, response_language: str) -> str:
    if cleaned_question:
        return cleaned_question

    if response_language == "ru":
        return "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."

    if response_language == "en":
        return "Describe in detail what is shown in this image. Describe all interface elements, text, colors and structure."

    return "Опиши подробно, что изображено на этом изображении. Опиши все элементы интерфейса, текст, цвета и структуру."


def _build_prompt_prefix(response_language: str) -> str:
    if response_language == "ru":
        return "Опиши это изображение на русском языке. "

    if response_language == "en":
        return "Describe this image in English. "

    if response_language == "auto":
        return ""

    # По умолчанию русский
    return "Опиши это изображение на русском языке."


async def process_vision_query(image_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    routed_payload = await route_image_payload(image_file)
    encoded_images = routed_payload.images
    document_context = routed_payload.context

    sanitized_question = _sanitize_question(question)
    cleaned_question_prefix = _build_cleaned_question_prefix(sanitized_question, response_language)
    cleaned_question = _build_cleaned_question(sanitized_question, response_language)
    prompt_prefix = _build_prompt_prefix(response_language)

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

