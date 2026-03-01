"""OpenAI-compatible LLM client."""
from __future__ import annotations
import httpx
import logging

logger = logging.getLogger("openwendy.providers.llm")


class LLMProvider:
    def __init__(self, config):
        self.config = config
        p = config.providers
        if p.active == "cloud":
            self.api_base = self._cloud_base(p.cloud.provider)
            self.api_key = p.cloud.apiKey
            self.default_model = p.cloud.model
        else:
            self.api_base = p.local.apiBase.rstrip("/")
            self.api_key = p.local.apiKey
            self.default_model = p.local.model
        self.client = httpx.AsyncClient(timeout=120.0)

    def _cloud_base(self, provider: str) -> str:
        bases = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "deepseek": "https://api.deepseek.com/v1",
        }
        return bases.get(provider, "https://api.openai.com/v1")

    async def chat(self, messages: list[dict], model: str | None = None,
                   temperature: float = 0.7, max_tokens: int = 2048) -> str:
        model = model if model and model != "auto" else self.default_model
        url = f"{self.api_base}/chat/completions"
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = await self.client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
