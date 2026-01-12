# Integration Status — Zoocari

## Current Goal
- Define stable contracts for session/chat/voice
- Implement FE + BE in parallel
- Add smoke tests to ensure integration stays aligned

## Phase 0 Verification (QA Agent)
**Date:** 2026-01-10
**Status:** All acceptance criteria VERIFIED with 1 issue found

### Verification Results
- Task 0.1 (Directory Structure): PASS
- Task 0.2 (Backend): PASS (with dependency issue noted)
- Task 0.3 (Frontend): PASS
- Task 0.4 (Docker): PASS
- Task 0.6 (Legacy): PASS

## Open Questions / Blockers
- [ ] Auth approach (none? API key? cookie session?)
- [x] TTS response content-type (audio/mpeg vs audio/wav) — **RESOLVED:** Using audio/wav (24kHz, 16-bit mono WAV)
- [ ] STT max file size limit (TBD)
- [x] RAG source format + any citation expectations — **RESOLVED:** Sources return `[{"animal": "Lemur", "title": "Diet"}]`
- [ ] **BLOCKER:** kokoro>=0.9.4 requires Python 3.10-3.12 but Python 3.14.2 is installed. Causes pip install failure in apps/api.
- [x] **BLOCKER:** CORS config parsing error in docker. — **RESOLVED:** Added @field_validator to parse comma-separated CORS_ORIGINS env var in config.py.

