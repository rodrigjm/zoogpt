"""
LLM service with local-first (Ollama), cloud fallback (OpenAI).
All methods are async for non-blocking I/O.
"""
import logging
import httpx
from typing import Optional
from openai import AsyncOpenAI
from ..config import settings, dynamic_config
from ..utils.timing import timed_print

logger = logging.getLogger(__name__)

_ollama_available: Optional[bool] = None
_async_httpx_client: Optional[httpx.AsyncClient] = None


def _get_async_httpx_client() -> httpx.AsyncClient:
    """Lazy-init a shared async httpx client for Ollama."""
    global _async_httpx_client
    if _async_httpx_client is None:
        _async_httpx_client = httpx.AsyncClient(timeout=60.0)
    return _async_httpx_client


async def check_ollama_health() -> bool:
    """Check if Ollama is available."""
    global _ollama_available
    try:
        client = _get_async_httpx_client()
        response = await client.get(f"{settings.ollama_url}/api/tags", timeout=5.0)
        _ollama_available = response.status_code == 200
        return bool(_ollama_available)
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        _ollama_available = False
        return False


async def is_ollama_available() -> bool:
    """Return cached Ollama availability."""
    global _ollama_available
    if _ollama_available is None:
        await check_ollama_health()
    return _ollama_available or False


class LLMService:
    """LLM service with local-first, cloud fallback."""

    def __init__(self, openai_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.ollama_url = settings.ollama_url

    async def generate_ollama(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate using local Ollama."""
        model = dynamic_config.pipeline_llm_model or settings.ollama_model
        timed_print(f"  [LLM] Ollama generating ({model})...")

        client = _get_async_httpx_client()
        response = await client.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
        )
        response.raise_for_status()
        result = response.json()["message"]["content"]
        timed_print(f"  [LLM] Ollama done: {len(result)} chars")
        return result

    async def generate_openai(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate using OpenAI API."""
        timed_print(f"  [LLM] OpenAI generating ({model})...")

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content
        timed_print(f"  [LLM] OpenAI done: {len(result)} chars")
        return result

    async def generate(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate with local-first, cloud fallback."""
        provider = dynamic_config.pipeline_llm_provider or settings.llm_provider

        # Try Ollama first if configured
        if provider == "ollama" and await is_ollama_available():
            try:
                return await self.generate_ollama(messages, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama failed, falling back to OpenAI: {e}")

        # Use OpenAI (either as primary or fallback)
        openai_model = dynamic_config.pipeline_llm_model or model
        return await self.generate_openai(messages, openai_model, temperature, max_tokens)
