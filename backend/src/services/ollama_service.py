from __future__ import annotations

import json
import os

import httpx
from fastapi import HTTPException

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def call_ollama(endpoint: str, payload: dict) -> dict:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    async with httpx.AsyncClient(timeout=httpx.Timeout(1800.0)) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Не удалось подключиться к Ollama по адресу {OLLAMA_BASE_URL}. Проверьте, что Ollama запущен и доступен."
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="Превышено время ожидания ответа от Ollama (30 минут). Модель обрабатывает запрос слишком долго. Попробуйте уменьшить размер файла или упростить вопрос."
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Ошибка при обращении к Ollama: {str(exc)}"
            ) from exc

    if response.status_code >= 400:
        error_detail = "Неизвестная ошибка"
        try:
            error_json = response.json()
            if "error" in error_json:
                error_detail = error_json["error"]
        except (ValueError, json.JSONDecodeError):
            error_detail = response.text[:200] if response.text else "Пустой ответ от Ollama"
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Модель не найдена в Ollama: {error_detail}"
            )
        elif response.status_code == 500:
            # Проверяем, не связана ли ошибка с нехваткой памяти
            if "memory" in error_detail.lower() or "system memory" in error_detail.lower():
                raise HTTPException(
                    status_code=507,
                    detail=f"Недостаточно памяти для запуска модели. {error_detail}. Попробуйте использовать более легкую модель или освободите память."
                )
            raise HTTPException(
                status_code=502,
                detail=f"Ошибка Ollama при генерации ответа: {error_detail}"
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка Ollama (код {response.status_code}): {error_detail}"
            )

    try:
        response_json = response.json()

        return response_json
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Invalid JSON from Ollama") from exc


def _extract_assistant_message(ollama_response: dict) -> str:
    message = ollama_response.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    content = ollama_response.get("response")
    if isinstance(content, str):
        return content

    raise HTTPException(status_code=502, detail="Unexpected response format from Ollama")

