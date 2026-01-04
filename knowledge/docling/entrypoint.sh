#!/bin/bash
set -e

DB_PATH="data/zoo_lancedb"

# Check if vector database exists
if [ ! -d "$DB_PATH" ] || [ -z "$(ls -A $DB_PATH 2>/dev/null)" ]; then
    echo "=================================================="
    echo "Vector database not found. Building knowledge base..."
    echo "=================================================="
    python zoo_build_knowledge.py
    echo ""
    echo "Knowledge base built successfully!"
    echo ""
else
    echo "Vector database found at $DB_PATH - skipping build"
fi

# Start the Streamlit app
echo "Starting Zoocari chatbot..."
exec streamlit run zoo_chat.py --server.port=8501 --server.address=0.0.0.0
