# Zoocari Migration Project Plan
## Streamlit to Vite + React + FastAPI

---

## Executive Summary

### Project Overview
Migrate the Zoocari Zoo Q&A Chatbot from a Streamlit monolith to a modern architecture using Vite + React for the frontend and FastAPI for the backend. The primary goal is to improve UX/performance, particularly for voice interactions.

### Key Metrics
| Metric | Value |
|--------|-------|
| **Estimated Effort** | 165-255 hours |
| **Timeline** | 6-8 weeks |
| **Team Size** | 1-2 developers |
| **Risk Level** | Medium |

### Success Criteria
- [ ] Full feature parity with current Streamlit application
- [ ] Voice recording works reliably on mobile (iOS Safari, Chrome)
- [ ] Response latency <= current Streamlit version
- [ ] Zero data loss during migration
- [ ] Rollback capability within 5 minutes

---

## Current Architecture

### Technology Stack
| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | Streamlit | Latest |
| Backend | Streamlit (same process) | Latest |
| Vector DB | LanceDB | Latest |
| Session DB | SQLite | 3.x |
| LLM | OpenAI GPT-4o-mini | - |
| Embeddings | OpenAI text-embedding-3-large | - |
| STT | Faster-Whisper (local) -> OpenAI (fallback) | 1.0+ |
| TTS | OpenAI -> ElevenLabs -> Kokoro (local) | - |
| Deployment | Docker + Cloudflare Tunnel | - |

### File Inventory
```
zoocari/
├── zoo_chat.py              # 913 lines - Main application
├── session_manager.py       # 357 lines - SQLite session handling
├── tts_kokoro.py           # 159 lines - Local TTS
├── zoo_build_knowledge.py  # 260 lines - Knowledge base builder
├── zoo_sources.py          # 269 lines - URL configuration
├── utils/
│   ├── text.py             # 67 lines - Text utilities
│   └── tokenizer.py        # 57 lines - Tokenizer wrapper
├── static/
│   └── zoocari.css         # 882 lines - UI styling
├── data/
│   ├── zoo_lancedb/        # Vector database
│   └── sessions.db         # SQLite sessions
├── Dockerfile              # Multi-stage build
└── docker-compose.yml      # Service orchestration
```

### Current Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Process                         │
│                                                                  │
│  User Input ──► STT ──► Vector Search ──► LLM ──► TTS ──► Audio │
│  (voice/text)   │         (LanceDB)      (GPT)    │      Output │
│                 │                                  │              │
│                 └──────────────────────────────────┘              │
│                         OpenAI API                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Target Architecture

### Technology Stack
| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | Vite + React + TypeScript | Vite 5.x, React 18.x |
| State Management | Zustand | 4.x |
| Styling | Tailwind CSS | 3.x |
| Backend | FastAPI + Pydantic | 0.109+ |
| Vector DB | LanceDB | (unchanged) |
| Session DB | SQLite | (unchanged) |
| HTTP Client | Native fetch | - |
| Testing | Vitest + Playwright | Latest |

### Target Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ VoiceButton │  │ ChatInput   │  │ MessageList + AudioPlay │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │
│         │                │                       ▲               │
│         └────────────────┼───────────────────────┘               │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTP/SSE
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│  │ /api/stt │  │/api/chat │  │ /api/tts │  │ /api/session   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘   │
│       │             │             │                │             │
│       ▼             ▼             ▼                ▼             │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐    ┌───────────┐        │
│  │ Whisper │  │ LanceDB  │  │  TTS    │    │  SQLite   │        │
│  └─────────┘  │ + OpenAI │  │ Chain   │    │ Sessions  │        │
│               └──────────┘  └─────────┘    └───────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure (Target)
```
zoocari/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py         # FastAPI app entry
│   │   │   ├── config.py       # Settings/environment
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py     # Chat endpoints
│   │   │   │   ├── voice.py    # STT/TTS endpoints
│   │   │   │   └── session.py  # Session endpoints
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── rag.py      # Vector search + LLM
│   │   │   │   ├── stt.py      # Speech-to-text
│   │   │   │   ├── tts.py      # Text-to-speech
│   │   │   │   └── session.py  # Session management
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py     # Pydantic models
│   │   │   │   └── session.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── text.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── web/                    # Vite + React frontend
│       ├── src/
│       │   ├── main.tsx
│       │   ├── App.tsx
│       │   ├── components/
│       │   │   ├── ChatInterface/
│       │   │   ├── VoiceButton/
│       │   │   ├── MessageBubble/
│       │   │   ├── AnimalGrid/
│       │   │   ├── AudioPlayer/
│       │   │   └── Layout/
│       │   ├── hooks/
│       │   │   ├── useVoiceRecorder.ts
│       │   │   ├── useChat.ts
│       │   │   ├── useSession.ts
│       │   │   └── useAudioPlayer.ts
│       │   ├── stores/
│       │   │   ├── chatStore.ts
│       │   │   └── sessionStore.ts
│       │   ├── lib/
│       │   │   ├── api.ts
│       │   │   └── constants.ts
│       │   ├── types/
│       │   │   └── index.ts
│       │   └── styles/
│       │       └── index.css
│       ├── public/
│       │   └── zoocari_mascot_web.png
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── package.json
│
├── data/                       # Shared data (mounted volume)
│   ├── zoo_lancedb/
│   └── sessions.db
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── docker-compose.yml
├── legacy/                     # Original Streamlit app (preserved)
│   ├── zoo_chat.py
│   └── ...
├── scripts/
│   ├── migrate.sh
│   └── rollback.sh
└── docs/
    └── api.md
```

