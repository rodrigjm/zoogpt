# Zoocari Admin Portal - System Architecture Design

## 1. Executive Summary

The Admin Portal is a separate Docker container providing operational visibility and content management for Zoocari. It connects to shared data stores (LanceDB, SQLite sessions) and the main API for real-time operations.

**Key Capabilities:**
1. **Analytics Dashboard** - Q&A pairs, session metrics, response latency, user experience insights
2. **Knowledge Base CRUD** - Add/remove animals, manage sources, rebuild vector index
3. **Prompt Engineering** - Edit Zoocari personality, system prompts, model parameters
4. **Voice Configuration** - TTS voice selection, speed adjustment, preview

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose Stack                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │   zoocari-app   │     │  admin-portal   │     │   cloudflared   │       │
│  │   (FastAPI)     │◄───►│   (FastAPI +    │     │   (HTTPS tunnel)│       │
│  │   Port: 8501    │     │    React SPA)   │     │                 │       │
│  │                 │     │   Port: 8502    │     │                 │       │
│  └────────┬────────┘     └────────┬────────┘     └─────────────────┘       │
│           │                       │                                         │
│           │   Shared Volumes      │                                         │
│           ▼                       ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     data/ (mounted volume)                       │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │       │
│  │  │ zoo_lancedb/ │  │ sessions.db  │  │ admin_config.json    │   │       │
│  │  │ (vectors)    │  │ (analytics)  │  │ (prompts, settings)  │   │       │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Models

### 3.1 Analytics Schema (SQLite Extension)

```sql
-- Extend existing sessions.db with analytics tables

-- Chat interactions for Q&A analysis
CREATE TABLE IF NOT EXISTS chat_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSON,                    -- Retrieved KB sources
    confidence_score REAL,           -- RAG confidence
    latency_ms INTEGER,              -- End-to-end response time
    rag_latency_ms INTEGER,          -- LanceDB query time
    llm_latency_ms INTEGER,          -- OpenAI API time
    tts_latency_ms INTEGER,          -- TTS synthesis time (if voice)
    feedback_rating INTEGER,         -- Optional user feedback (1-5)
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Session aggregates for dashboard
CREATE TABLE IF NOT EXISTS session_metrics (
    session_id TEXT PRIMARY KEY,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    message_count INTEGER DEFAULT 0,
    avg_response_latency_ms REAL,
    voice_requests INTEGER DEFAULT 0,
    client_type TEXT,               -- web, mobile, kiosk
    device_info JSON                -- user agent, screen size
);

-- Daily aggregates for trends
CREATE TABLE IF NOT EXISTS daily_analytics (
    date DATE PRIMARY KEY,
    total_sessions INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    avg_session_duration_sec REAL,
    avg_response_latency_ms REAL,
    unique_animals_queried JSON,    -- ["lion", "giraffe", ...]
    top_questions JSON,             -- Top 10 questions
    error_count INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_interactions_session ON chat_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON chat_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_start ON session_metrics(start_time);
```

### 3.2 Knowledge Base Management Schema

```sql
-- Animals and their source documents
CREATE TABLE IF NOT EXISTS kb_animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT,                   -- mammal, bird, reptile, etc.
    source_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Source documents for each animal
CREATE TABLE IF NOT EXISTS kb_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    content TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0,   -- Number of vector chunks
    last_indexed DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES kb_animals(id) ON DELETE CASCADE
);

-- Vector index rebuild history
CREATE TABLE IF NOT EXISTS kb_index_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    status TEXT DEFAULT 'running',   -- running, completed, failed
    total_documents INTEGER,
    total_chunks INTEGER,
    error_message TEXT
);
```

### 3.3 Configuration Schema

