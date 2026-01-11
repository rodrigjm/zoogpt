"""
Kokoro TTS - Local Text-to-Speech Inference Module

Uses hexgrad/Kokoro-82M for low-latency, high-quality TTS.
https://huggingface.co/hexgrad/Kokoro-82M

Requirements:
- pip install kokoro>=0.9.4 soundfile
- System: espeak-ng (brew install espeak-ng / apt-get install espeak-ng)
"""

import io
import re
from typing import Optional
import numpy as np
import soundfile as sf

from utils.text import strip_markdown

# Lazy-loaded pipeline (cached globally)
_pipeline = None
_pipeline_error = None


# Kid-friendly voice presets
VOICE_PRESETS = {
    "bella": "af_bella",      # Friendly female, clear pronunciation (default)
    "nova": "af_nova",        # Warm, engaging female
    "heart": "af_heart",      # Expressive, upbeat female
    "sarah": "af_sarah",      # Calm, gentle female
    "adam": "am_adam",        # Clear male voice
    "eric": "am_eric",        # Friendly male
}

DEFAULT_VOICE = "af_bella"


def get_kokoro_pipeline():
    """
    Lazy-load and cache the Kokoro pipeline.
    Returns None if initialization fails.
    """
    global _pipeline, _pipeline_error

    if _pipeline_error:
        print(f"[KOKORO] Pipeline previously failed: {_pipeline_error}", flush=True)
        return None

    if _pipeline is None:
        try:
            print("[KOKORO] Initializing KPipeline (first load may take a few seconds)...", flush=True)
            from kokoro import KPipeline
            _pipeline = KPipeline(lang_code='a')  # American English
            print("[KOKORO] Pipeline initialized successfully!", flush=True)
        except Exception as e:
            _pipeline_error = str(e)
            print(f"[KOKORO] Pipeline initialization FAILED: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None

    return _pipeline


def is_kokoro_available() -> bool:
    """Check if Kokoro TTS is available and working."""
    return get_kokoro_pipeline() is not None


def get_pipeline_error() -> Optional[str]:
    """Get the error message if pipeline failed to initialize."""
    return _pipeline_error


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Split text into optimal chunks for TTS.
    Kokoro works best with 100-200 tokens (~500-1000 chars).
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


def generate_speech_kokoro(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    chunk_long_text: bool = True
) -> bytes:
    """
    Generate speech using local Kokoro-82M model.

    Args:
        text: Text to convert to speech
        voice: Voice ID (e.g., 'af_bella', 'am_adam') or preset name
        speed: Speech speed multiplier (0.5-2.0)
        chunk_long_text: Whether to chunk long text for better quality

    Returns:
        Audio bytes in WAV format (24kHz)

    Raises:
        RuntimeError: If Kokoro pipeline is not available
    """
    pipeline = get_kokoro_pipeline()
    if pipeline is None:
        raise RuntimeError(f"Kokoro TTS not available: {_pipeline_error}")

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
    all_audio = []
    for chunk in chunks:
        for _, _, audio in pipeline(chunk, voice=voice, speed=speed):
            all_audio.append(audio)

    # Concatenate all audio chunks
    full_audio = np.concatenate(all_audio)

    # Convert to WAV bytes
    buffer = io.BytesIO()
    sf.write(buffer, full_audio, 24000, format='WAV')
    buffer.seek(0)

    return buffer.read()


def list_voices() -> dict[str, str]:
    """Return available voice presets."""
    return VOICE_PRESETS.copy()
