"""
Text-to-Speech (TTS) service with local-first, cloud fallback.

Fallback chain:
1. Kokoro (local) - high quality, kid-friendly voices
2. OpenAI TTS API (cloud) - paid fallback
"""

import io
import re
import logging
from typing import Optional

import numpy as np
import soundfile as sf
from openai import OpenAI

from ..config import dynamic_config
from ..utils.timing import timed_print

logger = logging.getLogger(__name__)

# Global lazy-loaded pipeline
_kokoro_pipeline: Optional[object] = None
_kokoro_pipeline_error: Optional[str] = None

# Kid-friendly voice presets
VOICE_PRESETS = {
    "bella": "af_bella",      # Friendly female, clear pronunciation (default)
    "nova": "af_nova",        # Warm, engaging female
    "heart": "af_heart",      # Expressive, upbeat female
    "sarah": "af_sarah",      # Calm, gentle female
    "adam": "am_adam",        # Clear male voice
    "eric": "am_eric",        # Friendly male
    "default": "af_heart",    # Default voice
}

# Note: Default voice is now loaded dynamically from admin_config.json
# via dynamic_config.tts_default_voice


def get_kokoro_pipeline():
    """
    Lazy-load and cache the Kokoro pipeline.
    Returns None if initialization fails.
    """
    global _kokoro_pipeline, _kokoro_pipeline_error

    if _kokoro_pipeline_error:
        logger.debug(f"[KOKORO] Pipeline previously failed: {_kokoro_pipeline_error}")
        return None

    if _kokoro_pipeline is None:
        try:
            logger.info("[KOKORO] Initializing KPipeline...")
            from kokoro import KPipeline
            _kokoro_pipeline = KPipeline(lang_code='a')  # American English
            logger.info("[KOKORO] Pipeline initialized successfully")
        except Exception as e:
            _kokoro_pipeline_error = str(e)
            logger.warning(f"[KOKORO] Pipeline initialization failed: {e}")
            return None

    return _kokoro_pipeline


def is_kokoro_available() -> bool:
    """Check if Kokoro TTS is available."""
    return get_kokoro_pipeline() is not None


def preload_kokoro_pipeline() -> bool:
    """
    Preload the Kokoro pipeline at app startup.
    Call this during FastAPI lifespan to avoid first-request latency.

    Returns:
        True if pipeline loaded successfully, False otherwise.
    """
    logger.info("[KOKORO] Preloading TTS model at startup...")
    pipeline = get_kokoro_pipeline()
    if pipeline is not None:
        logger.info("[KOKORO] TTS model preloaded successfully")
        return True
    else:
        logger.warning("[KOKORO] TTS model preload failed - will use OpenAI fallback")
        return False