```json
// data/admin_config.json
{
  "version": "1.0",
  "lastModified": "2024-01-14T10:30:00Z",

  "prompts": {
    "systemPrompt": "You are Zoocari the Elephant...",
    "fallbackResponse": "Hmm, I don't know about that yet!",
    "followupQuestions": [
      "What do lions like to eat?",
      "How fast can a cheetah run?"
    ]
  },

  "model": {
    "name": "gpt-4o-mini",
    "temperature": 0.7,
    "maxTokens": 500
  },

  "rag": {
    "embeddingModel": "text-embedding-3-small",
    "numResults": 5,
    "confidenceThreshold": 0.3
  },

  "tts": {
    "provider": "kokoro",
    "defaultVoice": "af_heart",
    "speed": 1.0,
    "fallbackProvider": "openai"
  },

  "voices": {
    "kokoro": {
      "bella": {"id": "af_bella", "description": "Friendly female"},
      "heart": {"id": "af_heart", "description": "Expressive female"},
      "adam": {"id": "am_adam", "description": "Clear male"}
    },
    "openai": {
      "nova": {"id": "nova", "description": "Warm female"},
      "shimmer": {"id": "shimmer", "description": "Upbeat female"}
    }
  }
}
```

---

## 4. API Specification

### 4.1 Analytics Endpoints

```yaml
/api/admin/analytics:

  GET /dashboard:
    description: Get dashboard summary metrics
    response:
      today:
        sessions: 45
        questions: 234
        avgLatencyMs: 1250
        errorRate: 0.02
      trends:
        - date: "2024-01-14"
          sessions: 45
          questions: 234
      topQuestions:
        - question: "What do lions eat?"
          count: 23
      topAnimals:
        - name: "Lion"
          count: 45

  GET /sessions:
    description: List sessions with filtering
    params:
      startDate: datetime
      endDate: datetime
      minDuration: int
      limit: int (default 50)
    response:
      sessions:
        - sessionId: "uuid"
          startTime: datetime
          duration: 245
          messageCount: 8
          avgLatency: 1100

  GET /sessions/{session_id}/interactions:
    description: Get Q&A pairs for a session
    response:
      interactions:
        - timestamp: datetime
          question: "What do lions eat?"
          answer: "Lions are carnivores..."
          latencyMs: 1150
          sources: [...]
          confidence: 0.85

  GET /interactions:
    description: Search across all Q&A pairs
    params:
      search: string
      animal: string
      startDate: datetime
      endDate: datetime
      minConfidence: float
    response:
      total: 234
      interactions: [...]

  GET /latency-breakdown:
    description: Latency analysis by component
    response:
      overall:
        p50: 1100
        p90: 2300
        p99: 4500
      byComponent:
        rag: {p50: 200, p90: 400}
        llm: {p50: 800, p90: 1500}
        tts: {p50: 300, p90: 600}
```

### 4.2 Knowledge Base Endpoints

```yaml
/api/admin/kb:

  GET /animals:
    description: List all animals in knowledge base
    response:
      animals:
        - id: 1
          name: "lion"
          displayName: "African Lion"
          category: "mammal"
          sourceCount: 3
          isActive: true

  POST /animals:
    description: Add new animal
    body:
      name: string (unique slug)
      displayName: string
      category: string
    response:
      id: 1
      name: "lion"

  GET /animals/{id}:
    description: Get animal with sources
    response:
      id: 1
      name: "lion"
      sources:
        - id: 1
          title: "Lion Facts"
          url: "https://..."
          chunkCount: 5
          lastIndexed: datetime

  PUT /animals/{id}:
    description: Update animal metadata
    body:
      displayName: string
      category: string
      isActive: boolean

  DELETE /animals/{id}:
    description: Remove animal and sources
    note: Requires vector index rebuild

  POST /animals/{id}/sources:
    description: Add source document
    body:
      title: string
      url: string (optional)
      content: string
    response:
      id: 1
      status: "pending_index"

  DELETE /animals/{id}/sources/{source_id}:
    description: Remove source document

  POST /index/rebuild:
    description: Trigger full vector index rebuild
    response:
      jobId: "uuid"
      status: "started"

  GET /index/status:
    description: Get current index status
    response:
      lastRebuild: datetime
      status: "ready" | "rebuilding"
      documentCount: 150
      chunkCount: 890
```

