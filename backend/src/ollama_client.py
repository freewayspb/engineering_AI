from typing import Any, Dict, List
import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60)

    async def list_models(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/tags"
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def generate(self, model: str, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False, "options": options or {}}
        try:
            resp = await self.client.post(url, json=payload, timeout=60.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ConnectionError(f"Ollama endpoint not found: {url}. Check if Ollama is running and model '{model}' exists.")
            raise
        except httpx.ConnectError as e:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}. Check if Ollama is running.")

    async def chat(self, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages, "stream": False, "options": options}
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


