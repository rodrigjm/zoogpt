"""
Unit tests for Pydantic models.
Tests validation rules per Task 1.1 of migration.md.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    ChatRequest,
    ChatResponse,
    StreamChunk,
    Session,
    SessionCreate,
    SessionResponse,
    ChatMessage,
    STTResponse,
    TTSRequest,
)


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_request(self):
        """Valid request should pass."""
        req = ChatRequest(session_id="test-123", message="Hello")
        assert req.session_id == "test-123"
        assert req.message == "Hello"
        assert req.mode == "rag"  # default

    def test_message_min_length(self):
        """Empty message should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(session_id="test-123", message="")
        assert "message" in str(exc_info.value)

    def test_message_max_length(self):
        """Message over 1000 chars should fail validation."""
        long_message = "x" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(session_id="test-123", message=long_message)
        assert "message" in str(exc_info.value)

    def test_message_at_max_length(self):
        """Message at exactly 1000 chars should pass."""
        message = "x" * 1000
        req = ChatRequest(session_id="test-123", message=message)
        assert len(req.message) == 1000

    def test_optional_metadata(self):
        """Metadata is optional."""
        req = ChatRequest(session_id="test-123", message="Hi")
        assert req.metadata is None

        req_with_meta = ChatRequest(
            session_id="test-123",
            message="Hi",
            metadata={"key": "value"}
        )
        assert req_with_meta.metadata == {"key": "value"}


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_valid_response(self):
        """Valid response should pass."""
        resp = ChatResponse(
            session_id="test-123",
            message_id="msg-456",
            reply="Hello there!",
            created_at=datetime.now()
        )
        assert resp.reply == "Hello there!"
        assert resp.sources == []  # default
        assert resp.followup_questions == []  # default
        assert resp.confidence == 1.0  # default

    def test_confidence_range_valid(self):
        """Confidence within 0-1 should pass."""
        resp = ChatResponse(
            session_id="test-123",
            message_id="msg-456",
            reply="Test",
            created_at=datetime.now(),
            confidence=0.5
        )
        assert resp.confidence == 0.5

    def test_confidence_below_zero(self):
        """Confidence below 0 should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse(
                session_id="test-123",
                message_id="msg-456",
                reply="Test",
                created_at=datetime.now(),
                confidence=-0.1
            )
        assert "confidence" in str(exc_info.value)

    def test_confidence_above_one(self):
        """Confidence above 1 should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse(
                session_id="test-123",
                message_id="msg-456",
                reply="Test",
                created_at=datetime.now(),
                confidence=1.5
            )
        assert "confidence" in str(exc_info.value)

    def test_with_followup_questions(self):
        """Response with followup questions."""
        resp = ChatResponse(
            session_id="test-123",
            message_id="msg-456",
            reply="Test",
            created_at=datetime.now(),
            followup_questions=["What else?", "Tell me more"]
        )
        assert len(resp.followup_questions) == 2


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_text_chunk(self):
        """Text chunk type."""
        chunk = StreamChunk(type="text", content="Hello")
        assert chunk.type == "text"
        assert chunk.content == "Hello"

    def test_done_chunk(self):
        """Done chunk with followups."""
        chunk = StreamChunk(
            type="done",
            followup_questions=["Q1?", "Q2?"],
            sources=[{"title": "Source 1"}]
        )
        assert chunk.type == "done"
        assert chunk.followup_questions is not None
        assert len(chunk.followup_questions) == 2

    def test_error_chunk(self):
        """Error chunk type."""
        chunk = StreamChunk(type="error", content="Something went wrong")
        assert chunk.type == "error"

    def test_invalid_type(self):
        """Invalid chunk type should fail."""
        with pytest.raises(ValidationError):
            StreamChunk(type="invalid")


class TestSession:
    """Tests for Session model."""

    def test_valid_session(self):
        """Valid session should pass."""
        session = Session(
            session_id="sess-123",
            created_at=datetime.now()
        )
        assert session.session_id == "sess-123"
        assert session.message_count == 0  # default
        assert session.client == "web"  # default

    def test_full_session(self):
        """Session with all fields."""
        now = datetime.now()
        session = Session(
            session_id="sess-123",
            created_at=now,
            last_active=now,
            message_count=10,
            client="mobile",
            metadata={"version": "1.0"}
        )
        assert session.message_count == 10
        assert session.client == "mobile"


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_user_message(self):
        """User message role."""
        msg = ChatMessage(
            message_id="msg-123",
            session_id="sess-456",
            role="user",
            content="Hello",
            created_at=datetime.now()
        )
        assert msg.role == "user"

    def test_assistant_message(self):
        """Assistant message role."""
        msg = ChatMessage(
            message_id="msg-123",
            session_id="sess-456",
            role="assistant",
            content="Hi there!",
            created_at=datetime.now()
        )
        assert msg.role == "assistant"

    def test_invalid_role(self):
        """Invalid role should fail."""
        with pytest.raises(ValidationError):
            ChatMessage(
                message_id="msg-123",
                session_id="sess-456",
                role="system",  # not allowed
                content="Test",
                created_at=datetime.now()
            )


class TestSessionModels:
    """Tests for SessionCreate and SessionResponse."""

    def test_session_create_defaults(self):
        """SessionCreate with defaults."""
        create = SessionCreate()
        assert create.client == "web"
        assert create.metadata is None

    def test_session_response(self):
        """SessionResponse per CONTRACT.md."""
        resp = SessionResponse(
            session_id="sess-123",
            created_at=datetime.now(),
            metadata={"key": "value"}
        )
        assert resp.session_id == "sess-123"
        assert resp.metadata == {"key": "value"}

    def test_session_response_minimal(self):
        """SessionResponse with minimal fields."""
        resp = SessionResponse(
            session_id="sess-123",
            created_at=datetime.now()
        )
        assert resp.session_id == "sess-123"
        assert resp.metadata is None


class TestSTTResponse:
    """Tests for STTResponse model."""

    def test_with_duration(self):
        """STTResponse with duration."""
        resp = STTResponse(
            session_id="sess-123",
            text="Hello world",
            duration_ms=1500
        )
        assert resp.duration_ms == 1500

    def test_without_duration(self):
        """STTResponse without duration (optional)."""
        resp = STTResponse(
            session_id="sess-123",
            text="Hello world"
        )
        assert resp.duration_ms is None


class TestTTSRequest:
    """Tests for TTSRequest model."""

    def test_default_voice(self):
        """TTSRequest with default voice."""
        req = TTSRequest(
            session_id="sess-123",
            text="Hello"
        )
        assert req.voice == "default"

    def test_custom_voice(self):
        """TTSRequest with custom voice."""
        req = TTSRequest(
            session_id="sess-123",
            text="Hello",
            voice="nova"
        )
        assert req.voice == "nova"
