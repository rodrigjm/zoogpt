"""
Tests for feedback router endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


def test_feedback_stats_endpoint(mock_auth, test_client):
    """Test GET /api/admin/feedback/stats endpoint."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        # Mock database responses
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock overall stats
        mock_cursor.fetchone.return_value = {
            "total": 100,
            "thumbs_up": 70,
            "thumbs_down": 20,
            "surveys": 10,
            "flagged": 5,
        }

        # Mock daily trends
        mock_cursor.fetchall.return_value = [
            {"date": "2026-01-25", "total": 50, "thumbs_up": 35, "thumbs_down": 10, "surveys": 5},
            {"date": "2026-01-24", "total": 50, "thumbs_up": 35, "thumbs_down": 10, "surveys": 5},
        ]

        response = test_client.get("/api/admin/feedback/stats?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["thumbs_up"] == 70
        assert data["thumbs_down"] == 20
        assert data["positive_rate"] == 0.7778
        assert len(data["daily_trends"]) == 2


def test_feedback_list_endpoint(mock_auth, test_client):
    """Test GET /api/admin/feedback/list endpoint."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock count
        mock_cursor.fetchone.side_effect = [
            [25],  # total count
            {"content": "Test message"},  # message content
        ]

        # Mock feedback items
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "session_id": "test-session",
                "message_id": "123",
                "feedback_type": "thumbs_up",
                "comment": None,
                "flagged": 0,
                "reviewed_at": None,
                "created_at": "2026-01-25T10:00:00",
            }
        ]

        response = test_client.get("/api/admin/feedback/list?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 1
        assert data["items"][0]["feedback_type"] == "thumbs_up"


def test_feedback_detail_endpoint(mock_auth, test_client):
    """Test GET /api/admin/feedback/{id} endpoint."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock feedback item
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "session_id": "test-session",
            "message_id": "123",
            "feedback_type": "thumbs_down",
            "comment": "Not helpful",
            "flagged": 1,
            "reviewed_at": None,
            "created_at": "2026-01-25T10:00:00",
        }

        # Mock chat context
        mock_cursor.fetchall.return_value = [
            {"id": "123", "role": "user", "content": "What is a lion?", "timestamp": "2026-01-25T10:00:00"},
            {"id": "124", "role": "assistant", "content": "A lion is...", "timestamp": "2026-01-25T10:00:01"},
        ]

        response = test_client.get("/api/admin/feedback/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["flagged"] is True
        assert len(data["chat_context"]) == 2


def test_update_flagged_status(mock_auth, test_client):
    """Test PATCH /api/admin/feedback/{id}/flag endpoint."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = test_client.patch(
            "/api/admin/feedback/1/flag",
            json={"flagged": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["flagged"] is True


def test_mark_as_reviewed(mock_auth, test_client):
    """Test PATCH /api/admin/feedback/{id}/reviewed endpoint."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        response = test_client.patch(
            "/api/admin/feedback/1/reviewed",
            json={"reviewed": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["reviewed_at"] is not None


def test_feedback_not_found(mock_auth, test_client):
    """Test 404 response for non-existent feedback."""
    with patch("routers.feedback.get_db_connection") as mock_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        response = test_client.get("/api/admin/feedback/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