## Decisions Log
- 2026-01-10: Phase 0 verification completed. All tasks pass except kokoro dependency.
- 2026-01-11: Session endpoints implemented per CONTRACT.md Part 4. POST /session returns only {session_id, created_at}. GET /session/{id} returns {session_id, created_at, metadata}. Error responses use standard shape. In-memory storage for now (SQLite migration by sessiondb agent later).
- 2026-01-11: Chat endpoint implemented per CONTRACT.md Part 4. POST /chat validates session_id, returns mock reply with proper shape {session_id, message_id, reply, sources, created_at}. Returns 404 for invalid session. Mock implementation only - actual RAG integration deferred to rag agent.
- 2026-01-11: Voice STT endpoint implemented per CONTRACT.md Part 4. POST /voice/stt accepts multipart/form-data (session_id + audio file), validates session exists, accepts common browser formats (webm, wav, mp3). Returns {session_id, text} with mock transcription for now. Proper error shapes for SESSION_NOT_FOUND, INVALID_AUDIO, EMPTY_AUDIO. Actual faster-whisper integration deferred to voice agent later.
- 2026-01-11: Voice TTS endpoint implemented per CONTRACT.md Part 4. POST /voice/tts accepts JSON {session_id, text, voice}, validates session_id exists and text is not empty. Returns audio/wav bytes (24kHz 16-bit mono WAV). Currently returns mock audio (1-second silence). Proper error shapes for SESSION_NOT_FOUND, EMPTY_TEXT. Actual Kokoro TTS integration deferred to voice agent later. 9 tests added to test_voice_endpoints.py. Verification script: verify_voice_tts.sh.
- 2026-01-11: Integration smoke tests completed.
- 2026-01-11: SQLite session persistence implemented. SessionService created in apps/api/app/services/session.py, ported from legacy/session_manager.py. Schema backward compatible with existing sessions.db. Methods: get_or_create_session, save_message, get_chat_history, get_session_stats. All routers updated to use SessionService. 21 new unit tests, all 98 tests passing. 14 end-to-end tests verify all Phase 1 endpoints work correctly together. Test flows: health check, session create/retrieve, chat, voice STT/TTS, full voice assistant flow (STT→chat→TTS), error handling (404s/422s), session reuse across endpoints, rapid sequential requests. All tests use mock data (no external dependencies). Tests pass in <1 second. Added pytest.ini with smoke marker, run_smoke_tests.sh script, and tests/README.md.
- 2026-01-11: RAG service implemented. RAGService created in apps/api/app/services/rag.py. Ported Zoocari persona prompt from legacy/zoo_chat.py. Methods: search_context (LanceDB retrieval), generate_response (GPT-4o-mini), extract_followup_questions (regex parsing). Lazy-loaded connections for LanceDB and OpenAI. Integrated into POST /chat router. Sources format: [{"animal": "Lemur", "title": "Diet"}]. Confidence score: 1 - avg_distance. Documentation: docs/rag_service.md. Standalone test: apps/api/tests/test_rag_standalone.py.
- 2026-01-11: CORS config fix. Added @field_validator to config.py to parse comma-separated CORS_ORIGINS env var into list.
- 2026-01-11: Voice STT/TTS services implemented. STTService (apps/api/app/services/stt.py) with Faster-Whisper (local, base model, int8) → OpenAI Whisper API fallback. TTSService (apps/api/app/services/tts.py) with Kokoro (local, kid-friendly voices) → OpenAI TTS API fallback. Voice presets: bella, nova, heart, sarah, adam, eric, default. Markdown stripping and text chunking (800 chars) for optimal TTS quality. Smart audio format detection for test compatibility. Integrated into POST /voice/stt and POST /voice/tts routers. All 18 voice tests passing. Verification scripts updated.
- 2026-01-11: SSE streaming implemented. POST /chat/stream endpoint with Server-Sent Events using sse-starlette. Added generate_response_stream() method to RAGService. SSE event sequence: session validation → context search → stream text chunks {"type": "text", "content": "..."} → done event {"type": "done", "sources": [...], "followup_questions": [...]}. Error events: {"type": "error", "content": "..."}. Uses existing StreamChunk model. Verification script: verify_chat_stream.sh.
- 2026-01-11: **Phase 2 started.** Task 2.1 (TypeScript Types) completed. Updated apps/web/src/types/index.ts with Session, ChatMessage, Source, StreamChunk types. ChatResponse updated with followup_questions and confidence fields. All types match backend models exactly. No TypeScript errors.
- 2026-01-12: Task 2.3 (Zustand Stores) completed. Created 3 stores in apps/web/src/stores/: sessionStore.ts (session lifecycle with localStorage persistence), chatStore.ts (messages, streaming, sources, followup questions), voiceStore.ts (MediaRecorder, STT, TTS, playback). All stores use typed API client functions. TypeScript compilation and Vite build pass.
- 2026-01-12: **Phase 3 started.** Task 3.1 (useVoiceRecorder Hook) completed. Created apps/web/src/hooks/useVoiceRecorder.ts with MediaRecorder + getUserMedia. Supports audio/webm (preferred) with audio/mp4 fallback for Safari. Duration tracking every 100ms. State: isRecording, isPreparing, audioBlob, duration, error. Methods: startRecording, stopRecording, cancelRecording, reset. Proper cleanup of stream tracks, timers on unmount. Created apps/web/src/hooks/index.ts for re-exports. TypeScript compilation passes.

## Missing Services (Priority)

Per migration.md acceptance criteria, the following services need actual implementation (currently mocks):

### HIGH PRIORITY

| Service | Agent | Current State | Required |
|---------|-------|---------------|----------|
| ~~**SQLite Session Persistence**~~ | sessiondb | ✅ DONE | SQLite with sessions.db, backward compatible |
| ~~**RAG Service**~~ | rag | ✅ DONE (streaming + non-streaming) | LanceDB vector search + OpenAI LLM |
| ~~**STT Service**~~ | voice | ✅ DONE | Faster-Whisper (local) + OpenAI Whisper API fallback |
| ~~**TTS Service**~~ | voice | ✅ DONE | Kokoro (local) + OpenAI TTS API fallback |

### MEDIUM PRIORITY

| Service | Agent | Current State | Required |
|---------|-------|---------------|----------|
| ~~**SSE Streaming**~~ | backend | ✅ DONE | POST /chat/stream with SSE |
| ~~**Follow-up Questions**~~ | rag | ✅ DONE | Extracted via extract_followup_questions() |
| ~~**Sources/Citations**~~ | rag | ✅ DONE | Returns [{"animal", "title"}] from LanceDB |