### 4.3 Configuration Endpoints

```yaml
/api/admin/config:

  GET /prompts:
    description: Get current prompt configuration
    response:
      systemPrompt: string
      fallbackResponse: string
      followupQuestions: [string]

  PUT /prompts:
    description: Update prompts
    body:
      systemPrompt: string
      fallbackResponse: string
      followupQuestions: [string]
    note: Changes apply immediately

  GET /model:
    description: Get LLM settings
    response:
      name: "gpt-4o-mini"
      temperature: 0.7
      maxTokens: 500

  PUT /model:
    description: Update LLM settings
    body:
      name: string (validated)
      temperature: float (0.0-2.0)
      maxTokens: int (100-2000)

  GET /tts:
    description: Get TTS configuration
    response:
      provider: "kokoro" | "openai"
      defaultVoice: string
      speed: float
      availableVoices:
        kokoro: [{id, name, description}]
        openai: [{id, name, description}]

  PUT /tts:
    description: Update TTS settings
    body:
      provider: string
      defaultVoice: string
      speed: float

  POST /tts/preview:
    description: Preview TTS with settings
    body:
      text: string
      voice: string
      speed: float
    response:
      audioUrl: string (temp file)
      durationMs: int
```

---

## 5. Frontend Component Architecture

```
apps/admin/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── api/
│   │   ├── client.ts           # Fetch wrapper with auth
│   │   ├── analytics.ts        # Analytics API hooks
│   │   ├── kb.ts               # Knowledge base API hooks
│   │   └── config.ts           # Config API hooks
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── Analytics/
│   │   │   ├── Dashboard.tsx       # Main metrics overview
│   │   │   ├── SessionList.tsx     # Browsable session history
│   │   │   ├── InteractionViewer.tsx # Q&A pair inspector
│   │   │   ├── LatencyChart.tsx    # Response time breakdown
│   │   │   └── TrendsChart.tsx     # Usage over time
│   │   ├── KnowledgeBase/
│   │   │   ├── AnimalList.tsx      # CRUD animals table
│   │   │   ├── AnimalEditor.tsx    # Edit animal + sources
│   │   │   ├── SourceEditor.tsx    # Add/edit source content
│   │   │   └── IndexStatus.tsx     # Rebuild status/trigger
│   │   ├── Config/
│   │   │   ├── PromptEditor.tsx    # System prompt editor
│   │   │   ├── ModelSettings.tsx   # LLM parameters
│   │   │   └── VoiceSettings.tsx   # TTS config + preview
│   │   └── shared/
│   │       ├── DataTable.tsx
│   │       ├── Charts.tsx
│   │       └── AudioPlayer.tsx
│   ├── stores/
│   │   ├── authStore.ts
│   │   └── configStore.ts
│   └── types/
│       └── index.ts
├── package.json
└── vite.config.ts
```

---

## 6. Docker Deployment

### 6.1 docker-compose.yml Addition

```yaml
services:
  # ... existing zoocari service ...

  admin-portal:
    build:
      context: .
      dockerfile: Dockerfile.admin
    container_name: zoocari-admin
    ports:
      - "8502:8502"

    volumes:
      # Share data directory with main app
      - ./data:/app/data

    environment:
      - ADMIN_API_PORT=8502
      - ZOOCARI_API_URL=http://zoocari:8501
      - OPENAI_API_KEY=${OPENAI_API_KEY}

      # Admin authentication
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}

      # Optional: JWT secret for session tokens
      - JWT_SECRET=${JWT_SECRET:-auto-generated}

    depends_on:
      - zoocari

    restart: unless-stopped

    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 256M
```

### 6.2 Dockerfile.admin

