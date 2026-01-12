"""
Integration tests for session endpoints.
Tests POST /session and GET /session/{session_id} per CONTRACT.md Part 4.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app

client = TestClient(app)


class TestPostSession:
    """Tests for POST /session endpoint."""

    def test_create_session_minimal(self):
        """Create session with minimal data."""
        response = client.post("/session", json={})
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "created_at" in data
        assert len(data["session_id"]) > 0

        # Verify created_at is valid ISO-8601
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    def test_create_session_with_client(self):
        """Create session with client specified."""
        response = client.post("/session", json={"client": "mobile"})
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "created_at" in data

    def test_create_session_with_metadata(self):
        """Create session with metadata."""
        response = client.post(
            "/session",
            json={
                "client": "web",
                "metadata": {"version": "1.0", "feature_flag": "enabled"}
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "created_at" in data

    def test_create_session_unique_ids(self):
        """Each session should get a unique ID."""
        response1 = client.post("/session", json={})
        response2 = client.post("/session", json={})

        assert response1.status_code == 200
        assert response2.status_code == 200

        id1 = response1.json()["session_id"]
        id2 = response2.json()["session_id"]

        assert id1 != id2

    def test_create_session_response_shape(self):
        """Response should match CONTRACT.md shape exactly."""
        response = client.post("/session", json={"client": "web"})
        assert response.status_code == 200

        data = response.json()

        # Should have exactly these fields per CONTRACT.md
        assert set(data.keys()) == {"session_id", "created_at"}


class TestGetSession:
    """Tests for GET /session/{session_id} endpoint."""

    def test_get_existing_session(self):
        """Get a session that exists."""
        # First create a session
        create_response = client.post(
            "/session",
            json={"client": "web", "metadata": {"test": "value"}}
        )
        session_id = create_response.json()["session_id"]

        # Then fetch it
        get_response = client.get(f"/session/{session_id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["session_id"] == session_id
        assert "created_at" in data
        assert "metadata" in data
        assert data["metadata"]["test"] == "value"

    def test_get_nonexistent_session(self):
        """Get a session that doesn't exist should return 404."""
        response = client.get("/session/nonexistent-id-12345")
        assert response.status_code == 404

        data = response.json()

        # Should match CONTRACT.md error shape
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    def test_get_session_response_shape(self):
        """Response should match CONTRACT.md shape exactly."""
        # Create session
        create_response = client.post("/session", json={"client": "web"})
        session_id = create_response.json()["session_id"]

        # Get session
        get_response = client.get(f"/session/{session_id}")
        assert get_response.status_code == 200

        data = get_response.json()

        # Should have these fields per CONTRACT.md
        assert "session_id" in data
        assert "created_at" in data
        assert "metadata" in data

    def test_get_session_without_metadata(self):
        """Session created without metadata should return empty metadata."""
        # Create session without metadata
        create_response = client.post("/session", json={"client": "web"})
        session_id = create_response.json()["session_id"]

        # Get session
        get_response = client.get(f"/session/{session_id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["metadata"] == {}


class TestSessionErrorHandling:
    """Tests for error handling per CONTRACT.md."""

    def test_404_error_shape(self):
        """404 errors should use standard error shape."""
        response = client.get("/session/missing-123")
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
