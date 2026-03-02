"""Configuration models for Admin API."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PromptsConfig(BaseModel):
    """Prompt configuration."""
    system_prompt: str
    fallback_response: str
    followup_questions: List[str]


class ModelConfig(BaseModel):
    """LLM model configuration."""
    name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 500


class VoicePreset(BaseModel):
    """Voice preset definition."""
    id: str
    name: str
    description: str


class TTSConfig(BaseModel):
    """TTS configuration."""
    provider: str = "kokoro"
    default_voice: str = "af_heart"
    speed: float = 1.0
    fallback_provider: str = "openai"
    available_voices: Dict[str, List[VoicePreset]] = {}


class TTSPreviewRequest(BaseModel):
    """TTS preview request."""
    text: str
    voice: str
    speed: float = 1.0


class TTSPreviewResponse(BaseModel):
    """TTS preview response."""
    audio_base64: str
    duration_ms: int
    voice: str


class FullConfig(BaseModel):
    """Complete admin configuration."""
    version: str = "1.0"
    prompts: PromptsConfig
    model: ModelConfig
    tts: TTSConfig
