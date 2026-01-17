"""
LLM service with local-first (Ollama), cloud fallback (OpenAI).
"""
import logging
import httpx
from typing import Optional
from openai import OpenAI
from ..config import settings
from ..utils.timing import timed_print

logger = logging.getLogger(__name__)

_ollama_available: Optional[bool] = None


def check_ollama_health() -> bool:
    """Check if Ollama is available."""
    global _ollama_available
    try:
        response = httpx.get(f"{settings.ollama_url}/api/tags", timeout=5.0)
        _ollama_available = response.status_code == 200
        return bool(_ollama_available)
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        _ollama_available = False
        return False


def is_ollama_available() -> bool:
    """Return cached Ollama availability."""
    global _ollama_available
    if _ollama_available is None:
        check_ollama_health()
    return _ollama_available or False


class LLMService:
    """LLM service with local-first, cloud fallback."""

    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.ollama_url = settings.ollama_url
        self.ollama_model = settings.ollama_model

    def generate_ollama(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate using local Ollama."""
        timed_print(f"  [LLM] Ollama generating ({self.ollama_model})...")

        response = httpx.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()["message"]["content"]
        timed_print(f"  [LLM] Ollama done: {len(result)} chars")
        return result

    def generate_openai(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate using OpenAI API."""
        timed_print(f"  [LLM] OpenAI generating ({model})...")

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content
        timed_print(f"  [LLM] OpenAI done: {len(result)} chars")
        return result

    def generate(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate with local-first, cloud fallback."""
        # Try Ollama first if available
        if settings.llm_provider == "ollama" and is_ollama_available():
            try:
                return self.generate_ollama(messages, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama failed, falling back to OpenAI: {e}")

        # Fallback to OpenAI
        return self.generate_openai(messages, model, temperature, max_tokens)
