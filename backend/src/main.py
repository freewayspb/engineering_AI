"""FastAPI backend для BA_AI_GOST с локальной Ollama."""
from __future__ import annotations

from typing import List
import os
import uvicorn
from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .ollama_client import OllamaClient
from .schemas import GenerateRequest, ChatRequest


from .services import process_json_query, process_vision_query

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

app = FastAPI(title="BA_AI_GOST Backend", version="1.0.0")

# CORS для локального клиента
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ollama = OllamaClient(base_url=OLLAMA_BASE_URL)


@app.post("/vision-query")
async def vision_query(
    files: List[UploadFile] = File(..., description="One or more image files"),
    question: str = Form(..., description="Question to ask the vision model"),
):
    return await process_vision_query(files, question)


@app.post("/json-query")
async def json_query(
    json_file: str = File(..., description="JSON file to provide as context"),
    question: str = Form(..., description="Question to ask the DeepSeek model"),
):
    return await process_json_query(json_file, question)


@app.get("/")
async def root():
    """Root endpoint with available routes."""
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    return {"message": "BA_AI_GOST Backend", "routes": routes}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/ollama")
async def health_ollama():
    """Check Ollama connectivity."""
    try:
        data = await ollama.list_models()
        return {"status": "ok", "ollama_url": OLLAMA_BASE_URL, "models_available": len(data.get("models", []))}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {str(e)}")


@app.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        data = await ollama.list_models()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Generate text using an Ollama model."""
    try:
        data = await ollama.generate(model=req.model, prompt=req.prompt, options=req.options or {})
        return data
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.post("/chat")
async def chat(req: ChatRequest):
    """Chat with an Ollama model using a message history."""
    try:
        data = await ollama.chat(model=req.model, messages=req.messages, options=req.options or {})
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)