---

## Phase 0: Foundation & Setup
**Duration: Week 1 (Days 1-5)**
**Goal: Establish project structure and development environment**

### Task 0.1: Create Monorepo Structure
**Priority:** Critical | **Effort:** 2 hours

**Steps:**
1. Create directory structure
2. Initialize git branches
3. Update .gitignore

**Commands:**
```bash
mkdir -p apps/api/app/{routers,services,models,utils}
mkdir -p apps/api/tests
mkdir -p apps/web/src/{components,hooks,stores,lib,types,styles}
mkdir -p apps/web/public
mkdir -p docker scripts docs legacy
```

**Acceptance Criteria:**
- [ ] Directory structure matches target
- [ ] .gitignore updated for Python + Node
- [ ] Feature branch created: `feature/node-fastapi-migration`

---

### Task 0.2: Initialize FastAPI Backend
**Priority:** Critical | **Effort:** 3 hours

**Steps:**
1. Create Python virtual environment
2. Create requirements.txt with dependencies
3. Create base FastAPI application
4. Create configuration module
5. Verify health endpoint works

**Dependencies (requirements.txt):**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
lancedb>=0.4.0
openai>=1.10.0
tiktoken>=0.5.0
faster-whisper>=1.0.0
kokoro>=0.9.4
soundfile>=0.12.0
elevenlabs>=1.0.0
httpx>=0.26.0
numpy>=1.26.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
sse-starlette>=1.6.0
```

**Acceptance Criteria:**
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] `GET /api/health` returns 200
- [ ] Configuration loads from .env

---

### Task 0.3: Initialize Vite + React Frontend
**Priority:** Critical | **Effort:** 3 hours

**Steps:**
1. Create Vite project with React + TypeScript template
2. Install additional dependencies (Zustand, Tailwind)
3. Configure Tailwind with Leesburg brand colors
4. Configure Vite proxy to FastAPI
5. Create base styles with fonts

**Commands:**
```bash
cd apps/web
npm create vite@latest . -- --template react-ts
npm install zustand @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Tailwind Config (key colors):**
```javascript
colors: {
  'leesburg-yellow': '#f5d224',
  'leesburg-brown': '#3d332a',
  'leesburg-beige': '#f4f2ef',
  'leesburg-orange': '#f29021',
  'leesburg-blue': '#76b9db',
}
```

**Acceptance Criteria:**
- [ ] Vite dev server runs on port 5173
- [ ] TypeScript compiles without errors
- [ ] Tailwind CSS working
- [ ] API proxy configured to localhost:8000

---

### Task 0.4: Create Development Docker Compose
**Priority:** High | **Effort:** 2 hours

**Steps:**
1. Create Dockerfile.dev for API
2. Create Dockerfile.dev for Web
3. Create docker-compose.dev.yml
4. Test hot reload for both services

**Acceptance Criteria:**
- [ ] `docker compose up` starts both services
- [ ] Hot reload works for Python changes
- [ ] Hot reload works for React changes
- [ ] Shared data volume accessible

---

### Task 0.5: Define API Contracts
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create OpenAPI specification (docs/api.yaml)
2. Define all endpoint schemas
3. Generate TypeScript types from spec (optional)
4. Document request/response formats

