#!/bin/bash
# ============================================================
# Zoocari Entrypoint Script
# ============================================================
# Initializes vector database and optionally warms up Kokoro TTS
# ============================================================

set -e

DB_PATH="data/zoo_lancedb"
WARMUP_TTS="${WARMUP_TTS:-true}"

echo "============================================================"
echo "🐘 ZOOCARI - Zoo Q&A Chatbot with Local TTS"
echo "============================================================"
echo ""

# Step 1: Check/build vector database
if [ ! -d "$DB_PATH" ] || [ -z "$(ls -A $DB_PATH 2>/dev/null)" ]; then
    echo "📚 Vector database not found. Building knowledge base..."
    echo "------------------------------------------------------------"
    python zoo_build_knowledge.py
    echo ""
    echo "✅ Knowledge base built successfully!"
    echo ""
else
    echo "✅ Vector database found at $DB_PATH"
fi

# Step 2: Warm up Kokoro TTS (optional, reduces first-request latency)
if [ "$WARMUP_TTS" = "true" ]; then
    echo ""
    echo "🔊 Warming up Kokoro TTS pipeline..."
    echo "------------------------------------------------------------"
    python -c "
import sys
try:
    from tts_kokoro import get_kokoro_pipeline, is_kokoro_available
    pipeline = get_kokoro_pipeline()
    if pipeline:
        # Generate a short test phrase to fully initialize
        for _, _, audio in pipeline('Hello!', voice='af_heart'):
            pass
        print('✅ Kokoro TTS warmed up and ready!')
    else:
        print('⚠️  Kokoro TTS not available, will use cloud fallback')
except Exception as e:
    print(f'⚠️  Kokoro warmup failed: {e}')
    print('   Will use ElevenLabs/OpenAI TTS fallback')
" || echo "⚠️  TTS warmup skipped"
fi

echo ""
echo "------------------------------------------------------------"
echo "🚀 Starting Zoocari chatbot on port 8501..."
echo "------------------------------------------------------------"
echo ""

# Step 3: Start Streamlit
exec streamlit run zoo_chat.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
