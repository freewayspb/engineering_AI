from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    model: str = Field(..., description="Имя модели Ollama")
    prompt: str = Field(..., description="Промпт для генерации")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Параметры модели")


class ChatMessage(BaseModel):
    role: str = Field(..., description="system|user|assistant")
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    options: Optional[Dict[str, Any]] = None


