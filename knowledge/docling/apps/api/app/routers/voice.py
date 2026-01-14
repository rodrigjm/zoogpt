"""
Voice (STT/TTS) router.
Per CONTRACT.md Part 4: Voice.
"""

import base64
import json
import logging
import re
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

from ..models import STTResponse, TTSRequest, ErrorResponse
from ..models.voice import TTSStreamRequest
from ..services.rag import RAGService
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
_rag_service = RAGService()

router = APIRouter(prefix="/voice", tags=["voice"])


# Sentence boundary detection for streaming TTS
SENTENCE_ENDINGS = re.compile(r'[.!?]+(?:\s|$)')


def extract_sentences(buffer: str) -> tuple[list[str], str]:
    """
    Extract complete sentences from buffer, return (sentences, remaining).
    
    Returns sentences that end with proper punctuation, keeps incomplete
    text in the remaining buffer.
    """
    sentences = []
    last_end = 0
    
    for match in SENTENCE_ENDINGS.finditer(buffer):
        end_pos = match.end()
        sentence = buffer[last_end:end_pos].strip()
        if sentence:
            sentences.append(sentence)
        last_end = end_pos
    
    remaining = buffer[last_end:]
    return sentences, remaining


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


@router.post(
    "/tts/stream",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Streaming audio via SSE",
            "content": {"text/event-stream": {}}
        },
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def tts_stream(body: TTSStreamRequest):
    """
    Stream TTS audio as RAG response is generated.
    
    Reduces latency by generating and sending audio sentence-by-sentence
    instead of waiting for the full response.
    
    SSE Events:
    - event: audio
      data: {chunk: base64_audio, sentence: text, index: n}
    - event: done
      data: {total_sentences: n}
    - event: error
      data: {code: str, message: str}
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

    async def generate_audio_stream():
        """Generator that yields SSE events with audio chunks."""
        buffer = ""
        sentence_index = 0
        
        try:
            # Get RAG context
            context, sources, _ = _rag_service.search_context(body.message)
            
            # Build message history
            messages = [{"role": "user", "content": body.message}]
            
            # Stream RAG response and generate TTS per sentence
            for chunk in _rag_service.generate_response_stream(messages, context):
                buffer += chunk
                
                # Extract complete sentences
                sentences, buffer = extract_sentences(buffer)
                
                for sentence in sentences:
                    if sentence.strip():
                        try:
                            # Generate audio for this sentence
                            audio_bytes = _tts_service.synthesize_kokoro(
                                sentence, 
                                voice=body.voice,
                                chunk_long_text=False  # Already chunked by sentence
                            )
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                            
                            # Yield audio event
                            yield {
                                "event": "audio",
                                "data": json.dumps({
                                    "chunk": audio_b64,
                                    "sentence": sentence,
                                    "index": sentence_index
                                })
                            }
                            sentence_index += 1
                            
                        except Exception as e:
                            logger.warning(f"TTS failed for sentence {sentence_index}: {e}")
                            # Continue with next sentence
            
            # Process any remaining text in buffer
            if buffer.strip():
                try:
                    audio_bytes = _tts_service.synthesize_kokoro(
                        buffer.strip(),
                        voice=body.voice,
                        chunk_long_text=False
                    )
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    yield {
                        "event": "audio",
                        "data": json.dumps({
                            "chunk": audio_b64,
                            "sentence": buffer.strip(),
                            "index": sentence_index
                        })
                    }
                    sentence_index += 1
                except Exception as e:
                    logger.warning(f"TTS failed for final buffer: {e}")
            
            # Send completion event
            yield {
                "event": "done",
                "data": json.dumps({
                    "total_sentences": sentence_index,
                    "sources": sources
                })
            }
            
        except Exception as e:
            logger.error(f"Streaming TTS failed: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "code": "STREAM_FAILED",
                    "message": str(e)
                })
            }

    return EventSourceResponse(generate_audio_stream())