```dockerfile
# Multi-stage build for Admin Portal
FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY apps/admin/package*.json ./
RUN npm ci
COPY apps/admin/ ./
RUN npm run build

FROM python:3.12-slim AS backend

WORKDIR /app

# Install Python dependencies
COPY apps/admin-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY apps/admin-api/ ./

# Copy built frontend
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8502

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8502"]
```

---

## 7. Security Considerations

### 7.1 Authentication
- Basic auth for initial MVP (username/password in env vars)
- JWT tokens for session management
- Optional: Upgrade to OAuth2/OIDC for production

### 7.2 Authorization
- Single admin role initially
- Read-only access for analytics
- Write access requires authentication

### 7.3 Data Protection
- Admin credentials never logged
- Sensitive config values encrypted at rest
- API rate limiting to prevent abuse

### 7.4 Network Isolation
- Admin portal not exposed through Cloudflare tunnel by default
- Requires explicit network access or VPN

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up admin-api FastAPI project
- [ ] Extend SQLite schema for analytics
- [ ] Implement analytics collection in main app
- [ ] Build basic dashboard API endpoints

### Phase 2: Analytics Dashboard (Week 2-3)
- [ ] Create React admin app with Vite
- [ ] Build dashboard components
- [ ] Implement session/interaction viewers
- [ ] Add latency breakdown charts

### Phase 3: Knowledge Base Management (Week 3-4)
- [ ] CRUD API for animals/sources
- [ ] Index rebuild worker
- [ ] React components for KB management
- [ ] Source document editor

### Phase 4: Configuration & Voice (Week 4-5)
- [ ] Prompt editor with preview
- [ ] Model parameter configuration
- [ ] TTS voice selection and preview
- [ ] Configuration hot-reload

### Phase 5: Polish & Deploy (Week 5-6)
- [ ] Authentication implementation
- [ ] Docker integration
- [ ] Documentation
- [ ] Testing and QA

---

## 9. File Structure Summary

```
zoocari/
├── apps/
│   ├── api/              # Existing main API
│   ├── web/              # Existing frontend
│   ├── admin/            # NEW: Admin React SPA
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── admin-api/        # NEW: Admin backend
│       ├── main.py
│       ├── routers/
│       │   ├── analytics.py
│       │   ├── kb.py
│       │   └── config.py
│       ├── services/
│       │   ├── analytics.py
│       │   ├── kb.py
│       │   └── indexer.py
│       ├── models/
│       └── requirements.txt
├── data/
│   ├── zoo_lancedb/      # Shared vector DB
│   ├── sessions.db       # Shared sessions + analytics
│   └── admin_config.json # Admin-managed config
├── docker-compose.yml    # Updated
└── Dockerfile.admin      # NEW
```

---

## 10. Integration Points with Main App

### 10.1 Analytics Collection (Modify main app)
Add timing instrumentation to `apps/api/app/routers/chat.py`:

```python
# Record interaction after response
await analytics_service.record_interaction(
    session_id=session_id,
    question=request.message,
    answer=response.answer,
    sources=response.sources,
    confidence=response.confidence,
    latency_ms=total_latency,
    rag_latency_ms=rag_latency,
    llm_latency_ms=llm_latency
)
```

### 10.2 Configuration Hot-Reload
Main app watches `admin_config.json` for changes:

```python
# apps/api/app/config.py
class DynamicConfig:
    """Hot-reloadable config from admin portal."""

    def __init__(self, config_path: str):
        self._path = config_path
        self._last_modified = 0
        self._config = {}
        self._reload()

    def _reload(self):
        stat = os.stat(self._path)
        if stat.st_mtime > self._last_modified:
            with open(self._path) as f:
                self._config = json.load(f)
            self._last_modified = stat.st_mtime

    @property
    def system_prompt(self) -> str:
        self._reload()
        return self._config.get("prompts", {}).get("systemPrompt", DEFAULT_PROMPT)
```

---

## Appendix A: UI Wireframes

