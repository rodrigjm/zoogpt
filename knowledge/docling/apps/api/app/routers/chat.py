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
from ..services.rag import RAGService, get_fallback_questions
from ..services.analytics import get_analytics_service
from ..services.safety import (
    validate_input,
    validate_output,
    BLOCKED_INPUT_RESPONSE,
    SAFE_FALLBACK_RESPONSE,
)
from ..utils.timing import RequestTimer


router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
_session_service = SessionService()
_rag_service = RAGService()
_analytics_service = get_analytics_service()


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
    timer = RequestTimer("CHAT", body.session_id[:8] if body.session_id else None)
    timer.mark(f"Question: '{body.message[:50]}...'")

    # Validate session exists
    timer.mark("Validating session")
    session = _session_service.get_session(body.session_id)
    if not session:
        timer.end("SESSION_NOT_FOUND")
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

    # Safety: Validate input before sending to LLM
    timer.mark("Safety: Validating input")
    input_check = validate_input(body.message)
    if not input_check.is_safe:
        timer.end(f"INPUT_BLOCKED: {input_check.reason}")
        # Log blocked message for abuse monitoring
        _session_service.log_blocked_message(
            body.session_id, body.message, input_check.reason or "safety_filter"
        )
        message_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        return {
            "session_id": body.session_id,
            "message_id": message_id,
            "reply": BLOCKED_INPUT_RESPONSE,
            "sources": [],
            "followup_questions": get_fallback_questions(3),
            "confidence": 0.0,
            "created_at": now.isoformat(),
        }

    # Generate unique message ID
    message_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    # RAG retrieval with timing
    timer.mark("RAG: Searching context")
    with timer.component("rag"):
        context, sources, confidence = _rag_service.search_context(body.message)
    timer.mark(f"RAG: Found {len(sources)} sources")

    # Build message history
    messages = [{"role": "user", "content": body.message}]

    # Generate response with timing
    timer.mark("RAG: Generating response")
    with timer.component("llm"):
        reply = _rag_service.generate_response(messages, context)
    timer.mark(f"RAG: Response generated ({len(reply)} chars)")

    # Safety: Validate LLM output
    timer.mark("Safety: Validating output")
    output_check = validate_output(reply)
    if not output_check.is_safe:
        timer.end(f"OUTPUT_BLOCKED: {output_check.reason}")
        return {
            "session_id": body.session_id,
            "message_id": message_id,
            "reply": SAFE_FALLBACK_RESPONSE,
            "sources": [],
            "followup_questions": get_fallback_questions(3),
            "confidence": 0.0,
            "created_at": now.isoformat(),
        }

    total_ms = timer.end("SUCCESS")

    # Record analytics
    timings = timer.get_timings()
    _analytics_service.record_interaction(
        session_id=body.session_id,
        question=body.message,
        answer=reply,
        sources=sources,
        confidence_score=confidence,
        latency_ms=total_ms,
        rag_latency_ms=timings.rag_ms,
        llm_latency_ms=timings.llm_ms,
    )

    # Save chat history for feedback tracking
    _session_service.save_message(body.session_id, "user", body.message)
    _session_service.save_message(
        body.session_id,
        "assistant",
        reply,
        metadata={"sources": sources, "confidence": confidence}
    )

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
    timer = RequestTimer("CHAT_STREAM", body.session_id[:8] if body.session_id else None)
    timer.mark(f"Question: '{body.message[:50]}...'")

    # Validate session exists (regular JSON response for 404)
    timer.mark("Validating session")
    session = _session_service.get_session(body.session_id)
    if not session:
        timer.end("SESSION_NOT_FOUND")
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

    # Safety: Validate input before sending to LLM
    timer.mark("Safety: Validating input")
    input_check = validate_input(body.message)
    if not input_check.is_safe:
        timer.end(f"INPUT_BLOCKED: {input_check.reason}")
        # Log blocked message for abuse monitoring
        _session_service.log_blocked_message(
            body.session_id, body.message, input_check.reason or "safety_filter"
        )

        async def blocked_generator():
            # Send blocked response as a single text chunk + done
            yield {"data": StreamChunk(type="text", content=BLOCKED_INPUT_RESPONSE).model_dump_json()}
            yield {"data": StreamChunk(
                type="done",
                sources=[],
                followup_questions=get_fallback_questions(3),
            ).model_dump_json()}

        return EventSourceResponse(blocked_generator())

    async def event_generator():
        """Generate SSE events for streaming chat response."""
        try:
            # RAG retrieval before streaming
            timer.mark("RAG: Searching context")
            with timer.component("rag"):
                context, sources, confidence = _rag_service.search_context(body.message)
            timer.mark(f"RAG: Found {len(sources)} sources")

            # Build message history
            messages = [{"role": "user", "content": body.message}]

            # Accumulate full response for follow-up question extraction
            full_response = ""

            # Stream text chunks with LLM timing
            timer.mark("RAG: Starting response stream")
            first_chunk = True
            chunk_count = 0
            import time
            llm_start = time.perf_counter()

            for chunk_text in _rag_service.generate_response_stream(messages, context):
                if first_chunk:
                    timer.mark("RAG: First token received")
                    first_chunk = False
                full_response += chunk_text
                chunk_count += 1
                chunk = StreamChunk(type="text", content=chunk_text)
                yield {"data": chunk.model_dump_json()}

            # Record LLM timing
            timer.component_timings["llm"] = int((time.perf_counter() - llm_start) * 1000)
            timer.mark(f"RAG: Stream complete ({chunk_count} chunks, {len(full_response)} chars)")

            # Extract follow-up questions from full response
            _, followup_questions = _rag_service.extract_followup_questions(full_response)

            # Send done event with sources and follow-up questions
            done_chunk = StreamChunk(
                type="done",
                sources=sources,
                followup_questions=followup_questions,
            )
            yield {"data": done_chunk.model_dump_json()}

            total_ms = timer.end("SUCCESS")

            # Record analytics
            timings = timer.get_timings()
            _analytics_service.record_interaction(
                session_id=body.session_id,
                question=body.message,
                answer=full_response,
                sources=sources,
                confidence_score=confidence,
                latency_ms=total_ms,
                rag_latency_ms=timings.rag_ms,
                llm_latency_ms=timings.llm_ms,
            )

            # Save chat history for feedback tracking
            _session_service.save_message(body.session_id, "user", body.message)
            _session_service.save_message(
                body.session_id,
                "assistant",
                full_response,
                metadata={"sources": sources, "confidence": confidence}
            )

        except Exception as e:
            timer.end("ERROR")
            # Send error event
            error_chunk = StreamChunk(
                type="error",
                content=str(e),
            )
            yield {"data": error_chunk.model_dump_json()}

    return EventSourceResponse(event_generator())
