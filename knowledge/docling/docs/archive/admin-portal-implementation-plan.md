# Admin Portal Implementation Plan

## Phase 1: Foundation & Analytics Collection

### 1.1 Extend SQLite Schema
**Files to create/modify:**
- `apps/api/app/models/analytics.py` - Pydantic models for analytics
- `apps/api/app/services/analytics.py` - Analytics service for recording/querying

**Tasks:**
1. Create analytics tables in sessions.db (chat_interactions, session_metrics, daily_analytics)
2. Add Pydantic models for analytics data
3. Create AnalyticsService class with record/query methods

### 1.2 Instrument Main App
**Files to modify:**
- `apps/api/app/routers/chat.py` - Add timing and analytics recording
- `apps/api/app/routers/voice.py` - Add TTS timing recording
- `apps/api/app/utils/timing.py` - Enhance with context manager

**Tasks:**
1. Create timing context manager for component-level latency tracking
2. Call analytics service after each chat/voice response
3. Record RAG, LLM, TTS latency separately

### 1.3 Create Admin API Project Structure
**Files to create:**
```
apps/admin-api/
├── main.py
├── config.py
├── requirements.txt
├── routers/
│   ├── __init__.py
│   ├── analytics.py
│   ├── kb.py
│   └── config.py
├── services/
│   ├── __init__.py
│   ├── analytics.py
│   ├── kb.py
│   └── indexer.py
├── models/
│   ├── __init__.py
│   ├── analytics.py
│   ├── kb.py
│   └── config.py
└── auth/
    ├── __init__.py
    └── basic.py
```

---

## Phase 2: Analytics API & Dashboard

### 2.1 Analytics API Endpoints
**File:** `apps/admin-api/routers/analytics.py`

**Endpoints:**
- `GET /api/admin/analytics/dashboard` - Summary metrics
- `GET /api/admin/analytics/sessions` - Session list with filters
- `GET /api/admin/analytics/sessions/{id}/interactions` - Q&A pairs
- `GET /api/admin/analytics/interactions` - Search all Q&A
- `GET /api/admin/analytics/latency-breakdown` - Component timing

### 2.2 Admin Frontend Setup
**Files to create:**
```
apps/admin/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts
│   ├── components/
│   │   └── Layout/
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   └── pages/
│       └── Dashboard.tsx
```

**Tasks:**
1. Initialize Vite + React + TypeScript project
2. Install dependencies: react-router, zustand, recharts, tailwindcss
3. Create basic layout with sidebar navigation
4. Set up API client with auth headers

### 2.3 Dashboard Components
**Files to create:**
- `apps/admin/src/components/Analytics/MetricCards.tsx`
- `apps/admin/src/components/Analytics/TrendsChart.tsx`
- `apps/admin/src/components/Analytics/LatencyChart.tsx`
- `apps/admin/src/components/Analytics/TopQuestions.tsx`
- `apps/admin/src/pages/Dashboard.tsx`

---

## Phase 3: Knowledge Base Management

### 3.1 KB Database Schema
**File:** `apps/admin-api/services/kb.py`

**Tasks:**
1. Create kb_animals, kb_sources, kb_index_history tables
2. Implement CRUD operations for animals
3. Implement CRUD operations for sources
4. Create index rebuild job system

### 3.2 KB API Endpoints
**File:** `apps/admin-api/routers/kb.py`

**Endpoints:**
- `GET /api/admin/kb/animals` - List animals
- `POST /api/admin/kb/animals` - Create animal
- `GET /api/admin/kb/animals/{id}` - Get animal with sources
- `PUT /api/admin/kb/animals/{id}` - Update animal
- `DELETE /api/admin/kb/animals/{id}` - Delete animal
- `POST /api/admin/kb/animals/{id}/sources` - Add source
- `DELETE /api/admin/kb/animals/{id}/sources/{sid}` - Remove source
- `POST /api/admin/kb/index/rebuild` - Trigger rebuild
- `GET /api/admin/kb/index/status` - Get index status

