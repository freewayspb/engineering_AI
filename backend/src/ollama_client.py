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
        payload = {"model": model, "prompt": prompt, "stream": False, "options": options}
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def chat(self, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages, "stream": False, "options": options}
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


