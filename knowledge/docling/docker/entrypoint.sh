#!/bin/bash
set -e

# Use LANCEDB_PATH env var or default
LANCEDB_DIR="${LANCEDB_PATH:-/app/data/zoo_lancedb}"

# Check if LanceDB data exists
if [ ! -d "$LANCEDB_DIR" ] || [ -z "$(ls -A $LANCEDB_DIR 2>/dev/null)" ]; then
    echo "=============================================="
    echo "LanceDB data not found. Building knowledge base..."
    echo "This may take 10-15 minutes on first run."
    echo "=============================================="

    # Check for required API key
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "ERROR: OPENAI_API_KEY is required to build knowledge base"
        exit 1
    fi

    # Run knowledge base builder
    python /app/zoo_build_knowledge.py

    echo "=============================================="
    echo "Knowledge base built successfully!"
    echo "=============================================="
else
    echo "LanceDB data found. Skipping knowledge base build."
fi

# Start the API server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