### Dashboard View
```
┌──────────────────────────────────────────────────────────────────┐
│  Zoocari Admin Portal                           [Admin ▾] [⚙]   │
├──────────┬───────────────────────────────────────────────────────┤
│          │  📊 Dashboard                                         │
│ Dashboard│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│ Sessions │  │Sessions │ │Questions│ │Avg Resp │ │Error    │     │
│ Q&A Pairs│  │   45    │ │   234   │ │  1.2s   │ │  2%     │     │
│          │  │ Today   │ │ Today   │ │ Latency │ │ Rate    │     │
│ ──────── │  └─────────┘ └─────────┘ └─────────┘ └─────────┘     │
│ Knowledge│                                                       │
│ Animals  │  ┌─────────────────────────────────────────────────┐  │
│ Sources  │  │              Usage Trends (7 days)              │  │
│ Index    │  │  📈 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │
│          │  └─────────────────────────────────────────────────┘  │
│ ──────── │                                                       │
│ Config   │  ┌──────────────────┐ ┌──────────────────────────┐   │
│ Prompts  │  │ Top Questions    │ │ Response Time Breakdown  │   │
│ Model    │  │ 1. What do lions │ │ RAG:  ████░░ 200ms      │   │
│ Voice    │  │ 2. How fast can  │ │ LLM:  ████████░ 800ms   │   │
│          │  │ 3. Why zebras    │ │ TTS:  ███░░░░░ 300ms    │   │
│          │  └──────────────────┘ └──────────────────────────┘   │
└──────────┴───────────────────────────────────────────────────────┘
```

### Knowledge Base View
```
┌──────────────────────────────────────────────────────────────────┐
│  🦁 Knowledge Base                    [+ Add Animal] [Rebuild]   │
├──────────────────────────────────────────────────────────────────┤
│  Search: [________________________]                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Animal        │ Category │ Sources │ Status  │ Actions     ││
│  ├───────────────┼──────────┼─────────┼─────────┼─────────────┤│
│  │ 🦁 Lion       │ Mammal   │ 3       │ ✓ Active│ Edit Delete ││
│  │ 🦒 Giraffe    │ Mammal   │ 2       │ ✓ Active│ Edit Delete ││
│  │ 🐘 Elephant   │ Mammal   │ 4       │ ✓ Active│ Edit Delete ││
│  │ 🦜 Parrot     │ Bird     │ 2       │ ✓ Active│ Edit Delete ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Index Status: ✓ Ready | Last rebuilt: 2024-01-14 10:30 AM      │
│  Documents: 45 | Chunks: 890                                     │
└──────────────────────────────────────────────────────────────────┘
```

### Prompt Editor View
```
┌──────────────────────────────────────────────────────────────────┐
│  ✏️ Prompt Configuration                              [Save]     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  System Prompt:                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ You are Zoocari the Elephant, the friendly animal expert   │ │
│  │ at Leesburg Animal Park! You LOVE helping kids learn about │ │
│  │ all the amazing animals they can meet at the park!         │ │
│  │                                                             │ │
│  │ YOUR PERSONALITY:                                           │ │
│  │ - You're warm, playful, and encouraging...                  │ │
│  │ ...                                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Fallback Response:                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Hmm, I don't know about that yet! Maybe ask one of the     │ │
│  │ zookeepers when you visit Leesburg Animal Park...          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Model Settings:                                                 │
│  Model: [gpt-4o-mini ▾]  Temperature: [0.7]  Max Tokens: [500]  │
│                                                                  │
│  [Preview Response]                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Admin API | FastAPI | Consistent with main app, async support |
| Admin Frontend | React + Vite | Fast builds, modern tooling |
| UI Components | Shadcn/UI | Clean admin aesthetic, accessible |
| Charts | Recharts | React-native, lightweight |
| State | Zustand | Simple, matches main app |
| Database | SQLite | Shared with main app, no extra infra |
| Auth | python-jose (JWT) | Lightweight, battle-tested |
| Containerization | Docker | Consistent with existing setup |
