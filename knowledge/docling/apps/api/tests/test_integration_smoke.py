"""
Integration smoke tests for Phase 1 API endpoints.
Tests end-to-end user flows across all endpoints per CONTRACT.md Part 4.

Run these tests separately with:
    pytest tests/test_integration_smoke.py -v
    pytest -m smoke
"""

import pytest
import io
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Pytest marker for smoke tests
pytestmark = pytest.mark.smoke


class TestHealthSmoke:
    """Smoke test for health endpoint."""

    def test_health_check(self):
        """GET /health returns {"ok": true}."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestSessionFlowSmoke:
    """Smoke test for session creation and retrieval flow."""

    def test_create_and_retrieve_session(self):
        """Full session flow: create → retrieve → verify."""
        # Step 1: Create session
        create_response = client.post(
            "/session",
            json={"client": "web", "metadata": {"test": "smoke"}}
        )
        assert create_response.status_code == 200

        create_data = create_response.json()
        assert "session_id" in create_data
        assert "created_at" in create_data

        session_id = create_data["session_id"]

        # Verify created_at is valid ISO-8601
        datetime.fromisoformat(create_data["created_at"].replace("Z", "+00:00"))

        # Step 2: Retrieve session
        get_response = client.get(f"/session/{session_id}")
        assert get_response.status_code == 200

        get_data = get_response.json()
        assert get_data["session_id"] == session_id
        assert "created_at" in get_data
        assert get_data["metadata"] == {"test": "smoke"}

        # Step 3: Verify shape matches CONTRACT.md
        assert set(create_data.keys()) == {"session_id", "created_at"}
        assert "session_id" in get_data
        assert "created_at" in get_data
        assert "metadata" in get_data


class TestChatFlowSmoke:
    """Smoke test for chat flow."""

    def test_session_to_chat_flow(self):
        """Full chat flow: create session → send message → verify response."""
        # Step 1: Create session
        session_response = client.post(
            "/session",
            json={"client": "web"}
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Step 2: Send chat message
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "What do lemurs eat?",
                "mode": "rag"
            }
        )
        assert chat_response.status_code == 200

        # Step 3: Verify response shape per CONTRACT.md
        chat_data = chat_response.json()
        assert chat_data["session_id"] == session_id
        assert "message_id" in chat_data
        assert "reply" in chat_data
        assert "sources" in chat_data
        assert "created_at" in chat_data

        # Verify types
        assert isinstance(chat_data["message_id"], str)
        assert len(chat_data["message_id"]) > 0
        assert isinstance(chat_data["reply"], str)
        assert len(chat_data["reply"]) > 0
        assert isinstance(chat_data["sources"], list)

        # Verify created_at is valid
        datetime.fromisoformat(chat_data["created_at"].replace("Z", "+00:00"))

    def test_multiple_chat_messages_flow(self):
        """Test conversation flow with multiple messages."""
        # Create session
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # Send multiple messages
        messages = [
            "What animals live at the zoo?",
            "Tell me about lemurs.",
            "How fast can a cheetah run?"
        ]

        message_ids = []
        for message in messages:
            response = client.post(
                "/chat",
                json={"session_id": session_id, "message": message}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            message_ids.append(data["message_id"])

        # All message IDs should be unique
        assert len(message_ids) == len(set(message_ids))


class TestVoiceSTTFlowSmoke:
    """Smoke test for voice STT flow."""

    def create_mock_audio(self) -> io.BytesIO:
        """Create mock audio file for testing."""
        return io.BytesIO(b"mock audio content for testing")

    def test_session_to_stt_flow(self):
        """Full STT flow: create session → send audio → get transcription."""
        # Step 1: Create session
        session_response = client.post("/session", json={"client": "web"})
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Step 2: Send audio for transcription
        audio_file = self.create_mock_audio()
        stt_response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )
        assert stt_response.status_code == 200

        # Step 3: Verify response shape per CONTRACT.md
        stt_data = stt_response.json()
        assert stt_data["session_id"] == session_id
        assert "text" in stt_data
        assert isinstance(stt_data["text"], str)
        assert len(stt_data["text"]) > 0


class TestVoiceTTSFlowSmoke:
    """Smoke test for voice TTS flow."""

    def test_session_to_tts_flow(self):
        """Full TTS flow: create session → send text → get audio."""
        # Step 1: Create session
        session_response = client.post("/session", json={"client": "web"})
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Step 2: Request TTS
        tts_response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "Hello, welcome to the zoo!",
                "voice": "default"
            }
        )
        assert tts_response.status_code == 200

        # Step 3: Verify response is audio per CONTRACT.md
        assert tts_response.headers["content-type"] == "audio/wav"
        audio_bytes = tts_response.content
        assert len(audio_bytes) > 0

        # Verify it's a valid WAV file
        assert audio_bytes[:4] == b"RIFF"
        assert audio_bytes[8:12] == b"WAVE"


class TestFullVoiceAssistantFlowSmoke:
    """Smoke test for complete voice assistant flow."""

    def create_mock_audio(self) -> io.BytesIO:
        """Create mock audio file for testing."""
        return io.BytesIO(b"mock audio data")

    def test_complete_voice_assistant_flow(self):
        """
        Simulated voice assistant flow:
        1. Create session
        2. User speaks (STT)
        3. Chat responds
        4. Response spoken back (TTS)
        """
        # Step 1: Create session for voice interaction
        session_response = client.post(
            "/session",
            json={"client": "mobile", "metadata": {"interface": "voice"}}
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Step 2: User speaks - convert speech to text
        audio_file = self.create_mock_audio()
        stt_response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("voice.webm", audio_file, "audio/webm")}
        )
        assert stt_response.status_code == 200
        transcribed_text = stt_response.json()["text"]
        assert len(transcribed_text) > 0

        # Step 3: Process chat message (using mock text for determinism)
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "What animals are at the zoo?",
                "mode": "rag"
            }
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["session_id"] == session_id
        reply_text = chat_data["reply"]
        assert len(reply_text) > 0

        # Step 4: Convert reply to speech
        tts_response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": reply_text[:100],  # Use first 100 chars to keep it fast
                "voice": "default"
            }
        )
        assert tts_response.status_code == 200
        assert tts_response.headers["content-type"] == "audio/wav"
        assert len(tts_response.content) > 0

        # Verify the entire flow completed successfully
        # Session persisted across all operations


class TestChatWithTTSFlowSmoke:
    """Smoke test for chat-then-TTS flow (text interface with audio response)."""

    def test_text_chat_with_audio_response(self):
        """Flow: create session → chat → TTS the reply."""
        # Step 1: Create session
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # Step 2: User types a question
        chat_response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": "Where do elephants live?"
            }
        )
        assert chat_response.status_code == 200
        reply_text = chat_response.json()["reply"]

        # Step 3: Convert reply to audio for playback
        tts_response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": reply_text[:50]  # Keep short for speed
            }
        )
        assert tts_response.status_code == 200
        assert tts_response.headers["content-type"] == "audio/wav"
        assert len(tts_response.content) > 0


class TestErrorHandlingSmoke:
    """Smoke tests for error cases per CONTRACT.md Part 4."""

    def test_session_not_found_errors(self):
        """Verify 404 error shape for non-existent sessions."""
        fake_session_id = "nonexistent-session-id-12345"

        # Test GET /session/{id}
        response1 = client.get(f"/session/{fake_session_id}")
        assert response1.status_code == 404
        data1 = response1.json()
        assert "error" in data1
        assert data1["error"]["code"] == "SESSION_NOT_FOUND"
        assert "message" in data1["error"]
        assert "details" in data1["error"]

        # Test POST /chat
        response2 = client.post(
            "/chat",
            json={"session_id": fake_session_id, "message": "Hello"}
        )
        assert response2.status_code == 404
        data2 = response2.json()
        assert "error" in data2
        assert data2["error"]["code"] == "SESSION_NOT_FOUND"

        # Test POST /voice/stt
        audio_file = io.BytesIO(b"test")
        response3 = client.post(
            "/voice/stt",
            data={"session_id": fake_session_id},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )
        assert response3.status_code == 404
        data3 = response3.json()
        assert "error" in data3
        assert data3["error"]["code"] == "SESSION_NOT_FOUND"

        # Test POST /voice/tts
        response4 = client.post(
            "/voice/tts",
            json={"session_id": fake_session_id, "text": "Hello"}
        )
        assert response4.status_code == 404
        data4 = response4.json()
        assert "error" in data4
        assert data4["error"]["code"] == "SESSION_NOT_FOUND"

    def test_validation_errors(self):
        """Test validation errors (422) for invalid requests."""
        # Create valid session first
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Empty message in chat
        response1 = client.post(
            "/chat",
            json={"session_id": session_id, "message": ""}
        )
        assert response1.status_code == 422

        # Message too long
        response2 = client.post(
            "/chat",
            json={"session_id": session_id, "message": "x" * 1001}
        )
        assert response2.status_code == 422

        # Missing required field
        response3 = client.post(
            "/chat",
            json={"message": "Hello"}
        )
        assert response3.status_code == 422

    def test_error_shape_consistency(self):
        """Verify all errors follow CONTRACT.md error shape."""
        # Trigger a 404 error
        response = client.get("/session/invalid-id")
        assert response.status_code == 404

        data = response.json()
        # Verify structure per CONTRACT.md Part 4
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "details" in error

        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)
        assert isinstance(error["details"], dict)


class TestCrossEndpointIntegrationSmoke:
    """Test integration across multiple endpoint types."""

    def test_session_reuse_across_endpoints(self):
        """Verify same session works across all endpoint types."""
        # Create session once
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # Use session for chat
        chat_response = client.post(
            "/chat",
            json={"session_id": session_id, "message": "Hello"}
        )
        assert chat_response.status_code == 200
        assert chat_response.json()["session_id"] == session_id

        # Use same session for STT
        audio_file = io.BytesIO(b"audio")
        stt_response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )
        assert stt_response.status_code == 200
        assert stt_response.json()["session_id"] == session_id

        # Use same session for TTS
        tts_response = client.post(
            "/voice/tts",
            json={"session_id": session_id, "text": "Test"}
        )
        assert tts_response.status_code == 200

        # Verify session still exists
        get_response = client.get(f"/session/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["session_id"] == session_id

    def test_rapid_sequential_requests(self):
        """Test multiple rapid requests in sequence."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Rapid-fire 5 chat messages
        for i in range(5):
            response = client.post(
                "/chat",
                json={
                    "session_id": session_id,
                    "message": f"Question {i + 1}"
                }
            )
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id

    def test_mixed_operation_sequence(self):
        """Test realistic mixed sequence of operations."""
        # Create session
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # 1. Check health
        health = client.get("/health")
        assert health.status_code == 200

        # 2. Chat message
        chat1 = client.post(
            "/chat",
            json={"session_id": session_id, "message": "What animals?"}
        )
        assert chat1.status_code == 200

        # 3. Get session info
        session_get = client.get(f"/session/{session_id}")
        assert session_get.status_code == 200

        # 4. TTS request
        tts = client.post(
            "/voice/tts",
            json={"session_id": session_id, "text": "Response"}
        )
        assert tts.status_code == 200

        # 5. Another chat
        chat2 = client.post(
            "/chat",
            json={"session_id": session_id, "message": "Tell me more"}
        )
        assert chat2.status_code == 200

        # All operations succeeded with same session