**Endpoints to Define:**
| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/api/health` | GET | - | `{status, version}` |
| `/api/chat` | POST | `{session_id, message}` | `{response, followups, sources}` |
| `/api/chat/stream` | POST | `{session_id, message}` | SSE stream |
| `/api/stt` | POST | `multipart/form-data` | `{text, duration_ms}` |
| `/api/tts` | POST | `{text, voice}` | `audio/mpeg` |
| `/api/session` | GET | `?session_id` | `{session_id, created_at, ...}` |
| `/api/session/{id}/history` | GET | `?limit` | `[{role, content, timestamp}]` |

**Acceptance Criteria:**
- [ ] OpenAPI spec complete
- [ ] All request/response schemas defined
- [ ] TypeScript types match API contracts

---

### Task 0.6: Preserve Legacy Application
**Priority:** Medium | **Effort:** 1 hour

**Steps:**
1. Copy all original files to legacy/ directory
2. Create legacy/docker-compose.yml
3. Create rollback script
4. Document rollback procedure

**Acceptance Criteria:**
- [ ] All original files in legacy/
- [ ] Legacy app can run independently
- [ ] Rollback script tested

---

## Phase 1: Backend API Development
**Duration: Week 2 (Days 6-12)**
**Goal: Create fully functional FastAPI backend**

### Task 1.1: Create Pydantic Models
**Priority:** Critical | **Effort:** 3 hours

**Steps:**
1. Create `app/models/chat.py` with ChatRequest, ChatResponse, StreamChunk
2. Create `app/models/session.py` with Session, SessionCreate, ChatMessage
3. Add validation rules (min/max lengths, ranges)
4. Write unit tests for model validation

**Key Models:**
```python
class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    response: str
    followup_questions: list[str]
    sources: list[str]
    confidence: float = Field(ge=0, le=1)
```

**Acceptance Criteria:**
- [ ] All models defined with proper types
- [ ] Validation rules working
- [ ] Unit tests passing

---

### Task 1.2: Implement Session Service
**Priority:** Critical | **Effort:** 4 hours

**Steps:**
1. Create `app/services/session.py`
2. Port logic from `session_manager.py`
3. Implement: get_or_create_session, save_message, get_chat_history
4. Add database schema initialization
5. Write unit tests

**Methods to Implement:**
| Method | Description |
|--------|-------------|
| `__init__` | Initialize DB connection, ensure schema |
| `get_or_create_session` | Get existing or create new session |
| `save_message` | Save chat message to history |
| `get_chat_history` | Get messages for session |
| `get_session_stats` | Get session statistics |

**Acceptance Criteria:**
- [ ] All session_manager.py functionality ported
- [ ] SQLite schema unchanged (backward compatible)
- [ ] Unit tests passing
- [ ] Works with existing sessions.db

---

### Task 1.3: Implement RAG Service
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create `app/services/rag.py`
2. Port Zoocari system prompt from zoo_chat.py
3. Implement vector search using LanceDB
4. Implement LLM response generation
5. Implement streaming response generator
6. Add follow-up question extraction
7. Write unit tests

**Methods to Implement:**
| Method | Description |
|--------|-------------|
| `search_context` | Search LanceDB for relevant chunks |
| `generate_response` | Generate complete response via OpenAI |
| `generate_response_stream` | Async generator for streaming |
| `extract_followups` | Parse follow-up questions from response |

**Acceptance Criteria:**
- [ ] Vector search returns relevant context
- [ ] LLM generates Zoocari-style responses
- [ ] Streaming works with SSE
- [ ] Follow-up questions extracted correctly

---

### Task 1.4: Implement STT Service
**Priority:** Critical | **Effort:** 4 hours

**Steps:**
1. Create `app/services/stt.py`
2. Implement Faster-Whisper local transcription
3. Implement OpenAI Whisper fallback
4. Add fallback chain logic
5. Handle audio format conversion if needed
6. Write unit tests

**Fallback Chain:**
1. Try Faster-Whisper (local, ~300ms)
2. Fall back to OpenAI Whisper API (~800ms)

**Acceptance Criteria:**
- [ ] Local STT works when Faster-Whisper available
- [ ] Fallback to OpenAI works
- [ ] Handles various audio formats
- [ ] Returns transcription with timing info

---

### Task 1.5: Implement TTS Service
**Priority:** Critical | **Effort:** 4 hours

**Steps:**
1. Create `app/services/tts.py`
2. Implement OpenAI TTS
3. Implement ElevenLabs fallback
4. Implement Kokoro local fallback
5. Add markdown stripping for clean TTS
6. Write unit tests

**Fallback Chain:**
1. OpenAI TTS (fast, reliable)
2. ElevenLabs (if API key configured)
3. Kokoro (if TTS_PROVIDER=kokoro)

**Acceptance Criteria:**
- [ ] OpenAI TTS generates audio
- [ ] ElevenLabs fallback works
- [ ] Kokoro works when configured
- [ ] Returns audio bytes (MP3/WAV)

---

### Task 1.6: Create API Routers
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create `app/routers/chat.py` with /chat and /chat/stream
2. Create `app/routers/voice.py` with /stt and /tts
3. Create `app/routers/session.py` with session endpoints
4. Register all routers in main.py
5. Add proper error handling
6. Write integration tests

**Router Files:**
| File | Endpoints |
|------|-----------|
| `chat.py` | POST /api/chat, POST /api/chat/stream |
| `voice.py` | POST /api/stt, POST /api/tts |
| `session.py` | GET /api/session, GET /api/session/{id}/history |

**Acceptance Criteria:**
- [ ] All endpoints responding correctly
- [ ] SSE streaming working
- [ ] Error responses follow consistent format
- [ ] Integration tests passing

---

### Task 1.7: Backend Testing
**Priority:** High | **Effort:** 6 hours

**Steps:**
1. Set up pytest with asyncio support
2. Create test fixtures for services
3. Write unit tests for all services
4. Write integration tests for all endpoints
5. Set up test coverage reporting
6. Achieve >80% coverage

**Test Files:**
```
tests/
├── conftest.py          # Fixtures
├── test_services/
│   ├── test_session.py
│   ├── test_rag.py
│   ├── test_stt.py
│   └── test_tts.py
└── test_routers/
    ├── test_chat.py
    ├── test_voice.py
    └── test_session.py
