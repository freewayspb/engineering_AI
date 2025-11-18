from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


async def run_console_vision_ollama(question: str, upload_file: Any) -> dict:
    """Запуск vision-модели через Ollama CLI c одним изображением.

    Параметр `upload_file` должен предоставлять атрибуты `filename` и `file`
    (как у FastAPI UploadFile).
    """

    suffix = Path(upload_file.filename or "").suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        temp_path = Path(tmp_file.name).resolve()
        upload_file.file.seek(0)
        shutil.copyfileobj(upload_file.file, tmp_file)

    try:
        file_size = temp_path.stat().st_size

        if file_size == 0:
            raise ValueError(f"File is empty: {temp_path}")

        prompt = (
            "Тебе передано изображение в бинарном формате. "
            "Используй его содержимое, чтобы ответить на вопрос пользователя "
            "ясно и по сути.\n\n"
            f"Путь к файлу изображения: {temp_path}\n\n"
            f"Вопрос:\n{question}\n\n"
        )

        try:
            result = subprocess.run(
                ["ollama", "run", "llama3.2-vision"],
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("The 'ollama' executable is not available in PATH.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else ""

            raise RuntimeError(
                "Ollama CLI call failed with exit code "
                f"{exc.returncode}. {stderr}"
            ) from exc

        response = result.stdout.strip()

        return {
            "model": "llama3.2-vision",
            "prompt": prompt,
            "response": response,
        }
    finally:
        temp_path.unlink(missing_ok=True)