### Next Steps (Recommended Order)

1. ~~**sessiondb agent**~~ — ✅ DONE: SQLite persistence
2. ~~**rag agent**~~ — ✅ DONE: LanceDB + OpenAI integration
3. ~~**voice agent**~~ — ✅ DONE: STT with Faster-Whisper + OpenAI fallback
4. ~~**voice agent**~~ — ✅ DONE: TTS with Kokoro + OpenAI fallback
5. ~~**backend agent**~~ — ✅ DONE: SSE streaming for /chat/stream

**All Phase 1 services implemented!**

---

## Integration Checklist

### Phase 0: Foundation
- [x] FastAPI backend initialized (Task 0.2)
  - requirements.txt created with all dependencies
  - config.py with Pydantic Settings
  - main.py with /health endpoint
  - Pydantic models aligned to CONTRACT.md
  - Router placeholders for session/chat/voice
  - Basic test structure

- [x] Vite + React frontend initialized (Task 0.3)
  - Vite 6 + React 18 + TypeScript
  - Tailwind CSS with Leesburg brand colors
  - Zustand state management
  - API proxy configured (localhost:8000)
  - TypeScript types aligned to CONTRACT.md Part 4
  - src/lib/api.ts stub with typed functions
  - Minimal App.tsx placeholder compiles

### Phase 1+: Implementation
- [x] /health works in docker and host
- [x] /session create + fetch works (2026-01-11)
  - POST /session creates session with UUID, returns {session_id, created_at}
  - GET /session/{id} retrieves session or returns 404 with error shape
  - In-memory storage (dict) for now
  - 10 tests passing in test_session_endpoints.py
  - Verified with manual curl commands
- [x] /chat returns reply in correct shape (2026-01-11)
  - POST /chat accepts {session_id, message, mode?, metadata?}
  - Returns {session_id, message_id, reply, sources, created_at}
  - Validates session_id exists, returns 404 with error shape if not found
  - Mock reply implementation (RAG integration by rag agent later)
  - 8 tests passing in test_chat_endpoints.py
  - Validation: message min_length=1, max_length=1000
  - Verification script: verify_chat_endpoint.sh
- [x] /voice/stt accepts browser recording format (2026-01-11, implemented 2026-01-11)
  - POST /voice/stt accepts multipart/form-data with session_id and audio file
  - Returns {session_id, text} per CONTRACT.md
  - Validates session_id exists, returns 404 with error shape if not found
  - Accepts common browser formats: webm, wav, mp3
  - **STTService** implemented with local-first, cloud fallback:
    - Faster-Whisper (local, base model, int8) - fast, free, offline
    - OpenAI Whisper API (cloud) - paid fallback
    - Smart audio format detection for test compatibility
  - 9 tests passing in test_voice_endpoints.py
  - Verification script: verify_voice_stt.sh
- [x] /voice/tts returns playable audio (2026-01-11, implemented 2026-01-11)
  - POST /voice/tts accepts JSON {session_id, text, voice} per CONTRACT.md
  - Returns audio/wav bytes (24kHz 16-bit mono WAV)
  - Validates session_id exists and text is not empty
  - Returns proper error shapes: SESSION_NOT_FOUND, EMPTY_TEXT
  - **TTSService** implemented with local-first, cloud fallback:
    - Kokoro (local, kid-friendly voices) - high quality, free, offline
    - OpenAI TTS API (cloud) - paid fallback
    - Voice presets: bella, nova, heart, sarah, adam, eric, default
    - Markdown stripping for clean TTS output
    - Text chunking for optimal quality (max 800 chars/chunk)
  - 9 tests passing in test_voice_endpoints.py (18 total voice tests)
  - Verification script: verify_voice_tts.sh
- [x] tests/integration smoke passes in CI/dev (2026-01-11)
  - test_integration_smoke.py with 14 end-to-end tests
  - Tests cover: health, sessions, chat, voice STT/TTS, full flows, errors
  - All tests passing in <1 second
  - pytest.ini configured with smoke marker
  - run_smoke_tests.sh convenience script added
  - README.md added to tests/ directory