```

**Acceptance Criteria:**
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Coverage >80%
- [ ] CI pipeline ready

---

## Phase 2: Frontend Foundation
**Duration: Week 3 (Days 13-19)**
**Goal: Create React UI shell with components**

### Task 2.1: Create TypeScript Types
**Priority:** Critical | **Effort:** 2 hours

**Steps:**
1. Create `src/types/index.ts`
2. Define all interfaces matching API contracts
3. Export types for use across components

**Types to Define:**
- ChatMessage, ChatRequest, ChatResponse
- Session, SessionCreate
- STTResponse, TTSRequest
- StreamChunk

**Acceptance Criteria:**
- [ ] All types defined
- [ ] Types match API contracts exactly
- [ ] No TypeScript errors

---

### Task 2.2: Create API Client
**Priority:** Critical | **Effort:** 3 hours

**Steps:**
1. Create `src/lib/api.ts`
2. Implement chat, chatStream, speechToText, textToSpeech methods
3. Implement getSession, getChatHistory methods
4. Add proper error handling
5. Add TypeScript types for all methods

**API Client Methods:**
| Method | Description |
|--------|-------------|
| `chat(request)` | Send message, get full response |
| `chatStream(request, onChunk, onComplete)` | Stream response via SSE |
| `speechToText(audioBlob)` | Convert audio to text |
| `textToSpeech(text, voice)` | Convert text to audio |
| `getSession(sessionId?)` | Get or create session |
| `getChatHistory(sessionId, limit)` | Get message history |

**Acceptance Criteria:**
- [ ] All API methods implemented
- [ ] Error handling working
- [ ] Streaming support working
- [ ] TypeScript types correct

---

### Task 2.3: Create Zustand Stores
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `src/stores/sessionStore.ts` with persist middleware
2. Create `src/stores/chatStore.ts` with message state
3. Implement actions for sending messages, loading history
4. Add streaming support to chat store

**Session Store State:**
- session: Session | null
- isLoading, error
- initSession(), clearSession()

**Chat Store State:**
- messages: ChatMessage[]
- isLoading, isStreaming, currentResponse
- followupQuestions: string[]
- sendMessage(), loadHistory(), clearMessages()

**Acceptance Criteria:**
- [ ] Session persists to localStorage
- [ ] Chat messages managed correctly
- [ ] Streaming updates state properly

---

### Task 2.4: Create Layout Component
**Priority:** High | **Effort:** 2 hours

**Steps:**
1. Create `src/components/Layout/index.tsx`
2. Create `src/components/Layout/Header.tsx`
3. Apply Leesburg branding styles
4. Make responsive (mobile-first)

**Acceptance Criteria:**
- [ ] Layout renders correctly
- [ ] Header with mascot and title
- [ ] Responsive on mobile/desktop

---

### Task 2.5: Create MessageBubble Component
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `src/components/MessageBubble/index.tsx`
2. Create `src/components/MessageBubble/StreamingBubble.tsx`
3. Style user vs assistant bubbles differently
4. Show sources if available
5. Handle streaming state with cursor

**Acceptance Criteria:**
- [ ] User messages styled (right-aligned, yellow)
- [ ] Assistant messages styled (left-aligned, white/border)
- [ ] Streaming cursor shows during generation
- [ ] Sources displayed when available

---

### Task 2.6: Create AnimalGrid Component
**Priority:** Medium | **Effort:** 2 hours

**Steps:**
1. Create `src/components/AnimalGrid/index.tsx`
2. Define animal data (emoji, name, query)
3. Create responsive grid layout
4. Handle click to send predefined query

**Animals (match current app):**
- Lions, Elephants, Giraffes, Camels
- Emus, Servals, Porcupines, Lemurs

**Acceptance Criteria:**
- [ ] 4x2 grid displays correctly
- [ ] Click triggers onSelect callback
- [ ] Disabled state works
- [ ] Hover/active states styled

---

### Task 2.7: Create ChatInput Component
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `src/components/ChatInput/index.tsx`
2. Implement controlled input with form
3. Handle submit on Enter key
4. Clear input after submit
5. Handle disabled state

**Acceptance Criteria:**
- [ ] Input styled with Leesburg branding
- [ ] Submit on button click and Enter key
- [ ] Input clears after submit
- [ ] Disabled state prevents interaction

---

### Task 2.8: Create FollowupQuestions Component
**Priority:** Medium | **Effort:** 2 hours

**Steps:**
1. Create `src/components/FollowupQuestions/index.tsx`
2. Display list of clickable questions
3. Style with dark background (match current)
4. Handle empty state (return null)

**Acceptance Criteria:**
- [ ] Questions display in list
- [ ] Click triggers onSelect
- [ ] Styled with brown background
- [ ] Hidden when no questions

---

## Phase 3: Voice Integration
**Duration: Week 4 (Days 20-26)**
**Goal: Implement voice recording and playback**

### Task 3.1: Create useVoiceRecorder Hook
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create `src/hooks/useVoiceRecorder.ts`
2. Implement MediaRecorder setup with getUserMedia
3. Handle recording start/stop
4. Track duration during recording
5. Return audio Blob on stop
6. Handle errors gracefully
7. Clean up on unmount

**State to Track:**
- isRecording, isPreparing
- audioBlob, duration, error

**Methods to Expose:**
- startRecording(): Promise<void>
- stopRecording(): Promise<Blob | null>
- cancelRecording(): void
- reset(): void

**Acceptance Criteria:**
- [ ] Recording works on desktop Chrome
- [ ] Recording works on mobile Safari
- [ ] Duration tracks correctly
- [ ] Audio blob returned on stop
- [ ] Cleanup prevents memory leaks

---

### Task 3.2: Create VoiceButton Component
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create `src/components/VoiceButton/index.tsx`
2. Use useVoiceRecorder hook
3. Display different states (idle, recording, processing)
4. Add pulse animation during recording
5. Call STT API on stop
6. Pass transcript to parent
7. Add cancel button during recording

**States:**
| State | Visual |
|-------|--------|
| Idle | Yellow gradient, mic icon, gentle pulse |
| Preparing | Spinner, "Preparing..." |
| Recording | Orange/red gradient, recording dot, active pulse |
| Processing | Loading spinner, "Processing..." |

**Acceptance Criteria:**
- [ ] Button toggles recording on click
- [ ] Visual states match design spec
- [ ] Pulse animation during recording
- [ ] STT called on stop
- [ ] Transcript passed to parent

---

### Task 3.3: Create useAudioPlayer Hook
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `src/hooks/useAudioPlayer.ts`
2. Manage Audio element lifecycle
3. Track playback state (playing, time, duration)
4. Implement play, pause, stop, seek
5. Clean up Object URLs on unmount

**State to Track:**
- isPlaying, isLoading
- currentTime, duration, error

**Methods to Expose:**
- play(audioBlob: Blob): Promise<void>
- pause(): void
- stop(): void
- seek(time: number): void

**Acceptance Criteria:**
- [ ] Audio plays correctly
- [ ] Progress tracks correctly
- [ ] Play/pause/stop work
- [ ] Cleanup on unmount

---

### Task 3.4: Create AudioPlayer Component
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `src/components/AudioPlayer/index.tsx`
2. Use useAudioPlayer hook
3. Display play/pause button
4. Show progress bar
5. Show current time / duration
6. Auto-play option
7. Style with dark background

**Acceptance Criteria:**
- [ ] Player displays when audioBlob provided
- [ ] Play/pause toggles correctly
- [ ] Progress bar updates
- [ ] Time display formatted
- [ ] Auto-play works

---

## Phase 4: Integration & Chat Interface
**Duration: Week 5 (Days 27-33)**
**Goal: Connect all components into working application**

### Task 4.1: Create ChatInterface Component
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create `src/components/ChatInterface/index.tsx`
2. Integrate sessionStore and chatStore
3. Add voice/text mode toggle
4. Render VoiceButton or ChatInput based on mode
5. Render message list with MessageBubble
6. Render streaming response with StreamingBubble
7. Generate and play TTS on new assistant message
8. Render follow-up questions
9. Render animal grid
10. Handle auto-scroll to bottom

**Component Structure:**
```tsx
<ChatInterface>
  <ModeToggle />
  <VoiceButton /> or <ChatInput />
  <AnimalGrid />
  <MessageList>
    <MessageBubble />...
    <StreamingBubble /> (if streaming)
  </MessageList>
  <AudioPlayer />
  <FollowupQuestions />
