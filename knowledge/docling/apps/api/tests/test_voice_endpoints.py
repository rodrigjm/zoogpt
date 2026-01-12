"""
Integration tests for voice endpoints.
Tests POST /voice/stt per CONTRACT.md Part 4: Voice.
"""

import pytest
import io
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPostVoiceSTT:
    """Tests for POST /voice/stt endpoint."""

    def create_mock_audio_file(self, content: bytes = b"mock audio data") -> io.BytesIO:
        """Create a mock audio file for testing."""
        return io.BytesIO(content)

    def test_stt_success(self):
        """Successful STT request returns mock transcription."""
        # First create a session
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # Create mock audio file
        audio_file = self.create_mock_audio_file()

        # Send STT request
        response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == session_id
        assert "text" in data
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0

    def test_stt_response_shape(self):
        """Response should match CONTRACT.md shape exactly."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Create mock audio
        audio_file = self.create_mock_audio_file()

        # STT request
        response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.webm", audio_file, "audio/webm")}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have these fields per CONTRACT.md
        assert "session_id" in data
        assert "text" in data

    def test_stt_different_audio_formats(self):
        """Should accept common browser audio formats."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        formats = [
            ("test.wav", "audio/wav"),
            ("test.webm", "audio/webm"),
            ("test.mp3", "audio/mpeg"),
        ]

        for filename, mime_type in formats:
            audio_file = self.create_mock_audio_file()
            response = client.post(
                "/voice/stt",
                data={"session_id": session_id},
                files={"audio": (filename, audio_file, mime_type)}
            )
            assert response.status_code == 200, f"Failed for format {mime_type}"

    def test_stt_session_not_found(self):
        """Should return 404 if session doesn't exist."""
        audio_file = self.create_mock_audio_file()

        response = client.post(
            "/voice/stt",
            data={"session_id": "nonexistent-session-id"},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )

        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_NOT_FOUND"
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_stt_missing_audio_file(self):
        """Should return 400 if audio file is missing."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Send request without audio file
        response = client.post(
            "/voice/stt",
            data={"session_id": session_id}
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_stt_empty_audio_file(self):
        """Should return 400 if audio file is empty."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Create empty audio file
        empty_audio = self.create_mock_audio_file(content=b"")

        response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.wav", empty_audio, "audio/wav")}
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "EMPTY_AUDIO"

    def test_stt_missing_session_id(self):
        """Should return 422 if session_id is missing."""
        audio_file = self.create_mock_audio_file()

        response = client.post(
            "/voice/stt",
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )

        assert response.status_code == 422  # FastAPI validation error


class TestVoiceErrorHandling:
    """Tests for voice endpoint error handling per CONTRACT.md."""

    def test_404_error_shape(self):
        """404 errors should use standard error shape."""
        audio_file = io.BytesIO(b"test")

        response = client.post(
            "/voice/stt",
            data={"session_id": "missing-session"},
            files={"audio": ("test.wav", audio_file, "audio/wav")}
        )

        assert response.status_code == 404

        data = response.json()

        # Verify error structure per CONTRACT.md Part 4
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "details" in error

        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)
        assert isinstance(error["details"], dict)

    def test_400_error_shape(self):
        """400 errors should use standard error shape."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Send empty audio
        empty_audio = io.BytesIO(b"")

        response = client.post(
            "/voice/stt",
            data={"session_id": session_id},
            files={"audio": ("test.wav", empty_audio, "audio/wav")}
        )

        assert response.status_code == 400

        data = response.json()

        # Verify error structure per CONTRACT.md Part 4
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "details" in error


class TestPostVoiceTTS:
    """Tests for POST /voice/tts endpoint."""

    def test_tts_success(self):
        """Successful TTS request returns audio bytes."""
        # First create a session
        session_response = client.post("/session", json={"client": "web"})
        session_id = session_response.json()["session_id"]

        # Send TTS request
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "Hello, this is a test",
                "voice": "default"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

        # Verify we got audio bytes
        audio_bytes = response.content
        assert len(audio_bytes) > 0

        # Verify it's a valid WAV file (starts with RIFF header)
        assert audio_bytes[:4] == b"RIFF"
        assert audio_bytes[8:12] == b"WAVE"

    def test_tts_default_voice(self):
        """TTS with default voice parameter."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # TTS request with default voice (omitted)
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "Hello world"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_tts_custom_voice(self):
        """TTS with custom voice parameter."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # TTS request with custom voice
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "Hello world",
                "voice": "bella"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_tts_session_not_found(self):
        """Should return 404 if session doesn't exist."""
        response = client.post(
            "/voice/tts",
            json={
                "session_id": "nonexistent-session-id",
                "text": "Hello"
            }
        )

        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_NOT_FOUND"
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_tts_empty_text(self):
        """Should return 400 if text is empty."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Send request with empty text
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": ""
            }
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "EMPTY_TEXT"

    def test_tts_whitespace_only_text(self):
        """Should return 400 if text is whitespace only."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # Send request with whitespace only
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "   "
            }
        )

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "EMPTY_TEXT"

    def test_tts_missing_session_id(self):
        """Should return 422 if session_id is missing."""
        response = client.post(
            "/voice/tts",
            json={
                "text": "Hello world"
            }
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_tts_missing_text(self):
        """Should return 422 if text is missing."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id
            }
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_tts_audio_format(self):
        """Verify TTS returns valid WAV format per CONTRACT.md."""
        # Create session
        session_response = client.post("/session", json={})
        session_id = session_response.json()["session_id"]

        # TTS request
        response = client.post(
            "/voice/tts",
            json={
                "session_id": session_id,
                "text": "Testing audio format"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

        # Check for Content-Disposition header
        assert "content-disposition" in response.headers
        assert "speech.wav" in response.headers["content-disposition"]
