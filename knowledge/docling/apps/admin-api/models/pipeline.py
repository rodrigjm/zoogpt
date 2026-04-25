"""Pydantic models for pipeline management endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PipelineStageConfig(BaseModel):
    """Configuration for a single pipeline stage."""
    provider: str
    model: Optional[str] = None


class PipelineConfig(BaseModel):
    """Full pipeline configuration across all stages."""
    stt: PipelineStageConfig
    llm: PipelineStageConfig
    tts: PipelineStageConfig


class PipelineStageUpdate(BaseModel):
    """Request to update a single stage's provider/model."""
    provider: str
    model: Optional[str] = None


class BenchmarkRequest(BaseModel):
    """Request to start a benchmark run."""
    concurrency: int = Field(5, description="Number of concurrent requests")
    rounds: int = Field(3, description="Number of rounds to run")


class BenchmarkMetrics(BaseModel):
    """Latency percentiles and success rate."""
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    success_rate: float


class CostBreakdown(BaseModel):
    """Per-request cost breakdown with token/char counts."""
    input_tokens_avg: Optional[float] = None
    output_tokens_avg: Optional[float] = None
    characters_avg: Optional[float] = None
    audio_seconds_avg: Optional[float] = None


class BenchmarkResult(BaseModel):
    """Result of a completed benchmark run."""
    id: str
    stage: str
    provider: str
    model: Optional[str]
    timestamp: str
    concurrency: int
    rounds: int
    total_requests: int
    metrics: BenchmarkMetrics
    cost_per_request: float
    cost_breakdown: CostBreakdown


class BenchmarkStatus(BaseModel):
    """Status of a running or completed benchmark."""
    stage: str
    running: bool
    progress: Optional[str] = None  # e.g., "8/15 requests"
    completed_requests: int = 0
    total_requests: int = 0
    result: Optional[BenchmarkResult] = None


# Available models per provider per stage
AVAILABLE_MODELS = {
    "stt": {
        "faster-whisper": [{"id": "base", "name": "Base (local)", "description": "Fast, free, offline"}],
        "openai": [{"id": "whisper-1", "name": "Whisper v1", "description": "OpenAI cloud STT"}],
    },
    "llm": {
        "ollama": [
            {"id": "qwen2.5:3b", "name": "Qwen 2.5 3B", "description": "Fast, lightweight"},
            {"id": "phi4", "name": "Phi-4", "description": "Microsoft, good reasoning"},
            {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Meta, general purpose"},
        ],
        "openai": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast, cheap"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Most capable, higher cost"},
        ],
    },
    "tts": {
        "kokoro": [
            {"id": "af_heart", "name": "Heart", "description": "Expressive, upbeat female"},
            {"id": "af_bella", "name": "Bella", "description": "Friendly female"},
            {"id": "af_nova", "name": "Nova", "description": "Warm, engaging female"},
            {"id": "af_sarah", "name": "Sarah", "description": "Calm, gentle female"},
            {"id": "am_adam", "name": "Adam", "description": "Clear male voice"},
            {"id": "am_eric", "name": "Eric", "description": "Friendly male"},
        ],
        "openai": [
            {"id": "tts-1", "name": "TTS-1", "description": "Standard quality"},
        ],
        "elevenlabs": [
            {"id": "default", "name": "Default", "description": "ElevenLabs default voice"},
        ],
    },
}
