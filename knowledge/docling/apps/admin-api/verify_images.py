#!/usr/bin/env python3
"""
Quick verification script for image management endpoints.
Run this after starting the admin-api server.
"""

import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost:8502"
USERNAME = "admin"
PASSWORD = "your_password"  # Set via env


def get_token():
    """Get JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        auth=(USERNAME, PASSWORD)
    )
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    return response.json()["access_token"]


def verify_endpoints(token):
    """Test all image endpoints."""
    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: List all animals
    print("1. Testing GET /api/admin/images/animals")
    response = requests.get(f"{BASE_URL}/api/admin/images/animals", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Animals count: {len(data.get('animals', {}))}")
    else:
        print(f"   Error: {response.text}")

    # Test 2: Get specific animal
    print("\n2. Testing GET /api/admin/images/animals/Lion")
    response = requests.get(f"{BASE_URL}/api/admin/images/animals/Lion", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Name: {data.get('name')}")
        print(f"   Images: {len(data.get('images', []))}")
        print(f"   Thumbnail: {data.get('thumbnail')}")
    else:
        print(f"   Error: {response.text}")

    # Test 3: Sync images
    print("\n3. Testing POST /api/admin/images/sync")
    response = requests.post(f"{BASE_URL}/api/admin/images/sync", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total files: {data.get('total_files')}")
        print(f"   Added: {len(data.get('added', []))}")
        print(f"   Removed: {len(data.get('removed', []))}")
    else:
        print(f"   Error: {response.text}")


if __name__ == "__main__":
    print("Image Management Endpoints Verification")
    print("=" * 50)

    try:
        token = get_token()
        print("Authentication successful\n")
        verify_endpoints(token)
        print("\n" + "=" * 50)
        print("Verification complete!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
