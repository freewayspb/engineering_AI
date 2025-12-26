#!/usr/bin/env python3
"""
Асинхронный конвертер PDF-файлов в изображения, закодированные в Base64.
"""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, UploadFile

try:
    import pypdfium2 as pdfium
except ImportError as exc:
    raise ImportError(
        "pypdfium2 не установлен. Установите его командой: pip install pypdfium2>=4.27.0"
    ) from exc

from src.services.utils.compat_asyncio import to_thread


def _render_pdf_pages(pdf_bytes: bytes, scale: float = 2.0, max_pages: int = 50) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Рендерит страницы PDF в изображения.
    
    Args:
        pdf_bytes: Байты PDF файла
        scale: Масштаб рендеринга (2.0 = 200% для лучшего качества)
        max_pages: Максимальное количество страниц для обработки (защита от больших файлов)
    """
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
    except Exception as exc:
        raise ValueError(f"Не удалось открыть PDF документ: {str(exc)}") from exc

    images: List[Dict[str, Any]] = []
    try:
        total_pages = len(pdf)
        if total_pages > max_pages:
            raise ValueError(f"PDF содержит слишком много страниц ({total_pages}). Максимум: {max_pages}")
        
        for index, page in enumerate(pdf):
            if index >= max_pages:
                break
                
            pil_image = None
            try:
                bitmap = page.render(scale=scale)
                try:
                    pil_image = bitmap.to_pil()
                except Exception as exc:
                    raise ValueError(f"Ошибка при рендеринге страницы {index + 1}: {str(exc)}") from exc
                finally:
                    bitmap.close()

                buffer = io.BytesIO()
                try:
                    pil_image.save(buffer, format="PNG")
                except Exception as exc:
                    raise ValueError(f"Ошибка при сохранении страницы {index + 1} в PNG: {str(exc)}") from exc

                encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

                images.append(
                    {
                        "page_index": index,
                        "format": "png",
                        "base64": encoded,
                    }
                )
            except Exception as exc:
                # Логируем ошибку для конкретной страницы, но продолжаем обработку остальных
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Ошибка при обработке страницы {index + 1}: {str(exc)}")
                # Пропускаем проблемную страницу и продолжаем
                continue
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

    # Ограничение размера файла (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    payload = await pdf_file.read()
    await pdf_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный PDF-файл пуст.")
    
    if len(payload) > MAX_FILE_SIZE:
        size_mb = len(payload) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"PDF-файл слишком большой ({size_mb:.1f} MB). Максимальный размер: 50 MB."
        )

    try:
        page_count, images = await to_thread(_render_pdf_pages, payload)
    except ValueError as exc:
        error_msg = str(exc) or "Ошибка валидации PDF"
        raise HTTPException(
            status_code=422,
            detail=f"Ошибка обработки PDF: {error_msg}"
        ) from exc
    except pdfium.PdfiumError as exc:
        error_msg = str(exc) or "Неизвестная ошибка pypdfium2"
        raise HTTPException(
            status_code=422, 
            detail=f"Не удалось обработать PDF-файл: {error_msg}"
        ) from exc
    except MemoryError as exc:
        raise HTTPException(
            status_code=507,
            detail="Недостаточно памяти для обработки PDF. Файл слишком большой или содержит слишком много страниц."
        ) from exc
    except OSError as exc:
        error_msg = str(exc) or "Ошибка файловой системы"
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при чтении PDF-файла: {error_msg}"
        ) from exc
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        error_type = type(exc).__name__
        error_msg = str(exc) or "Неизвестная ошибка"
        # Логируем детали для отладки, но не показываем пользователю технические детали
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PDF conversion error: {error_type}: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка конвертера PDF ({error_type}). Проверьте формат файла и попробуйте снова."
        ) from exc

    if page_count == 0:
        raise HTTPException(status_code=422, detail="PDF-файл не содержит страниц.")

    return {
        "source_filename": filename,
        "page_count": page_count,
        "images": images,
    }


__all__ = ["convert_pdf_upload_to_base64_images"]


