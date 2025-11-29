#!/usr/bin/env python3
"""
Асинхронный конвертер PDF-файлов в изображения, закодированные в Base64.
"""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, UploadFile
import pypdfium2 as pdfium

from ..utils.compat_asyncio import to_thread


def _render_pdf_pages(pdf_bytes: bytes, scale: float = 2.0) -> Tuple[int, List[Dict[str, Any]]]:
    pdf = pdfium.PdfDocument(pdf_bytes)

    images: List[Dict[str, Any]] = []
    try:
        for index, page in enumerate(pdf):
            pil_image = None
            try:
                bitmap = page.render(scale=scale)
                try:
                    pil_image = bitmap.to_pil()
                finally:
                    bitmap.close()

                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")

                encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

                images.append(
                    {
                        "page_index": index,
                        "format": "png",
                        "base64": encoded,
                    }
                )
            finally:
                if pil_image is not None:
                    pil_image.close()
                page.close()
    finally:
        pdf.close()

    return len(images), images


async def convert_pdf_upload_to_base64_images(pdf_file: UploadFile) -> Dict[str, Any]:
    """
    Конвертирует PDF-файл в список изображений (PNG), представленных в Base64.
    """
    if pdf_file is None:
        raise HTTPException(status_code=400, detail="Файл PDF обязателен для загрузки.")

    filename = pdf_file.filename or "uploaded.pdf"

    payload = await pdf_file.read()
    await pdf_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный PDF-файл пуст.")

    try:
        page_count, images = await to_thread(_render_pdf_pages, payload)
    except pdfium.PdfiumError as exc:
        raise HTTPException(status_code=422, detail="Не удалось обработать PDF-файл.") from exc
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        raise HTTPException(status_code=500, detail="Внутренняя ошибка конвертера PDF.") from exc

    if page_count == 0:
        raise HTTPException(status_code=422, detail="PDF-файл не содержит страниц.")

    return {
        "source_filename": filename,
        "page_count": page_count,
        "images": images,
    }


__all__ = ["convert_pdf_upload_to_base64_images"]


