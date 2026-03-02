"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import settings
from auth import create_access_token


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token."""
    token = create_access_token(username=settings.admin_username)
    return {"Authorization": f"Bearer {token.access_token}"}