def strip_followup_questions(text: str) -> str:
    """
    Remove follow-up questions section from response for TTS.

    The follow-up questions section starts with "**Want to explore more?**"
    and should not be read aloud.

    Args:
        text: Response text potentially containing follow-up questions

    Returns:
        Text with follow-up questions section removed
    """
    # Try multiple patterns to handle LLM format variations
    patterns = [
        # **Want to explore more?...** and everything after
        r'\*\*Want to explore more\?.*',
        # Want to explore more? (without bold) and everything after
        r'Want to explore more\?.*',
        # "questions to ask" section and everything after
        r'Here are some.*questions to ask.*',
    ]

    result = text
    for pattern in patterns:
        new_result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE).strip()
        if new_result != result:
            return new_result

    return result.strip()


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text for TTS processing.

    Removes:
    - Bold (**text**)
    - Italic (*text*)
    - Headers (# ## ### etc.)
    - Links [text](url)
    - Follow-up questions section

    Args:
        text: Text containing markdown formatting

    Returns:
        Plain text with markdown removed
    """
    result = text
    result = strip_followup_questions(result)  # Remove follow-up questions first
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)  # Remove bold
    result = re.sub(r'\*([^*]+)\*', r'\1', result)  # Remove italic
    result = re.sub(r'#{1,6}\s*', '', result)  # Remove headers
    result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)  # Remove links
    return result.strip()


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Split text into optimal chunks for TTS.
    Kokoro works best with 100-200 tokens (~500-1000 chars).

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) < max_chars:
            current += sentence + " "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + " "

    if current:
        chunks.append(current.strip())

    return chunks if chunks else [text]


class TTSService:
    """
    Text-to-Speech service with local-first approach.

    Uses Kokoro locally when available, falls back to OpenAI API.
    """

    def __init__(self, openai_api_key: str, default_voice: str = dynamic_config.tts_default_voice):
        """
        Initialize TTS service.

        Args:
            openai_api_key: OpenAI API key for cloud fallback
            default_voice: Default voice preset to use
        """
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.default_voice = default_voice

    def synthesize_kokoro(
        self,
        text: str,
        voice: str = dynamic_config.tts_default_voice,
        speed: float = 1.0,
        chunk_long_text: bool = True
    ) -> bytes:
        """
        Generate speech using local Kokoro model.

        Args:
            text: Text to convert to speech
            voice: Voice ID (e.g., 'af_bella', 'am_adam') or preset name
            speed: Speech speed multiplier (0.5-2.0)
            chunk_long_text: Whether to chunk long text for better quality

        Returns:
            Audio bytes in WAV format (24kHz)

        Raises:
            RuntimeError: If Kokoro is not available or fails
        """
        pipeline = get_kokoro_pipeline()
        if pipeline is None:
            raise RuntimeError(f"Kokoro TTS not available: {_kokoro_pipeline_error}")

        # Resolve voice preset if using shorthand
        if voice in VOICE_PRESETS:
            voice = VOICE_PRESETS[voice]

        # Clean text for TTS (remove markdown)
        clean_text = strip_markdown(text)

        if not clean_text:
            raise ValueError("No text to convert to speech")

        # Chunk long text for better quality
        if chunk_long_text and len(clean_text) > 800:
            chunks = chunk_text(clean_text)
        else:
            chunks = [clean_text]

        # Generate audio for each chunk
        timed_print(f"  [TTS] Kokoro synthesizing {len(chunks)} chunk(s)...")
        all_audio = []
        for i, chunk in enumerate(chunks):
            for _, _, audio in pipeline(chunk, voice=voice, speed=speed):
                all_audio.append(audio)
            if len(chunks) > 1:
                timed_print(f"  [TTS] Kokoro chunk {i+1}/{len(chunks)} done")

        # Concatenate all audio chunks
        full_audio = np.concatenate(all_audio)

        # Convert to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, full_audio, 24000, format='WAV')
        buffer.seek(0)

        timed_print(f"  [TTS] Kokoro done: {len(full_audio)} samples, {len(buffer.getvalue())} bytes")
        return buffer.read()

    def synthesize_openai(
        self,
        text: str,
        voice: str = "nova"
    ) -> bytes:
        """
        Generate speech using OpenAI TTS API.

        Args:
            text: Text to convert to speech
            voice: OpenAI voice name (nova, alloy, shimmer, etc.)

        Returns:
            Audio bytes (format depends on OpenAI API)
        """
        # Clean text for TTS
        clean_text = strip_markdown(text)

        # Map preset names to OpenAI voices
        openai_voice_map = {
            "bella": "nova",
            "nova": "nova",
            "heart": "shimmer",
            "sarah": "nova",
            "adam": "onyx",
            "eric": "echo",
            "default": "nova",
        }
        openai_voice = openai_voice_map.get(voice, "nova")

        # Valid OpenAI voices
        valid_openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if openai_voice not in valid_openai_voices:
            openai_voice = "nova"

        # OpenAI TTS has 4096 character limit
        truncated_text = clean_text[:4096]

        timed_print(f"  [TTS] OpenAI API call starting (voice={openai_voice})...")
        with self.openai_client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=openai_voice,
            input=truncated_text,
            response_format="wav",  # Request WAV for browser compatibility
        ) as response:
            audio_bytes = response.read()

        timed_print(f"  [TTS] OpenAI done: {len(audio_bytes)} bytes")
        return audio_bytes

    def synthesize(
        self,
        text: str,
        voice: str = dynamic_config.tts_default_voice,
        speed: float = 1.0
    ) -> bytes:
        """
        Generate speech with local-first, cloud fallback strategy.

        Fallback chain:
        1. Try Kokoro (local) first - high quality, free, offline
        2. Fall back to OpenAI TTS API if local fails

        Args:
            text: Text to convert to speech
            voice: Voice preset name (bella, nova, heart, etc.)
            speed: Speech speed multiplier (only for Kokoro)

        Returns:
            Audio bytes in WAV format

        Raises:
            Exception: If all TTS methods fail
        """
        logger.info(f"[TTS] Starting synthesis for {len(text)} chars, voice={voice}")

        # 1. Try local Kokoro first
        if is_kokoro_available():
            logger.info("[TTS] Attempting Kokoro (local)...")
            try:
                audio = self.synthesize_kokoro(text, voice=voice, speed=speed)
                logger.info("[TTS] Kokoro succeeded")
                return audio
            except Exception as e:
                logger.warning(f"[TTS] Kokoro failed: {e}")
        else:
            logger.info("[TTS] Kokoro not available, using cloud fallback")

        # 2. Fall back to OpenAI TTS
        logger.info("[TTS] Attempting OpenAI TTS (cloud)...")
        try:
            audio = self.synthesize_openai(text, voice=voice)
            logger.info("[TTS] OpenAI TTS succeeded")
            return audio
        except Exception as e:
            logger.error(f"[TTS] All TTS methods failed: {e}")
            raise
