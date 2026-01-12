"""
Voice (STT/TTS) related Pydantic models.
Aligned with CONTRACT.md Part 4: Voice.
"""

from pydantic import BaseModel
from typing import Optional


class STTResponse(BaseModel):
    """Response model for POST /voice/stt."""
    session_id: str
    text: str
    duration_ms: Optional[int] = None


class TTSRequest(BaseModel):
    """Request model for POST /voice/tts."""
    session_id: str
    text: str
    voice: str = "default"
