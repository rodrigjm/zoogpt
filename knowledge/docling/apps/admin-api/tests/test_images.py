"""Tests for image management endpoints."""

import pytest
from pathlib import Path
from io import BytesIO
from PIL import Image


@pytest.fixture
def mock_image_bytes():
    """Create a mock image in memory."""
    img = Image.new('RGB', (200, 200), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


def test_list_animals_images(client, auth_headers):
    """Test listing all animal images."""
    response = client.get("/api/admin/images/animals", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "animals" in data
    assert isinstance(data["animals"], dict)


def test_get_animal_images(client, auth_headers):
    """Test getting a specific animal's images."""
    # Test with known animal
    response = client.get("/api/admin/images/animals/Lion", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Lion"
    assert "thumbnail" in data
    assert "images" in data
    assert "alt" in data


def test_get_animal_images_not_found(client, auth_headers):
    """Test getting images for non-existent animal."""
    response = client.get("/api/admin/images/animals/NonExistentAnimal", headers=auth_headers)
    assert response.status_code == 404


def test_update_animal_images(client, auth_headers):
    """Test updating animal image metadata."""
    update_data = {
        "alt": "Updated Lion Description"
    }
    response = client.put(
        "/api/admin/images/animals/Lion",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alt"] == "Updated Lion Description"


def test_upload_image_requires_auth(client):
    """Test that upload requires authentication."""
    response = client.post("/api/admin/images/animals/Lion/upload")
    assert response.status_code == 401


def test_sync_images(client, auth_headers):
    """Test syncing images with filesystem."""
    response = client.post("/api/admin/images/sync", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "added" in data
    assert "removed" in data
    assert "total_files" in data
