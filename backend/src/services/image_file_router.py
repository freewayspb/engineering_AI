from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .file_handlers.image_upload_service import convert_upload_image_to_base64
from .file_handlers.pdf_upload_service import convert_pdf_upload_to_base64_images


@dataclass(frozen=True)
class RoutedImagePayload:
    images: list[str]
    context: str
    filename: str


async def route_image_payload(image_file: UploadFile) -> RoutedImagePayload:
    """
    Унифицированная маршрутизация файлов изображений и PDF.
    Возвращает список Base64-строк и описание источника для промпта.
    """
    if image_file is None:
        raise HTTPException(status_code=400, detail="Файл обязателен для обработки изображения.")

    filename = image_file.filename or ""
    content_type = (image_file.content_type or "").lower()
    suffix = Path(filename).suffix.lower()

    is_pdf = suffix == ".pdf" or content_type == "application/pdf"

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
        resolved_filename = pdf_payload.get("source_filename") or filename or "document.pdf"
    else:
        encoded_image = await convert_upload_image_to_base64(image_file)
        encoded_images = [encoded_image]
        document_context = ""
        resolved_filename = filename or "image"

    return RoutedImagePayload(
        images=encoded_images,
        context=document_context,
        filename=resolved_filename,
    )

