"""
Tests for WebSocket TTS endpoint.

Contract (matches frontend):
- Request: {"session_id": "...", "text": "...", "voice": "..."}
- Audio: {"type": "audio", "data": "<base64>", "index": n}
- Done: {"type": "done", "chunks": n}
- Error: {"type": "error", "data": "<message>"}
"""

import pytest
from fastapi.testclient import TestClient
import base64

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_tts_websocket_connection(client):
    """Test WebSocket connection can be established and returns audio."""
    with client.websocket_connect("/voice/tts/ws") as websocket:
        # Send a simple TTS request (uses Kokoro-FastAPI sidecar by default)
        websocket.send_json({
            "text": "Hello world",
            "voice": "af_heart",
            "speed": 1.0
            # use_streaming defaults to True (uses Kokoro-FastAPI sidecar)
        })

        # Receive messages until done
        chunks_received = 0
        while True:
            message = websocket.receive_json()

            if message.get("type") == "audio":
                # Verify base64-encoded audio
                assert "data" in message, "Audio message should have data field"
                assert "index" in message, "Audio message should have index field"
                # Verify it's valid base64
                audio_bytes = base64.b64decode(message["data"])
                assert len(audio_bytes) > 0, "Audio data should not be empty"
                chunks_received += 1

            elif message.get("type") == "done":
                # Completion message
                assert message.get("chunks") == chunks_received
                break

            elif message.get("type") == "error":
                pytest.fail(f"TTS error: {message.get('data')}")
                break

        # Should have received at least one audio chunk
        assert chunks_received > 0, "Should receive at least one audio chunk"


def test_tts_websocket_empty_text(client):
    """Test WebSocket handles empty text gracefully."""
    with client.websocket_connect("/voice/tts/ws") as websocket:
        # Send empty text
        websocket.send_json({
            "text": "",
            "voice": "af_heart"
        })

        # Should receive error message
        message = websocket.receive_json()
        assert message.get("type") == "error"
        assert "required" in message.get("data", "").lower()


def test_tts_websocket_multiple_requests(client):
    """Test WebSocket can handle multiple requests in sequence."""
    with client.websocket_connect("/voice/tts/ws") as websocket:
        for i in range(2):
            # Send request (uses Kokoro-FastAPI sidecar by default)
            websocket.send_json({
                "text": f"Test {i}",
                "voice": "af_heart"
            })

            # Wait for completion
            while True:
                message = websocket.receive_json()
                if message.get("type") in ("done", "error"):
                    break
