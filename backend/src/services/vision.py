from __future__ import annotations

from pathlib import Path
from fastapi import HTTPException, UploadFile

from .ollama_service import call_ollama
from .file_handlers.image_upload_service import convert_upload_image_to_base64
from .file_handlers.pdf_upload_service import convert_pdf_upload_to_base64_images


async def process_vision_query(image_file: UploadFile, question: str, response_language: str = "ru") -> dict:
    filename = image_file.filename or ""
    content_type = (image_file.content_type or "").lower()
    suffix = Path(filename).suffix.lower()

    is_pdf = suffix == ".pdf" or content_type == "application/pdf"
    document_context = ""

    if is_pdf:
        pdf_payload = await convert_pdf_upload_to_base64_images(image_file)
        encoded_images = [
            page.get("base64")
            for page in pdf_payload.get("images", [])
            if page.get("base64")
        ]
        if not encoded_images:
            raise HTTPException(
                status_code=422,
                detail="PDF-файл не содержит обрабатываемых страниц."
            )
        document_context = (
            f"Источник: PDF-файл '{pdf_payload.get('source_filename', filename or 'document.pdf')}', "
            f"страниц: {pdf_payload.get('page_count', len(encoded_images))}."
        )
    else:
        encoded_image = await convert_upload_image_to_base64(image_file)
        encoded_images = [encoded_image]

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

