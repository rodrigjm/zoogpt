"""
Voice (STT/TTS) router.
Per CONTRACT.md Part 4: Voice.
"""

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse, Response
from typing import Annotated
import logging

from ..models import STTResponse, TTSRequest, ErrorResponse
from ..services.session import SessionService
from ..services.stt import STTService
from ..services.tts import TTSService
from ..config import settings

logger = logging.getLogger(__name__)

# Initialize services
_session_service = SessionService()
_stt_service = STTService(openai_api_key=settings.openai_api_key)
_tts_service = TTSService(
    openai_api_key=settings.openai_api_key,
    default_voice=settings.tts_voice
)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post(
    "/stt",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": STTResponse, "description": "Audio transcribed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def speech_to_text(
    session_id: Annotated[str, Form()],
    audio: Annotated[UploadFile, File()],
):
    """
    Convert speech to text.

    Per CONTRACT.md Part 4:
    - Request: multipart/form-data with session_id and audio file
    - Response 200: {session_id, text}
    - Supports common browser formats: webm, wav, mp3
    """
    # Validate session exists
    session = _session_service.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session {session_id} not found",
                    "details": {},
                }
            },
        )

    # Validate audio file is provided
    if not audio or not audio.filename:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_AUDIO",
                    "message": "Audio file is required",
                    "details": {},
                }
            },
        )

    # Read audio bytes
    audio_bytes = await audio.read()

    # Validate audio has content
    if len(audio_bytes) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "EMPTY_AUDIO",
                    "message": "Audio file is empty",
                    "details": {},
                }
            },
        )

    # Transcribe audio using STT service
    try:
        text = _stt_service.transcribe(audio_bytes)
    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "TRANSCRIPTION_FAILED",
                    "message": "Failed to transcribe audio",
                    "details": {"error": str(e)},
                }
            },
        )

    return STTResponse(
        session_id=session_id,
        text=text,
    )


@router.post(
    "/tts",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Audio generated successfully",
            "content": {
                "audio/wav": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def text_to_speech(body: TTSRequest):
    """
    Convert text to speech.

    Per CONTRACT.md Part 4:
    - Request: {session_id, text, voice}
    - Response 200: audio bytes (audio/wav)
    """
    # Validate session exists
    session = _session_service.get_session(body.session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session {body.session_id} not found",
                    "details": {},
                }
            },
        )

    # Validate text is not empty
    if not body.text or not body.text.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "EMPTY_TEXT",
                    "message": "Text cannot be empty",
                    "details": {},
                }
            },
        )

    # Synthesize speech using TTS service
    try:
        audio_bytes = _tts_service.synthesize(text=body.text, voice=body.voice)
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "SYNTHESIS_FAILED",
                    "message": "Failed to generate speech",
                    "details": {"error": str(e)},
                }
            },
        )

    # Return audio as WAV file
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=speech.wav"
        }
    )
