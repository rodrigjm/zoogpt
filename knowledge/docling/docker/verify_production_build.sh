#!/bin/bash
# Production Dockerfile Build Verification Script
# Phase 6.1 - Verify docker/Dockerfile.api builds successfully

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Production Docker Build Verification"
echo "=========================================="
echo ""

# Step 1: Check prerequisites
echo "[1/6] Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed"
    exit 1
fi
echo "✓ Docker installed: $(docker --version)"
echo ""

# Step 2: Check if frontend is built
echo "[2/6] Checking frontend build..."
FRONTEND_DIST="$PROJECT_ROOT/apps/web/dist"
if [ ! -d "$FRONTEND_DIST" ] || [ ! -f "$FRONTEND_DIST/index.html" ]; then
    echo "WARNING: Frontend not built. Building now..."
    cd "$PROJECT_ROOT/apps/web"
    npm run build
    cd "$PROJECT_ROOT"
fi
echo "✓ Frontend built at: $FRONTEND_DIST"
echo ""

# Step 3: Build production image
echo "[3/6] Building production image (this may take 5-10 minutes)..."
cd "$PROJECT_ROOT"
docker build -f docker/Dockerfile.api -t zoocari-api:prod-test .
echo "✓ Image built successfully"
echo ""

# Step 4: Check image size
echo "[4/6] Checking image size..."
IMAGE_SIZE=$(docker image inspect zoocari-api:prod-test --format='{{.Size}}' | awk '{print $1/1024/1024/1024 " GB"}')
echo "✓ Image size: $IMAGE_SIZE"
echo ""

# Step 5: Test container startup
echo "[5/6] Testing container startup (will auto-stop after 10s)..."
docker run -d \
    --name zoocari-api-verify \
    -p 8001:8000 \
    -e OPENAI_API_KEY=dummy_key_for_test \
    -e CORS_ORIGINS=http://localhost:5173 \
    zoocari-api:prod-test

# Wait for startup
sleep 5

# Check if container is running
if ! docker ps | grep -q zoocari-api-verify; then
    echo "ERROR: Container failed to start"
    docker logs zoocari-api-verify
    docker rm zoocari-api-verify
    exit 1
fi
echo "✓ Container started successfully"
echo ""

# Step 6: Test health endpoint
echo "[6/6] Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8001/health || echo "FAILED")
if [[ "$HEALTH_RESPONSE" == *"\"ok\""* ]]; then
    echo "✓ Health check passed: $HEALTH_RESPONSE"
else
    echo "ERROR: Health check failed: $HEALTH_RESPONSE"
    docker logs zoocari-api-verify
    docker stop zoocari-api-verify
    docker rm zoocari-api-verify
    exit 1
fi
echo ""

# Cleanup
echo "Cleaning up test container..."
docker stop zoocari-api-verify > /dev/null
docker rm zoocari-api-verify > /dev/null
echo "✓ Cleanup complete"
echo ""

echo "=========================================="
echo "ALL VERIFICATION CHECKS PASSED ✓"
echo "=========================================="
echo ""
echo "Production image ready: zoocari-api:prod-test"
echo "To run: docker run -d -p 8000:8000 -v \$(pwd)/data:/app/data -e OPENAI_API_KEY=... zoocari-api:prod-test"
echo ""