</ChatInterface>
```

**Acceptance Criteria:**
- [ ] Full chat flow works
- [ ] Voice and text modes work
- [ ] Messages display correctly
- [ ] Streaming shows in real-time
- [ ] TTS plays automatically
- [ ] Follow-ups are clickable

---

### Task 4.2: Create Main App Component
**Priority:** Critical | **Effort:** 2 hours

**Steps:**
1. Update `src/App.tsx` to use Layout and ChatInterface
2. Update `src/main.tsx` with proper imports
3. Add error boundary (optional)
4. Verify all components work together

**Acceptance Criteria:**
- [ ] App renders without errors
- [ ] All features accessible
- [ ] Error boundary catches errors (if added)

---

### Task 4.3: Create WelcomeMessage Component
**Priority:** Medium | **Effort:** 1 hour

**Steps:**
1. Create welcome message matching current Streamlit design
2. Display when no messages in chat
3. Style with Leesburg branding

**Acceptance Criteria:**
- [ ] Welcome message displays on fresh session
- [ ] Matches current design
- [ ] Hidden when messages exist

---

### Task 4.4: Integration Testing
**Priority:** High | **Effort:** 4 hours

**Steps:**
1. Set up MSW (Mock Service Worker) for API mocking
2. Write integration tests for ChatInterface
3. Test voice button interaction (mocked)
4. Test message sending flow
5. Test follow-up question interaction

**Acceptance Criteria:**
- [ ] Integration tests pass
- [ ] Critical paths covered
- [ ] Mocking works correctly

---

## Phase 5: Testing & Polish
**Duration: Week 6 (Days 34-40)**
**Goal: Production-ready quality**

### Task 5.1: End-to-End Testing with Playwright
**Priority:** High | **Effort:** 6 hours

**Steps:**
1. Set up Playwright config
2. Write tests for main user flows
3. Test voice features (as much as possible)
4. Test mobile viewports
5. Set up CI integration

**E2E Test Scenarios:**
- [ ] Welcome message displays
- [ ] Send text message, receive response
- [ ] Quick animal buttons work
- [ ] Follow-up questions clickable
- [ ] Voice button visible and clickable
- [ ] Session persists across refresh
- [ ] Mobile layout works

**Acceptance Criteria:**
- [ ] All E2E tests passing
- [ ] Mobile tests passing
- [ ] CI pipeline runs tests

---

### Task 5.2: Performance Optimization
**Priority:** Medium | **Effort:** 4 hours

**Steps:**
1. Memoize expensive components with React.memo
2. Implement code splitting with React.lazy
3. Add API caching with react-query
4. Optimize audio compression
5. Run Lighthouse audit
6. Fix any performance issues

**Optimizations:**
- [ ] MessageBubble memoized
- [ ] AudioPlayer lazy-loaded
- [ ] Chat history cached
- [ ] Audio compressed before upload
- [ ] Lighthouse score >90

**Acceptance Criteria:**
- [ ] No unnecessary re-renders
- [ ] Initial load time acceptable
- [ ] Lighthouse score >90

---

### Task 5.3: Accessibility Improvements
**Priority:** Medium | **Effort:** 3 hours

**Steps:**
1. Add ARIA labels to all interactive elements
2. Ensure keyboard navigation works
3. Test with screen reader
4. Verify color contrast meets WCAG
5. Add focus indicators

**A11y Checklist:**
- [ ] Voice button has aria-label
- [ ] Messages have role="log"
- [ ] Focus visible on all interactive elements
- [ ] Color contrast >4.5:1
- [ ] Keyboard-only navigation works

**Acceptance Criteria:**
- [ ] ARIA labels present
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] Color contrast verified

---

### Task 5.4: Mobile Testing & Fixes
**Priority:** High | **Effort:** 4 hours

**Steps:**
1. Test on real iOS device (Safari)
2. Test on real Android device (Chrome)
3. Fix any mobile-specific bugs
4. Verify touch targets are 44px+
5. Verify no input zoom on iOS
6. Test voice recording on mobile

**Devices to Test:**
- [ ] iPhone (Safari)
- [ ] iPhone (Chrome)
- [ ] Android (Chrome)
- [ ] Android (Samsung Browser)

**Acceptance Criteria:**
- [ ] Voice recording works on mobile
- [ ] Audio playback works on mobile
- [ ] Touch targets large enough
- [ ] No unexpected zoom
- [ ] Scroll behavior smooth

---

## Phase 6: Deployment
**Duration: Week 7-8 (Days 41-54)**
**Goal: Production deployment with zero downtime**

### Task 6.1: Create Production Dockerfiles
**Priority:** Critical | **Effort:** 4 hours

**Steps:**
1. Create `docker/Dockerfile.api` with multi-stage build
2. Pre-download ML models in build stage
3. Copy built frontend into API container
4. Configure static file serving in FastAPI
5. Test production build locally

**Dockerfile Features:**
- Multi-stage build for smaller image
- Model pre-download for faster cold start
- Static file serving from FastAPI
- Health check endpoint

**Acceptance Criteria:**
- [ ] Production image builds successfully
- [ ] Image size reasonable (<2GB)
- [ ] Static files served correctly
- [ ] Health check works

---

### Task 6.2: Create Production Docker Compose
**Priority:** Critical | **Effort:** 3 hours

**Steps:**
1. Create `docker/docker-compose.prod.yml`
2. Configure health checks
3. Set resource limits
4. Configure logging
5. Add Cloudflare tunnel service

**Configuration:**
- Memory limit: 4GB
- Health check: every 30s
- Log rotation: 10MB, 3 files
- Tunnel profile: optional

**Acceptance Criteria:**
- [ ] Compose file complete
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Logging configured

---

### Task 6.3: Create Deployment Scripts
**Priority:** High | **Effort:** 3 hours

**Steps:**
1. Create `scripts/deploy.sh`
2. Create `scripts/rollback.sh`
3. Create `scripts/backup.sh`
4. Add health check verification
5. Add automatic rollback on failure

**Deploy Script Flow:**
1. Build images
2. Backup current data
3. Stop old containers
4. Start new containers
5. Wait for health check
6. Rollback if failed

**Acceptance Criteria:**
- [ ] Deploy script works
- [ ] Rollback script works
- [ ] Backup script works
- [ ] Automatic rollback on failure

---

### Task 6.4: Staging Deployment & Testing
**Priority:** Critical | **Effort:** 6 hours

**Steps:**
1. Create staging environment
2. Deploy to staging
3. Run full validation checklist
4. Perform load testing
5. Fix any issues found
6. Document staging results

**Validation Checklist:**
- [ ] All API endpoints responding
- [ ] Chat functionality working
- [ ] Voice recording on mobile
- [ ] TTS playback working
- [ ] Session persistence working
- [ ] Performance acceptable

**Acceptance Criteria:**
- [ ] Staging deployed
- [ ] All validation passed
- [ ] Load test completed
- [ ] Results documented

---

### Task 6.5: Production Cutover
**Priority:** Critical | **Effort:** 4 hours

**Steps:**
1. Complete pre-cutover checklist
2. Create final backup
3. Run deploy script
4. Verify health checks
5. Update Cloudflare tunnel
6. Smoke test critical paths
7. Monitor for 30 minutes
8. Keep legacy running for 48 hours

**Pre-Cutover Checklist:**
- [ ] Staging validation complete
- [ ] Backup scripts tested
- [ ] Rollback scripts tested
- [ ] Monitoring configured
- [ ] Team notified
- [ ] Maintenance window scheduled

**Acceptance Criteria:**
- [ ] Production deployed
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Monitoring active
- [ ] Rollback ready

---

## Risk Mitigation

### High-Risk Items

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mobile voice recording fails | Medium | High | Test on real devices early; fallback to text input |
| SSE streaming issues | Low | Medium | Implement polling fallback |
| Audio playback blocked | Medium | Medium | Handle autoplay restrictions gracefully |
| Session data migration | Low | High | Keep SQLite schema compatible |
| Performance regression | Low | Medium | Load test before cutover |

### Rollback Triggers

Immediately rollback if:
- Error rate >5% for 5 minutes
- P95 latency >5 seconds
- Voice features completely broken
- Data corruption detected

### Rollback Procedure

**Quick Rollback (<5 minutes):**
```bash
./scripts/rollback.sh
```

**Manual Rollback:**
1. Stop new containers: `docker compose down`
2. Start legacy: `docker compose -f legacy/docker-compose.yml up -d`
3. Verify: `curl http://localhost:8501/_stcore/health`

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Error rate | <1% | API error responses |
| P95 latency | <3s | API response time |
| Voice success rate | >95% | STT transcription success |
| Mobile usability | 100% | Manual testing |
| Lighthouse score | >90 | Lighthouse audit |
| Test coverage | >80% | Jest/Vitest coverage |

