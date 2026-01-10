# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zoocari is a voice-first, kid-friendly zoo Q&A chatbot for Leesburg Animal Park. It uses RAG (Retrieval-Augmented Generation) with a LanceDB vector database to provide accurate, hallucination-free responses about animals for children ages 6-12.

**Repository:** https://github.com/rodrigjm/zoogpt.git

## Build & Run Commands

### Prerequisites
- Python 3.12+ (required for Kokoro TTS compatibility)
- espeak-ng system dependency: `brew install espeak-ng` (macOS) or `apt-get install espeak-ng` (Linux)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy .env.example to .env, add OPENAI_API_KEY)
cp .env.example .env

# Build knowledge base (first time only, ~5-10 minutes)
python zoo_build_knowledge.py

# Run chatbot
streamlit run zoo_chat.py
```

### Docker Deployment
```bash
docker-compose up --build
# Access at: http://localhost:8501
```

### Verification Commands
```bash
# Check Faster-Whisper STT availability
python -c "from faster_whisper import WhisperModel; print('Faster-Whisper available')"

# Check Kokoro TTS availability
python -c "from tts_kokoro import is_kokoro_available; print(is_kokoro_available())"

# Verify vector database row count
python -c "import lancedb; db = lancedb.connect('data/zoo_lancedb'); print(db.open_table('animals').count_rows())"
```

## Architecture

### Main Files
- `zoo_chat.py` - Main Streamlit chatbot application with voice/text input
- `zoo_build_knowledge.py` - Knowledge base builder using Docling + LanceDB
- `zoo_sources.py` - Curated list of trusted animal education URLs
- `tts_kokoro.py` - Local Kokoro TTS inference with cloud fallback chain
- `utils/text.py` - Markdown stripping and HTML sanitization

### Data Flow

**Chat Pipeline:**
```
User Input (voice/text) → STT (Faster-Whisper local / OpenAI fallback) → Vector Search (LanceDB) → LLM (GPT-4o-mini) → TTS → Audio Response
```

**Knowledge Build Pipeline:**
```
Trusted URLs → Docling Extraction → HybridChunker → OpenAI Embeddings → LanceDB Storage
```

### STT Fallback Chain
1. **Faster-Whisper** (local, ~300ms) - Primary, free, offline capable
2. **OpenAI Whisper API** (cloud, ~800ms) - Fallback

### TTS Fallback Chain
1. **Kokoro** (local, 50-200ms) - Primary, requires espeak-ng
2. **ElevenLabs** (cloud, 500-2000ms) - First fallback
3. **OpenAI TTS** (cloud, 300-800ms) - Final fallback

### Key Environment Variables
- `OPENAI_API_KEY` - Required for chat, embeddings, and STT fallback
- `ELEVENLABS_API_KEY` - Optional, for cloud TTS fallback
- `TTS_PROVIDER` - kokoro, elevenlabs, or openai
- `TTS_VOICE` - Voice ID (default: af_heart for Kokoro)

## Common Tasks

- **Add new animal sources:** Edit `zoo_sources.py`, then run `python zoo_build_knowledge.py`
- **Modify Zoocari persona:** Edit `ZUCARI_SYSTEM_PROMPT` in `zoo_chat.py`
- **Change UI styling:** Edit `static/zoocari.css`
- **Switch TTS provider:** Set `TTS_PROVIDER` in `.env`

## Important Constraints

- Python 3.12+ required for Kokoro compatibility
- HTTPS required for browser microphone access in production
- LanceDB must be built before running chatbot
- Vector database stored in `data/zoo_lancedb/`
