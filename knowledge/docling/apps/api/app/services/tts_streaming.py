"""
Streaming TTS service for Kokoro-FastAPI sidecar.

This service connects to the Kokoro-FastAPI container running as a sidecar
and streams audio chunks back as they are generated, reducing latency.
"""

import logging
from typing import AsyncIterator

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


async def stream_tts_audio(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0
) -> AsyncIterator[bytes]:
    """
    Stream TTS audio from Kokoro-FastAPI sidecar.

    This function makes a streaming HTTP request to the Kokoro-FastAPI
    service and yields audio chunks as they become available.

    Args:
        text: Text to convert to speech
        voice: Voice ID (e.g., 'af_heart', 'af_bella')
        speed: Speech speed multiplier (0.5-2.0)

    Yields:
        Audio chunks as bytes (PCM format, 24kHz)

    Raises:
        httpx.HTTPError: If the request fails
    """
    url = f"{settings.kokoro_tts_url}/v1/audio/speech"

    payload = {
        "input": text,
        "voice": voice,
        "model": "kokoro",
        "response_format": "pcm",  # Raw PCM for lowest latency
        "speed": speed
    }

    try:
        logger.info(f"[TTS_STREAM] Requesting streaming TTS from {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                # Stream audio chunks as they arrive
                chunk_count = 0
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        chunk_count += 1
                        logger.debug(f"[TTS_STREAM] Yielding chunk {chunk_count} ({len(chunk)} bytes)")
                        yield chunk

                logger.info(f"[TTS_STREAM] Streaming complete: {chunk_count} chunks")

    except httpx.HTTPError as e:
        logger.error(f"[TTS_STREAM] HTTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"[TTS_STREAM] Unexpected error: {e}")
        raise


async def stream_tts_with_fallback(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    fallback_to_local: bool = True
) -> AsyncIterator[bytes]:
    """
    Stream TTS with automatic fallback to local synthesis.

    Attempts to use the Kokoro-FastAPI sidecar for streaming. If it fails,
    falls back to local Kokoro-ONNX synthesis.

    Args:
        text: Text to convert to speech
        voice: Voice ID (e.g., 'af_heart', 'af_bella')
        speed: Speech speed multiplier (0.5-2.0)
        fallback_to_local: Whether to fall back to local synthesis on error

    Yields:
        Audio chunks as bytes

    Raises:
        Exception: If both streaming and fallback fail
    """
    try:
        # Try streaming first
        async for chunk in stream_tts_audio(text, voice, speed):
            yield chunk

    except Exception as e:
        if not fallback_to_local:
            raise

        logger.warning(f"[TTS_STREAM] Streaming failed, falling back to local synthesis: {e}")

        # Fallback to local Kokoro-ONNX
        from .tts import TTSService
        tts_service = TTSService(
            openai_api_key=settings.openai_api_key,
            default_voice=voice
        )

        try:
            audio_bytes = tts_service.synthesize_kokoro(text, voice=voice, speed=speed)
            # Yield the entire audio as a single chunk
            yield audio_bytes
            logger.info("[TTS_STREAM] Fallback synthesis complete")

        except Exception as fallback_error:
            logger.error(f"[TTS_STREAM] Fallback synthesis also failed: {fallback_error}")
            raise
