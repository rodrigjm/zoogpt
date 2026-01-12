# Zoocari - Project Overview

## Purpose
Zoocari is a **voice-first, kid-friendly zoo Q&A chatbot** for Leesburg Animal Park. It uses RAG (Retrieval-Augmented Generation) with LanceDB for accurate, hallucination-free responses about animals for children ages 6-12.

**Repository:** https://github.com/rodrigjm/zoogpt.git

## Tech Stack
### Backend (`apps/api/`)
- **Framework**: FastAPI (async Python)
- **Python**: 3.12+ (required for Kokoro)
- **Data Validation**: Pydantic v2, pydantic-settings
- **Vector DB**: LanceDB (RAG retrieval)
- **Session DB**: SQLite
- **TTS**: Kokoro (default), ElevenLabs (optional)
- **STT**: faster-whisper
- **LLM**: OpenAI API
- **Testing**: pytest, pytest-asyncio

### Frontend (`apps/web/`)
- **Framework**: React 18 + TypeScript
- **Build**: Vite 6
- **Styling**: Tailwind CSS (Leesburg brand colors)
- **State**: Zustand

## Project Structure
```
zoocari/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/  # session, chat, voice
│   │   │   ├── models/   # Pydantic models
│   │   │   └── services/ # RAG, TTS, STT
│   │   └── tests/
│   └── web/              # React frontend
│       └── src/
├── docs/
│   └── integration/
│       ├── CONTRACT.md   # API contracts (source of truth)
│       └── STATUS.md     # Task tracking, decisions
├── legacy/               # Original implementation (reference)
├── docker/               # Docker configs
├── data/
│   └── zoo_lancedb/      # Vector database
└── .venv/                # Python virtual environment
```

## Key Constraints
- Python 3.12+ required for Kokoro compatibility
- HTTPS required for browser microphone access in production
- LanceDB must be built before running chatbot
- Vector database stored in `data/zoo_lancedb/`

## Integration Contracts
- **CONTRACT.md**: Source of truth for API shapes
- **STATUS.md**: Task tracking, open questions, decisions
- Subagents collaborate through these shared artifacts only