### 3.3 Vector Index Rebuilder
**File:** `apps/admin-api/services/indexer.py`

**Tasks:**
1. Read sources from SQLite
2. Chunk text using existing logic
3. Generate embeddings via OpenAI
4. Write to LanceDB
5. Track progress in kb_index_history

### 3.4 KB Frontend Components
**Files to create:**
- `apps/admin/src/pages/KnowledgeBase.tsx`
- `apps/admin/src/components/KB/AnimalList.tsx`
- `apps/admin/src/components/KB/AnimalEditor.tsx`
- `apps/admin/src/components/KB/SourceEditor.tsx`
- `apps/admin/src/components/KB/IndexStatus.tsx`

---

## Phase 4: Configuration Management

### 4.1 Config File Structure
**File to create:** `data/admin_config.json`

Initial content with defaults from current codebase.

### 4.2 Config API Endpoints
**File:** `apps/admin-api/routers/config.py`

**Endpoints:**
- `GET /api/admin/config/prompts` - Get prompts
- `PUT /api/admin/config/prompts` - Update prompts
- `GET /api/admin/config/model` - Get LLM settings
- `PUT /api/admin/config/model` - Update LLM settings
- `GET /api/admin/config/tts` - Get TTS settings
- `PUT /api/admin/config/tts` - Update TTS settings
- `POST /api/admin/config/tts/preview` - Generate preview audio

### 4.3 Hot-Reload in Main App
**File to modify:** `apps/api/app/config.py`

**Tasks:**
1. Create DynamicConfig class that watches admin_config.json
2. Reload on file modification
3. Expose properties for prompts, model settings, TTS settings

### 4.4 Config Frontend Components
**Files to create:**
- `apps/admin/src/pages/Configuration.tsx`
- `apps/admin/src/components/Config/PromptEditor.tsx`
- `apps/admin/src/components/Config/ModelSettings.tsx`
- `apps/admin/src/components/Config/VoiceSettings.tsx`
- `apps/admin/src/components/Config/AudioPreview.tsx`

---

## Phase 5: Authentication & Docker

### 5.1 Basic Authentication
**File:** `apps/admin-api/auth/basic.py`

**Tasks:**
1. Implement HTTP Basic Auth dependency
2. Validate against env vars (ADMIN_USERNAME, ADMIN_PASSWORD)
3. Issue JWT tokens for session management
4. Add auth middleware to all admin routes

### 5.2 Docker Configuration
**Files to create/modify:**
- `Dockerfile.admin` - Multi-stage build for admin portal
- `docker-compose.yml` - Add admin-portal service

### 5.3 Frontend Auth
**Files to create:**
- `apps/admin/src/pages/Login.tsx`
- `apps/admin/src/stores/authStore.ts`
- `apps/admin/src/components/ProtectedRoute.tsx`

---

## Implementation Order

```
Week 1:
├── Phase 1.1: SQLite schema extension
├── Phase 1.2: Main app instrumentation
└── Phase 1.3: Admin API project structure

Week 2:
├── Phase 2.1: Analytics API endpoints
├── Phase 2.2: Admin frontend setup
└── Phase 2.3: Dashboard components

Week 3:
├── Phase 3.1: KB database schema
├── Phase 3.2: KB API endpoints
└── Phase 3.3: Vector index rebuilder

Week 4:
├── Phase 3.4: KB frontend components
├── Phase 4.1: Config file structure
└── Phase 4.2: Config API endpoints

Week 5:
├── Phase 4.3: Hot-reload in main app
├── Phase 4.4: Config frontend components
└── Phase 5.1: Basic authentication

Week 6:
├── Phase 5.2: Docker configuration
├── Phase 5.3: Frontend auth
└── Testing & polish
```

---

## Immediate Next Steps

Start with **Phase 1.1** - extending the SQLite schema:

1. Create `apps/api/app/models/analytics.py`
2. Create `apps/api/app/services/analytics.py`
3. Add schema initialization to app startup
4. Test with manual inserts

Ready to begin?
