# Zoocari API - Project Overview

## Purpose
Zoocari is a **voice-first, kid-friendly zoo Q&A chatbot backend** for Leesburg Animal Park. It uses RAG (Retrieval-Augmented Generation) with LanceDB for accurate, hallucination-free responses about animals for children ages 6-12.

## Tech Stack
- **Framework**: FastAPI (async Python web framework)
- **Python**: 3.12+
- **Data Validation**: Pydantic v2 with pydantic-settings
- **Database**: LanceDB (vector database for RAG), SQLite (sessions)
- **TTS**: Kokoro (default), ElevenLabs (optional)
- **STT**: faster-whisper
- **LLM**: OpenAI API
- **Testing**: pytest, pytest-asyncio

## Project Structure
```
apps/api/
├── app/
│   ├── main.py          # FastAPI entry point, health endpoint
│   ├── config.py        # Pydantic Settings configuration
│   ├── routers/         # API route handlers
│   │   ├── session.py   # /session endpoints
│   │   ├── chat.py      # /chat endpoint
│   │   └── voice.py     # /voice/stt and /voice/tts endpoints
│   ├── models/          # Pydantic models
│   │   ├── session.py   # Session-related models
│   │   ├── chat.py      # Chat-related models
│   │   ├── voice.py     # Voice-related models
│   │   └── common.py    # Shared models (ErrorResponse, etc.)
│   ├── services/        # Business logic (RAG, TTS, STT)
│   └── utils/           # Helper utilities
├── tests/               # pytest test files
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (not committed)
```

## API Endpoints (per CONTRACT.md)
- `GET /health` - Health check
- `POST /session` - Create session
- `GET /session/{id}` - Get session
- `POST /chat` - Send chat message
- `POST /voice/stt` - Speech-to-text
- `POST /voice/tts` - Text-to-speech
