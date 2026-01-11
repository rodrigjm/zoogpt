"""
Voice (STT/TTS) related Pydantic models.
Aligned with CONTRACT.md Part 4: Voice.
"""

from pydantic import BaseModel


class STTResponse(BaseModel):
    """Response model for POST /voice/stt."""
    session_id: str
    text: str


class TTSRequest(BaseModel):
    """Request model for POST /voice/tts."""
    session_id: str
    text: str
    voice: str = "default"
