from __future__ import annotations

import json
import os

import httpx
from fastapi import HTTPException


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def call_ollama(endpoint: str, payload: dict) -> dict:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to reach Ollama: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "error": "Ollama returned an error",
                "payload": response.text,
            },
        )

    try:
        response_json = await response.json()
        _extract_assistant_message(response_json)
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

