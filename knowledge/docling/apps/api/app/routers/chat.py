"""
Chat router - implements POST /chat and POST /chat/stream.
Per CONTRACT.md Part 4: Chat.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
import uuid
from sse_starlette.sse import EventSourceResponse

from ..models import ChatRequest, ErrorResponse, StreamChunk
from ..services.session import SessionService
from ..services.rag import RAGService


router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
_session_service = SessionService()
_rag_service = RAGService()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Chat response generated successfully"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def chat(body: ChatRequest):
    """
    Send a chat message for a given session.

    Per CONTRACT.md:
    - Request: {session_id, message, mode?, metadata?}
    - Response 200: {session_id, message_id, reply, sources, created_at}
    - Response 404: Session not found (standard error shape)
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

    # Generate unique message ID
    message_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    # RAG retrieval and generation
    context, sources, _ = _rag_service.search_context(body.message)

    # Build message history
    messages = [{"role": "user", "content": body.message}]

    # Generate response
    reply = _rag_service.generate_response(messages, context)

    # Return response per CONTRACT.md
    return {
        "session_id": body.session_id,
        "message_id": message_id,
        "reply": reply,
        "sources": sources,
        "created_at": now.isoformat(),
    }


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "SSE stream of chat response"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def chat_stream(body: ChatRequest):
    """
    Stream chat response using Server-Sent Events.

    SSE Event Sequence:
    1. Validate session (return 404 JSON if not found)
    2. Search context before streaming
    3. Stream text chunks: {"type": "text", "content": "chunk"}
    4. Send done event: {"type": "done", "sources": [...], "followup_questions": [...]}
    5. On error: {"type": "error", "content": "error message"}
    """
    # Validate session exists (regular JSON response for 404)
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

    async def event_generator():
        """Generate SSE events for streaming chat response."""
        try:
            # RAG retrieval before streaming
            context, sources, _ = _rag_service.search_context(body.message)

            # Build message history
            messages = [{"role": "user", "content": body.message}]

            # Accumulate full response for follow-up question extraction
            full_response = ""

            # Stream text chunks
            for chunk_text in _rag_service.generate_response_stream(messages, context):
                full_response += chunk_text
                chunk = StreamChunk(type="text", content=chunk_text)
                yield {"data": chunk.model_dump_json()}

            # Extract follow-up questions from full response
            _, followup_questions = _rag_service.extract_followup_questions(full_response)

            # Send done event with sources and follow-up questions
            done_chunk = StreamChunk(
                type="done",
                sources=sources,
                followup_questions=followup_questions,
            )
            yield {"data": done_chunk.model_dump_json()}

        except Exception as e:
            # Send error event
            error_chunk = StreamChunk(
                type="error",
                content=str(e),
            )
            yield {"data": error_chunk.model_dump_json()}

    return EventSourceResponse(event_generator())
