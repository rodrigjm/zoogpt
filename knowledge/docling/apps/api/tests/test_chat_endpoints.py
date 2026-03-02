"""
Tests for POST /chat and POST /chat/stream endpoints.
Per CONTRACT.md Part 4: Chat.
"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestChatEndpoint:
    """Test suite for POST /chat."""

    def test_chat_success(self):
        """Test successful chat request with valid session."""
        # First create a session
        session_response = client.post(
            "/session",
            json={"client": "web", "metadata": {}},
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        session_id = session_data["session_id"]

        # Now send a chat message
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "What do lemurs eat?",
                "mode": "rag",
                "metadata": {},
            },
        )

        assert chat_response.status_code == 200
        data = chat_response.json()

        # Verify response shape per CONTRACT.md
        assert "session_id" in data
        assert "message_id" in data
        assert "reply" in data
        assert "sources" in data
        assert "created_at" in data

        # Verify values
        assert data["session_id"] == session_id
        assert isinstance(data["message_id"], str)
        assert len(data["message_id"]) > 0
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0
        assert isinstance(data["sources"], list)
        assert isinstance(data["created_at"], str)

    def test_chat_session_not_found(self):
        """Test chat request with non-existent session returns 404."""
        chat_response = client.post(
            "/chat",
            json={
                "session_id": "non-existent-session-id",
                "message": "What do lemurs eat?",
            },
        )

        assert chat_response.status_code == 404
        data = chat_response.json()

        # Verify error shape per CONTRACT.md
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    def test_chat_minimal_request(self):
        """Test chat with minimal request (only required fields)."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Send minimal chat request
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "Hello!",
            },
        )

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert data["session_id"] == session_id
        assert data["reply"]  # Should have a reply

    def test_chat_with_metadata(self):
        """Test chat request with optional metadata."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Send chat with metadata
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "What animals live at the zoo?",
                "mode": "rag",
                "metadata": {"test": "value", "user_age": 8},
            },
        )

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert data["session_id"] == session_id

    def test_chat_empty_message(self):
        """Test that empty message is rejected by validation."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Try to send empty message
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "",
            },
        )

        # Should fail validation (422)
        assert chat_response.status_code == 422

    def test_chat_message_too_long(self):
        """Test that message exceeding max length is rejected."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Try to send message that's too long (> 1000 chars)
        long_message = "a" * 1001
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": long_message,
            },
        )

        # Should fail validation (422)
        assert chat_response.status_code == 422

    def test_chat_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        # Missing session_id
        response1 = client.post(
            "/chat",
            json={
                "message": "Hello",
            },
        )
        assert response1.status_code == 422

        # Missing message
        response2 = client.post(
            "/chat",
            json={
                "session_id": "some-id",
            },
        )
        assert response2.status_code == 422

    def test_chat_multiple_messages_same_session(self):
        """Test multiple chat messages in the same session."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Send first message
        response1 = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "What do lemurs eat?",
            },
        )
        assert response1.status_code == 200
        message_id_1 = response1.json()["message_id"]

        # Send second message
        response2 = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "How fast can a cheetah run?",
            },
        )
        assert response2.status_code == 200
        message_id_2 = response2.json()["message_id"]

        # Message IDs should be different
        assert message_id_1 != message_id_2
        # Session ID should be the same
        assert response2.json()["session_id"] == session_id


class TestChatStreamEndpoint:
    """Test suite for POST /chat/stream.

    Note: Full integration tests require OpenAI API key and LanceDB setup.
    These tests verify endpoint structure and error handling.
    """

    @pytest.mark.skip(reason="Requires OpenAI API key and LanceDB setup - run manually or in CI with secrets")
    def test_stream_success(self):
        """Test successful streaming chat request with valid session."""
        # First create a session
        session_response = client.post(
            "/session",
            json={"client": "web", "metadata": {}},
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        session_id = session_data["session_id"]

        # Now send a streaming chat message
        with client.stream(
            "POST",
            "/chat/stream",
            json={
                "session_id": session_id,
                "message": "What do lemurs eat?",
                "mode": "rag",
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Parse SSE events by reading lines from the stream
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])  # Strip "data: " prefix
                    events.append(data)

            # Verify we got at least text chunks and a done event
            assert len(events) > 0

            # Check that we have text chunks
            text_chunks = [e for e in events if e["type"] == "text"]
            assert len(text_chunks) > 0

            # Check for done event
            done_events = [e for e in events if e["type"] == "done"]
            assert len(done_events) == 1

            # Verify done event has sources and followup_questions
            done_event = done_events[0]
            assert "sources" in done_event
            assert "followup_questions" in done_event
            assert isinstance(done_event["sources"], list)
            assert isinstance(done_event["followup_questions"], list)

    def test_stream_session_not_found(self):
        """Test streaming chat request with non-existent session returns 404 JSON."""
        response = client.post(
            "/chat/stream",
            json={
                "session_id": "non-existent-session-id",
                "message": "What do lemurs eat?",
            },
        )

        # Should return 404 as regular JSON, not SSE
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        data = response.json()

        # Verify error shape per CONTRACT.md
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.skip(reason="Requires OpenAI API key and LanceDB setup - run manually or in CI with secrets")
    def test_stream_minimal_request(self):
        """Test streaming chat with minimal request (only required fields)."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Send minimal streaming request
        with client.stream(
            "POST",
            "/chat/stream",
            json={
                "session_id": session_id,
                "message": "Hello!",
            },
        ) as response:
            assert response.status_code == 200

            # Parse events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)

            # Should have at least text and done events
            assert any(e["type"] == "text" for e in events)
            assert any(e["type"] == "done" for e in events)

    def test_stream_empty_message(self):
        """Test that empty message is rejected by validation."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Try to send empty message
        response = client.post(
            "/chat/stream",
            json={
                "session_id": session_id,
                "message": "",
            },
        )

        # Should fail validation (422)
        assert response.status_code == 422

    @pytest.mark.skip(reason="Requires OpenAI API key and LanceDB setup - run manually or in CI with secrets")
    def test_stream_accumulates_full_response(self):
        """Test that streaming chunks form a coherent response."""
        # Create session
        session_response = client.post(
            "/session",
            json={"client": "web"},
        )
        session_id = session_response.json()["session_id"]

        # Send streaming request
        with client.stream(
            "POST",
            "/chat/stream",
            json={
                "session_id": session_id,
                "message": "What do elephants eat?",
            },
        ) as response:
            assert response.status_code == 200

            # Accumulate text chunks
            full_text = ""
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)
                    if data["type"] == "text" and data.get("content"):
                        full_text += data["content"]

            # Verify we got some text
            assert len(full_text) > 0

            # Verify done event exists
            done_events = [e for e in events if e["type"] == "done"]
            assert len(done_events) == 1
