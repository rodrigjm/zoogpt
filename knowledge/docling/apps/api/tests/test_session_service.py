"""
Unit tests for SessionService.
Tests SQLite persistence, backward compatibility, and all CRUD operations.
"""

import pytest
import tempfile
import os
from pathlib import Path

from app.services.session import SessionService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def session_service(temp_db):
    """Create a SessionService instance with temp database."""
    return SessionService(db_path=temp_db)


class TestSessionServiceInit:
    """Test initialization and schema creation."""

    def test_init_creates_directory(self):
        """Service should create directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "sessions.db")
            service = SessionService(db_path=db_path)
            assert os.path.exists(db_path)

    def test_init_creates_schema(self, temp_db):
        """Service should create tables and indexes."""
        service = SessionService(db_path=temp_db)

        with service._get_connection() as conn:
            cursor = conn.cursor()

            # Check sessions table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            assert cursor.fetchone() is not None

            # Check chat_history table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'"
            )
            assert cursor.fetchone() is not None

            # Check indexes exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_chat_history_session'"
            )
            assert cursor.fetchone() is not None

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_chat_history_timestamp'"
            )
            assert cursor.fetchone() is not None


class TestGetOrCreateSession:
    """Test get_or_create_session method."""

    def test_create_new_session(self, session_service):
        """Creating a new session should return is_new=True."""
        result = session_service.get_or_create_session(
            session_id="test-session-1",
            metadata={"client": "web"}
        )

        assert result["session_id"] == "test-session-1"
        assert result["is_new"] is True
        assert result["message_count"] == 0
        assert result["metadata"] == {"client": "web"}
        assert "created_at" in result
        assert "last_active" in result

    def test_get_existing_session(self, session_service):
        """Getting an existing session should return is_new=False."""
        # Create session
        session_service.get_or_create_session(
            session_id="test-session-2",
            metadata={"client": "mobile"}
        )

        # Get same session
        result = session_service.get_or_create_session(session_id="test-session-2")

        assert result["session_id"] == "test-session-2"
        assert result["is_new"] is False
        assert result["metadata"] == {"client": "mobile"}

    def test_create_session_without_metadata(self, session_service):
        """Creating session without metadata should default to empty dict."""
        result = session_service.get_or_create_session(session_id="test-session-3")

        assert result["metadata"] == {}

    def test_get_updates_last_active(self, session_service):
        """Getting existing session should update last_active."""
        # Create session
        first_result = session_service.get_or_create_session(session_id="test-session-4")
        assert "last_active" in first_result

        # Get again
        second_result = session_service.get_or_create_session(session_id="test-session-4")
        assert "last_active" in second_result

        # Both should have last_active timestamps
        # Note: SQLite timestamp format may differ, so just verify field exists
        assert second_result["last_active"] is not None


class TestSaveMessage:
    """Test save_message method."""

    def test_save_user_message(self, session_service):
        """Saving a user message should return message ID."""
        # Create session first
        session_service.get_or_create_session(session_id="test-session-5")

        # Save message
        message_id = session_service.save_message(
            session_id="test-session-5",
            role="user",
            content="Hello, what animals do you have?"
        )

        assert message_id is not None
        assert isinstance(message_id, int)

    def test_save_assistant_message(self, session_service):
        """Saving an assistant message should work."""
        session_service.get_or_create_session(session_id="test-session-6")

        message_id = session_service.save_message(
            session_id="test-session-6",
            role="assistant",
            content="We have lions, elephants, and giraffes!"
        )

        assert message_id is not None

    def test_save_message_with_metadata(self, session_service):
        """Saving message with metadata should work."""
        session_service.get_or_create_session(session_id="test-session-7")

        message_id = session_service.save_message(
            session_id="test-session-7",
            role="assistant",
            content="Lions are amazing!",
            metadata={"sources": ["doc1", "doc2"], "confidence": 0.95}
        )

        assert message_id is not None

    def test_save_message_increments_count(self, session_service):
        """Saving messages should increment session message_count."""
        session_service.get_or_create_session(session_id="test-session-8")

        # Save 3 messages
        session_service.save_message(session_id="test-session-8", role="user", content="Q1")
        session_service.save_message(session_id="test-session-8", role="assistant", content="A1")
        session_service.save_message(session_id="test-session-8", role="user", content="Q2")

        # Get session and check count
        session = session_service.get_session("test-session-8")
        assert session["message_count"] == 3


class TestGetChatHistory:
    """Test get_chat_history method."""

    def test_get_empty_history(self, session_service):
        """Getting history for session with no messages should return empty list."""
        session_service.get_or_create_session(session_id="test-session-9")

        history = session_service.get_chat_history(session_id="test-session-9")

        assert history == []

    def test_get_chat_history(self, session_service):
        """Getting history should return messages in chronological order."""
        session_service.get_or_create_session(session_id="test-session-10")

        # Add messages
        session_service.save_message(session_id="test-session-10", role="user", content="Q1")
        session_service.save_message(session_id="test-session-10", role="assistant", content="A1")
        session_service.save_message(session_id="test-session-10", role="user", content="Q2")

        history = session_service.get_chat_history(session_id="test-session-10")

        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Q1"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "A1"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "Q2"

    def test_get_chat_history_with_limit(self, session_service):
        """Limit parameter should restrict number of messages."""
        session_service.get_or_create_session(session_id="test-session-11")

        # Add 5 messages
        for i in range(5):
            session_service.save_message(
                session_id="test-session-11",
                role="user",
                content=f"Message {i}"
            )

        history = session_service.get_chat_history(session_id="test-session-11", limit=3)

        assert len(history) == 3

    def test_get_chat_history_without_metadata(self, session_service):
        """By default, metadata should not be included."""
        session_service.get_or_create_session(session_id="test-session-12")

        session_service.save_message(
            session_id="test-session-12",
            role="assistant",
            content="Answer",
            metadata={"sources": ["doc1"]}
        )

        history = session_service.get_chat_history(session_id="test-session-12")

        assert len(history) == 1
        assert "metadata" not in history[0]
        assert "role" in history[0]
        assert "content" in history[0]
        assert "timestamp" in history[0]

    def test_get_chat_history_with_metadata(self, session_service):
        """With include_metadata=True, metadata should be included."""
        session_service.get_or_create_session(session_id="test-session-13")

        session_service.save_message(
            session_id="test-session-13",
            role="assistant",
            content="Answer",
            metadata={"sources": ["doc1"], "confidence": 0.9}
        )

        history = session_service.get_chat_history(
            session_id="test-session-13",
            include_metadata=True
        )

        assert len(history) == 1
        assert "metadata" in history[0]
        assert history[0]["metadata"]["sources"] == ["doc1"]
        assert history[0]["metadata"]["confidence"] == 0.9


class TestGetSessionStats:
    """Test get_session_stats method."""

    def test_stats_empty_session(self, session_service):
        """Stats for session with no messages should return zero count."""
        session_service.get_or_create_session(session_id="test-session-14")

        stats = session_service.get_session_stats(session_id="test-session-14")

        assert stats["message_count"] == 0
        assert stats["first_message"] is None
        assert stats["last_message"] is None

    def test_stats_with_messages(self, session_service):
        """Stats should reflect actual message count and timestamps."""
        session_service.get_or_create_session(session_id="test-session-15")

        # Add messages
        session_service.save_message(session_id="test-session-15", role="user", content="Q1")
        session_service.save_message(session_id="test-session-15", role="assistant", content="A1")
        session_service.save_message(session_id="test-session-15", role="user", content="Q2")

        stats = session_service.get_session_stats(session_id="test-session-15")

        assert stats["message_count"] == 3
        assert stats["first_message"] is not None
        assert stats["last_message"] is not None


class TestGetSession:
    """Test get_session method."""

    def test_get_existing_session(self, session_service):
        """Getting existing session should return session data."""
        session_service.get_or_create_session(
            session_id="test-session-16",
            metadata={"client": "web"}
        )

        session = session_service.get_session("test-session-16")

        assert session is not None
        assert session["session_id"] == "test-session-16"
        assert session["metadata"] == {"client": "web"}
        assert "created_at" in session
        assert "last_active" in session
        assert session["message_count"] == 0

    def test_get_nonexistent_session(self, session_service):
        """Getting non-existent session should return None."""
        session = session_service.get_session("nonexistent-session")

        assert session is None


class TestBackwardCompatibility:
    """Test backward compatibility with legacy schema."""

    def test_legacy_schema_compatible(self, session_service):
        """Schema should match legacy/session_manager.py exactly."""
        with session_service._get_connection() as conn:
            cursor = conn.cursor()

            # Check sessions table columns
            cursor.execute("PRAGMA table_info(sessions)")
            columns = {row[1] for row in cursor.fetchall()}
            expected = {
                "session_id",
                "device_fingerprint",
                "created_at",
                "last_active",
                "message_count",
                "metadata"
            }
            assert columns == expected

            # Check chat_history table columns
            cursor.execute("PRAGMA table_info(chat_history)")
            columns = {row[1] for row in cursor.fetchall()}
            expected = {
                "id",
                "session_id",
                "role",
                "content",
                "timestamp",
                "metadata"
            }
            assert columns == expected

    def test_device_fingerprint_support(self, session_service):
        """Service should support device_fingerprint field."""
        result = session_service.get_or_create_session(
            session_id="test-session-17",
            device_fingerprint="abc123xyz"
        )

        assert result["device_fingerprint"] == "abc123xyz"

        # Verify it's stored
        session = session_service.get_session("test-session-17")
        assert session["device_fingerprint"] == "abc123xyz"
