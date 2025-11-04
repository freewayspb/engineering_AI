from __future__ import annotations

import base64
from typing import List

from fastapi import HTTPException, UploadFile

from .ollama_service import call_ollama


async def process_vision_query(files: List[UploadFile], question: str) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="At least one image file is required")

    encoded_images: List[str] = []
    for upload in files:
        data = await upload.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"File '{upload.filename}' is empty")
        encoded_images.append(base64.b64encode(data).decode("utf-8"))

    content_blocks = [{"type": "text", "text": question}]
    content_blocks.extend({"type": "image", "image": encoded} for encoded in encoded_images)

    payload = {
        "model": "llama3.2-vision",
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": content_blocks,
            }
        ],
    }

    ollama_response = await call_ollama("/api/chat", payload)

    return {
        "model": "llama3.2-vision",
        "response": ollama_response,
    }

