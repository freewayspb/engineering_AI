"""FastAPI backend для BA_AI_GOST с локальной Ollama."""
from __future__ import annotations

import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException, File, Form, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .ollama_client import OllamaClient
from .schemas import GenerateRequest, ChatRequest


from .services import process_json_query, process_vision_query

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

app = FastAPI(title="BA_AI_GOST Backend", version="1.0.0")

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов."""
    logger.info("Request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        logger.info("Response: %s %s - %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as exc:
        logger.error("Exception in request %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        raise

# Глобальный обработчик исключений (только для необработанных исключений)
# HTTPException обрабатываются FastAPI автоматически, поэтому не регистрируем обработчик для них
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Обработчик всех необработанных исключений (кроме HTTPException)."""
    # HTTPException обрабатываются FastAPI автоматически, пропускаем их
    if isinstance(exc, HTTPException):
        # Пробрасываем HTTPException дальше для обработки FastAPI
        raise exc
    
    logger.error("Unhandled exception: %s", exc, exc_info=True, extra={
        "path": request.url.path,
        "method": request.method,
    })
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Внутренняя ошибка сервера: {str(exc)}",
            "type": type(exc).__name__,
        }
    )

# CORS для локального клиента
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ollama = OllamaClient(base_url=OLLAMA_BASE_URL)


@app.post("/vision-query")
async def vision_query(
    image_file: UploadFile = File(..., description="One or more image files"),
    question: str = Form(..., description="Question to ask the vision model"),
    response_language: str = Form("ru", description="Language for the response (ru, en, auto)"),
):
    return await process_vision_query(image_file, question, response_language)


@app.post("/json-query")
async def json_query(
    json_file: UploadFile = File(..., description="JSON file to provide as context"),
    question: str = Form(..., description="Question to ask the deepseek-r1 model"),
    response_language: str = Form("ru", description="Language for the response (ru, en, auto)"),
):
    return await process_json_query(json_file, question, response_language)


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


