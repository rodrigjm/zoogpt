# ============================================================
# Zoocari - Zoo Q&A Chatbot with Local Kokoro TTS
# ============================================================
# Python 3.12 required for Kokoro TTS compatibility
# Includes espeak-ng for phoneme generation
# ============================================================

FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Hugging Face cache directory
    HF_HOME=/app/.cache/huggingface \
    # Streamlit configuration
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# ============================================================
# Stage 1: Build dependencies
# ============================================================
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Runtime image
# ============================================================
FROM base AS runtime

# Install runtime dependencies including espeak-ng for Kokoro TTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libespeak-ng1 \
    curl \
    # Audio processing
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create cache directories with proper permissions
RUN mkdir -p /app/.cache/huggingface /app/.cache/torch \
    && chmod -R 777 /app/.cache

# Copy application code
COPY zoo_chat.py .
COPY tts_kokoro.py .
COPY zoo_build_knowledge.py .
COPY zoo_sources.py .
COPY zoocari_mascot_web.png .
COPY entrypoint.sh .
COPY utils/ ./utils/
COPY static/ ./static/

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# ============================================================
# Stage 3: Pre-download models (optional, for faster cold starts)
# ============================================================
FROM runtime AS with-models

# Pre-download spaCy model (required for Kokoro)
RUN python -m spacy download en_core_web_sm

# Pre-download Kokoro model (this caches the model in the image)
# Comment out if you prefer to download on first run
RUN python -c "\
from kokoro import KPipeline; \
print('Pre-loading Kokoro model...'); \
p = KPipeline(lang_code='a'); \
print('Kokoro model cached successfully!')" || echo "Kokoro pre-load skipped (will download on first use)"

# Pre-download Faster-Whisper model for local STT (Phase 1 Voice Upgrade)
# Uses 'base' model with int8 quantization for optimal speed/size balance
RUN python -c "\
from faster_whisper import WhisperModel; \
print('Pre-loading Faster-Whisper model (base, int8)...'); \
m = WhisperModel('base', device='cpu', compute_type='int8'); \
print('Faster-Whisper model cached successfully!')" || echo "Faster-Whisper pre-load skipped (will download on first use)"

# ============================================================
# Final stage
# ============================================================
FROM with-models AS final

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