---

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Foundation | Project structure, dev environment |
| 2 | Backend | FastAPI with all endpoints |
| 3 | Frontend Foundation | React components, styling |
| 4 | Voice Integration | Recording, playback, STT/TTS |
| 5 | Integration | Full chat flow working |
| 6 | Testing & Polish | E2E tests, performance, a11y |
| 7 | Staging | Staging deployment, validation |
| 8 | Production | Production cutover, monitoring |

---

## Appendix A: API Endpoint Reference

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/api/health` | GET | - | `{status, version}` |
| `/api/chat` | POST | `{session_id, message}` | `{response, followup_questions, sources, confidence}` |
| `/api/chat/stream` | POST | `{session_id, message}` | SSE: `{type: "text"/"done", content/followups}` |
| `/api/stt` | POST | `multipart: audio` | `{text, duration_ms}` |
| `/api/tts` | POST | `{text, voice}` | `audio/mpeg` binary |
| `/api/session` | GET | `?session_id` | `{session_id, created_at, last_active, message_count}` |
| `/api/session/{id}/history` | GET | `?limit` | `[{role, content, timestamp, metadata}]` |

## Appendix B: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `ELEVENLABS_API_KEY` | No | - | ElevenLabs API key |
| `TTS_PROVIDER` | No | openai | TTS provider (openai/elevenlabs/kokoro) |
| `TTS_VOICE` | No | nova | Voice ID |
| `DB_PATH` | No | data/zoo_lancedb | LanceDB path |
| `SESSION_DB_PATH` | No | data/sessions.db | SQLite path |
| `CLOUDFLARE_TUNNEL_TOKEN` | No | - | Cloudflare tunnel token |

## Appendix C: File Migration Map

| Original File | New Location | Notes |
|---------------|--------------|-------|
| `zoo_chat.py` | Split across api + web | Logic -> API, UI -> Web |
| `session_manager.py` | `apps/api/app/services/session.py` | Minimal changes |
| `tts_kokoro.py` | `apps/api/app/services/tts.py` | Merged with other TTS |
| `zoo_sources.py` | `apps/api/app/config.py` | Or unchanged |
| `utils/text.py` | `apps/api/app/utils/text.py` | Minimal changes |
| `utils/tokenizer.py` | `apps/api/app/utils/tokenizer.py` | Unchanged |
| `static/zoocari.css` | `apps/web/src/styles/` | Converted to Tailwind |
| `zoocari_mascot_web.png` | `apps/web/public/` | Unchanged |

## Appendix D: Commands Quick Reference

```bash
# Development
cd apps/api && uvicorn app.main:app --reload --port 8000
cd apps/web && npm run dev

# Testing
cd apps/api && pytest
cd apps/web && npm test
cd apps/web && npx playwright test

# Build
cd apps/web && npm run build
docker compose -f docker/docker-compose.prod.yml build

# Deploy
./scripts/deploy.sh

# Rollback
./scripts/rollback.sh
```
