from __future__ import annotations

import base64

from fastapi import HTTPException, UploadFile


async def convert_upload_image_to_base64(image_file: UploadFile) -> str:
    """
    Читает загруженный файл изображения, выполняет базовую валидацию
    и возвращает его содержимое в формате base64.
    """
    if image_file is None:
        raise HTTPException(
            status_code=400,
            detail="Изображение не предоставлено. Загрузите файл изображения для обработки.",
        )

    try:
        data = await image_file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при чтении файла изображения: {str(exc)}",
        ) from exc

    if not data:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Файл '{image_file.filename or 'изображение'}' пустой. "
                "Загрузите непустой файл изображения."
            ),
        )

    try:
        return base64.b64encode(data).decode("utf-8")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при кодировании изображения: {str(exc)}",
        ) from exc

