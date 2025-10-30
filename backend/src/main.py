import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .ollama_client import OllamaClient
from .schemas import GenerateRequest, ChatRequest


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

ollama = OllamaClient(base_url=OLLAMA_BASE_URL)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def list_models():
    try:
        data = await ollama.list_models()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate(req: GenerateRequest):
    try:
        data = await ollama.generate(model=req.model, prompt=req.prompt, options=req.options or {})
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        data = await ollama.chat(model=req.model, messages=req.messages, options=req.options or {})
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