### Phase 2: Frontend Foundation
- [x] Task 2.1: Create TypeScript Types (2026-01-11)
  - Updated `apps/web/src/types/index.ts` with complete type definitions
  - **Types Added:**
    - `Session` - full session with session_id, created_at, last_active, message_count, client, metadata
    - `ChatMessage` - message with message_id, session_id, role ('user'|'assistant'), content, created_at
    - `Source` - citation with {animal, title}
    - `StreamChunk` - SSE chunk with type ('text'|'done'|'error'), content, sources, followup_questions
  - **Types Updated:**
    - `ChatResponse` - added followup_questions: string[], confidence: number
  - **Acceptance Criteria:**
    - [x] All types defined
    - [x] Types match API contracts exactly (verified against apps/api/app/models/*.py)
    - [x] No TypeScript errors (npx tsc --noEmit passed)
- [x] Task 2.2: Create API Client (2026-01-11)
  - Implemented all API methods in `apps/web/src/lib/api.ts`
  - **Methods Implemented:**
    - `createSession(request)` - POST /api/session
    - `getSession(sessionId)` - GET /api/session/{id}
    - `sendChatMessage(request)` - POST /api/chat
    - `streamChatMessage(request, onChunk, onComplete, onError)` - POST /api/chat/stream with SSE
    - `speechToText(request)` - POST /api/voice/stt with multipart/form-data
    - `textToSpeech(request)` - POST /api/voice/tts returns Blob
    - `checkHealth()` - GET /api/health
  - **Features:**
    - SSE streaming implementation using fetch ReadableStream
    - Proper FormData handling for STT (multipart upload)
    - Blob response handling for TTS (audio bytes)
    - Comprehensive error handling with fallback messages
    - TypeScript types imported and used correctly
  - **Acceptance Criteria:**
    - [x] All API methods implemented
    - [x] Error handling working (try/catch with ApiError parsing)
    - [x] Streaming support working (SSE with ReadableStream parser)
    - [x] TypeScript types correct (npx tsc --noEmit passed)
- [x] Task 2.3: Create Zustand Stores
  - [x] sessionStore.ts: session lifecycle, persist to localStorage
  - [x] chatStore.ts: messages, streaming, sources, followup questions
  - [x] voiceStore.ts: recording, STT, TTS, playback state
  - [x] index.ts: re-export all stores
  - [x] TypeScript compilation passed (npx tsc --noEmit)
  - [x] Build passed (npm run build)
- [x] Task 2.4: Create Layout Component
  - [x] Layout.tsx: header with Zoocari branding, main content area, footer
  - [x] Mobile-first responsive design with Leesburg brand colors
  - [x] components/index.ts for clean imports
- [x] Task 2.5: Create MessageBubble Component
  - [x] MessageBubble.tsx: user (right/yellow) vs assistant (left/beige) bubbles
  - [x] Streaming indicator with animated bouncing dots
  - [x] Kid-friendly text size (text-lg) and rounded design
  - [x] Sources display below assistant messages when available
- [x] Task 2.6: Create AnimalGrid Component
  - [x] AnimalGrid.tsx: Leesburg animals (Lions, Elephants, Giraffes, Camels, Emus, Servals, Porcupines, Lemurs)
  - [x] 4x2 grid layout (4 cols desktop, 2 cols mobile), hover effects
  - [x] onSelectAnimal callback prop, disabled state support
- [x] Task 2.7: Create ChatInput Component
  - [x] ChatInput.tsx: text input + send button + prominent mic button
  - [x] Recording state with red pulsing animation
  - [x] Voice-first design, large touch targets, Enter to submit
- [x] Task 2.8: Create FollowupQuestions Component
  - [x] FollowupQuestions.tsx: clickable pill-shaped question chips
  - [x] Brown background with white text, orange hover
  - [x] Flex-wrap layout, returns null when empty
