"""
Internal benchmark endpoints for per-stage latency measurement.

These endpoints are called by the admin-api benchmark service to measure
individual stage performance in isolation. Not exposed to external traffic.
"""

import io
import logging
import random
import time

from fastapi import APIRouter

from ..config import settings
from ..services.llm import LLMService
from ..services.rag import RAGService
from ..services.stt import STTService
from ..services.tts import TTSService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/benchmark", tags=["benchmark"])

# Service singletons for benchmark endpoints
_rag_service = RAGService()
_stt_service = STTService(openai_api_key=settings.openai_api_key)
_tts_service = TTSService(openai_api_key=settings.openai_api_key)
_llm_service = LLMService(openai_api_key=settings.openai_api_key)

# Test data
TEST_QUESTIONS = [
    "What do elephants eat?",
    "How fast can a cheetah run?",
    "Do penguins live at the zoo?",
    "What sounds does a lion make?",
    "How long do turtles live?",
]

TEST_TTS_TEXT = (
    "Elephants are amazing animals! They can eat up to 300 pounds of food every single day. "
    "They love munching on grasses, leaves, bark, and fruit. At Leesburg Animal Park, "
    "our elephants get a special diet to keep them healthy and happy!"
)


@router.post("/stt")
async def benchmark_stt():
    """
    Benchmark STT stage.
    Uses a generated short audio clip for consistent measurement.
    """
    import numpy as np
    import soundfile as sf

    sample_rate = 16000
    duration = 2.0
    audio_data = (np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.01)
    buf = io.BytesIO()
    sf.write(buf, audio_data, sample_rate, format="WAV")
    audio_bytes = buf.getvalue()

    start = time.monotonic()
    try:
        result = await _stt_service.transcribe(audio_bytes)
    except Exception as e:
        logger.warning(f"STT benchmark failed: {e}")
        result = ""
    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 1),
        "audio_seconds": duration,
        "transcript_length": len(result),
    }


@router.post("/llm")
async def benchmark_llm():
    """
    Benchmark LLM + RAG stage.
    Runs a random test question through RAG retrieval + LLM generation.
    """
    question = random.choice(TEST_QUESTIONS)

    start = time.monotonic()

    # RAG retrieval — returns (context_str, sources, confidence)
    context, _sources, _confidence = await _rag_service.search_context(question)

    # LLM generation
    messages = [
        {"role": "system", "content": "You are a helpful zoo assistant. Answer briefly."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"},
    ]

    response = await _llm_service.generate(messages, temperature=0.7, max_tokens=200)

    elapsed_ms = (time.monotonic() - start) * 1000

    # Approximate token counts (1 token ~ 4 chars)
    input_text = " ".join(m["content"] for m in messages)
    input_tokens = len(input_text) // 4
    output_tokens = len(response) // 4

    return {
        "latency_ms": round(elapsed_ms, 1),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


@router.post("/tts")
async def benchmark_tts():
    """
    Benchmark TTS stage.
    Synthesizes a fixed test text and returns timing and character count.
    """
    start = time.monotonic()

    try:
        audio_bytes = await _tts_service.synthesize(text=TEST_TTS_TEXT)
    except Exception as e:
        logger.warning(f"TTS benchmark failed: {e}")
        audio_bytes = b""

    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 1),
        "characters": len(TEST_TTS_TEXT),
        "audio_bytes": len(audio_bytes),
    }
