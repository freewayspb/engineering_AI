from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from .ollama_service import call_ollama

DEFAULT_ROUTER_INSTRUCTION = (
    "Вам предоставлены данные из файла. Используйте их, чтобы ответить на вопрос пользователя ясно и кратко."
)


async def run_console_json_ollama(
    question: str,
    file_path: str,
    response_language: str = "ru",
    *,
    instruction: str | None = None,
    original_filename: str | None = None,
) -> dict:
    """Run the deepseek-r1 model via the Ollama HTTP API using JSON/file context."""

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        file_contents = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UnicodeDecodeError(exc.encoding, exc.object, exc.start, exc.end, "Unable to decode file as UTF-8")

    # Определяем инструкцию по языку ответа (ВАЖНО: в начале промпта)
    if response_language == "ru":
        language_instruction = "ВАЖНО: Отвечайте ТОЛЬКО на русском языке. Все ваши ответы должны быть на русском языке."
    elif response_language == "en":
        language_instruction = "IMPORTANT: Respond ONLY in English. All your responses must be in English."
    elif response_language == "auto":
        language_instruction = "Respond in the same language as the question or context."
    else:
        language_instruction = "ВАЖНО: Отвечайте ТОЛЬКО на русском языке. Все ваши ответы должны быть на русском языке."  # По умолчанию русский

    instruction_block = (instruction or DEFAULT_ROUTER_INSTRUCTION).strip()
    filename_for_prompt = original_filename or path.name

    prompt = (
        f"{language_instruction}\n\n"
        f"{instruction_block}\n\n"
        f"Вопрос:\n{question}\n\n"
        f"файл ({filename_for_prompt}):\n{file_contents}"
    )

    payload = {
        "model": "deepseek-r1",
        "prompt": prompt,
        "stream": False,
    }

    try:
        ollama_response = await call_ollama("/api/generate", payload)
    except HTTPException as exc:
        # Пробрасываем HTTPException как есть, чтобы сохранить статус код
        raise
    except Exception as exc:
        error_msg = str(exc)
        if "Failed to reach Ollama" in error_msg:
            raise HTTPException(
                status_code=502,
                detail="Не удалось подключиться к Ollama. Проверьте, что Ollama запущен и доступен по адресу http://ollama:11434"
            ) from exc
        elif "model" in error_msg.lower() and "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Модель 'deepseek-r1' не найдена в Ollama. Установите модель через docker-compose run --rm ollama-init"
            ) from exc
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обращении к Ollama: {error_msg}"
            ) from exc

    response_text = ollama_response.get("response", "").strip()

    return {
        "model": "deepseek-r1",
        "prompt": prompt,
        "response": response_text,
    }


