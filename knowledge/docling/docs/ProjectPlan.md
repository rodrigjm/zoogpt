# Zoocari Project Plan

> **Last Updated:** 2026-03-01 (Concurrency optimization implemented — 3-track parallel: multi-worker, async I/O, smaller model)
> **Status:** Active Development
> **Branch:** ui_fix
>
> **Latest Change:** Concurrency optimization deployed & benchmarked. All 3 tracks live: gunicorn 2 workers, async I/O (async_helpers.py), qwen2.5:3b + OLLAMA_NUM_PARALLEL=2. Scaling efficiency 97-114% at 5 concurrent users. Absolute latency targets pending production hardware (MacBook CPU ~18 tok/s is bottleneck).

---

## Current Deployment

| Component | Status | Version/Notes |
|-----------|--------|---------------|
| API (FastAPI) | ✅ Running | Port 8000, Python 3.12+ |
| Web Frontend | ✅ Running | Port 3000, React/TypeScript |
| Admin Portal API | ✅ Running | Port 8001, Image Management |
| Admin Portal Web | ✅ Running | Port 3001, React/TypeScript |
| Kokoro-TTS | ✅ Healthy | Port 8880, ONNX streaming |
| Ollama (qwen2.5:3b) | ✅ Running | Port 11434, local inference |
| LlamaGuard | ✅ Active | Content safety via Ollama |
| LanceDB | ✅ Built | `data/zoo_lancedb/` |

### Infrastructure
- **Hosting:** Docker Compose (local/staging)
- **SSL:** Cloudflare Tunnel (production HTTPS)
- **Database:** LanceDB vector store for RAG

---

## Active Features (In Progress)

### 🔄 Concurrency Optimization
- **Directory:** `docs/active/concurrency-optimization/`
- **Status:** Deployed & Benchmarked — Pending Production Verification
- **Owner:** Main + Backend Agents
- **Started:** 2026-03-01

| Task | Status | Notes |
|------|--------|-------|
| Design & Brainstorming | ✅ Done | 8 options analyzed |
| Track A: Multi-Worker + Ollama Tuning | ✅ Done | Gunicorn 2 workers, WAL, parallel |
| Track B: Async I/O + Background Analytics | ✅ Done | async_helpers.py, router wrapping |
| Track C: Smaller Model (qwen2.5:3b) | ✅ Done | phi4 → qwen2.5:3b |
| Unit Tests (async_helpers) | ✅ Done | 11/11 passed |
| Deploy & Benchmark | ✅ Done | All 3 tracks deployed, 97-114% scaling efficiency |

### ⏸️ Animal Pictures in Chat (Disabled)
- **Directory:** `docs/active/animal-pictures/`
- **Status:** Disabled in UI — moved to backlog
- **Owner:** Frontend Agent
- **Started:** 2026-01-20
- **Completed:** 2026-01-24
- **Disabled:** 2026-02-22 — Images incorrect for ~60/70 animals

| Task | Status | Notes |
|------|--------|-------|
| UX Decision | ✅ Done | Collapsible Gallery (Option C) |
| Image Source Decision | ✅ Done | JSON config file |
| Implementation | ✅ Done | 4 components, 8 animals configured |
| QA & Polish | ✅ Done | Images show by default |
| **Gallery hidden in UI** | ⏸️ | Gallery components preserved, rendering commented out in MessageBubble.tsx |

### ✅ Admin Portal Image Management
- **Directory:** `docs/active/image-management/`
- **Status:** Complete
- **Owner:** Backend/Frontend Agents
- **Started:** 2026-01-24
- **Completed:** 2026-01-24

| Task | Status | Notes |
|------|--------|-------|
| Backend API | ✅ Done | 6 REST endpoints for CRUD |
| Frontend Types/API | ✅ Done | TypeScript types + imagesApi |
| Images Page | ✅ Done | Grid view with thumbnails |
| Upload Components | ✅ Done | Modal, uploader, gallery, selector |
| QA Testing | ✅ Done | TypeScript + build passing |
| Docker Deployment | ✅ Done | Both containers running |
| Image Display Fix | ✅ Done | Name normalization in RAG |
| Show Images Default | ✅ Done | Auto-expand in chat |

### ✅ Park Animal Inventory Integration
- **Directory:** `docs/active/park-inventory-integration/`
- **Status:** Complete
- **Owner:** Main + Backend/QA Agents
- **Started:** 2026-01-25
- **Completed:** 2026-01-25

| Task | Status | Notes |
|------|--------|-------|
| Build Inventory Script | ✅ Done | `scripts/build_park_inventory.py` |
| Generate JSON Data | ✅ Done | 42 species, 151 individuals |
| RAG Service Integration | ✅ Done | Lazy-loading + context enrichment |
| System Prompt Update | ✅ Done | [PARK INFO] handling instructions |
| Unit Tests | ✅ Done | 28 tests passing |
| Integration Verification | ✅ Done | Tested in Docker |

---

## Bugs & Issues

| ID | Description | Severity | Status | Related Docs |
|----|-------------|----------|--------|--------------|
| 1 | Block intrasession questions/text before audio has completed | Medium | ✅ Verified | `isAudioPlaying` state + `wasPlayingRef` transition detection. Playwright-verified: textarea disabled during TTS, re-enabled on audio end |
| 2 | Admin portal model/prompt panel not showing Ollama parameters | Low | ➡️ Backlog | Reclassified as feature enhancement — `ModelConfig` only has 3 fields, Ollama params (top_p, top_k, etc.) never implemented |
| 3 | Admin portal KB vector index not showing any animals | High | ✅ Verified | Playwright-verified: 138 animals displayed, admin container healthy. Docker health check (IPv6→IPv4), KB limit 100→200 |
---

## Completed (Recent)

| Feature | Completed | Documentation |
|---------|-----------|---------------|
| Mobile-First Chat UI Redesign | 2026-01-31 | `docs/archive/chat-redesign/` |
| KB Park Animals Expansion | 2026-01-25 | `docs/active/kb-park-animals/` |
| Park Inventory Integration | 2026-01-25 | `docs/active/park-inventory-integration/` |
| User Feedback System | 2026-01-25 | `docs/active/feedback-system/` |
| Admin Portal Image Management | 2026-01-24 | `docs/active/image-management/` |
| Animal Pictures in Chat | 2026-01-24 | `docs/active/animal-pictures/` |
| TTS Latency Optimization | 2026-01-15 | `docs/archive/TTS_OPTIMIZATION_IMPLEMENTATION.md` |
| Ollama Integration (Phi-4 + LlamaGuard) | 2026-01-15 | `docs/archive/` |
| Local Voice Inference | 2026-01-15 | `docs/archive/` |
| Admin Portal Design | 2026-01-XX | `docs/archive/admin-portal/` |

---

## Roadmap

### Q1 2026
- [x] add picture slideshow of animals in question → **Complete:** `docs/active/animal-pictures/`
- [x] Admin portal image management → **Complete:** `docs/active/image-management/`
- [x] add personalized information for each animal → **Complete:** `docs/active/park-inventory-integration/`
- [x] Thumbs up/down on answers provided → **Complete:** `docs/active/feedback-system/`
- [ ] Multi-language support → **Moved to Backlog:** `docs/active/multilingual-support/`
- [x] Mobile-first chat UI redesign → **Complete:** `docs/archive/chat-redesign/`
- [ ] admin app - Analytics dashboard - ability to review per model performance & ability to change ollama models (with ollama endpoint instantiaion and retireing old model)
- [x] feedback text/record button for additional feedback on experience → **Complete:** `docs/active/feedback-system/`
- [ ] local ollama hosted embedding model

### Q2 2026
- [ ] Mobile app companion
- [ ] Offline mode support

### Backlog
- [ ] **Multi-Lingual Support (English/Spanish)** - Planning complete, design doc at `docs/active/multilingual-support/design.md`. 6-phase implementation: API contracts → Voice/RAG/Frontend (parallel) → KB/Safety → QA → Deploy. ~35-45 files affected.
- [ ] **Admin Portal Ollama Parameters** - Add Ollama-specific model params (top_p, top_k, repeat_penalty, etc.) to admin config panel. Requires updates across ModelConfig (Python + TypeScript), admin UI, and LLM/RAG services. ~7 files.
- [ ] **Animal Image Gallery — Fix Image Sourcing** - Gallery components preserved in codebase (`AnimalImageGallery`, `AnimalImage`, `ImageLightbox`, `ImageSkeleton`), disabled in UI pending correct image sourcing for ~60/70 animals. Re-enable by uncommenting gallery block in `MessageBubble.tsx`.
- [ ] **AI Feedback Synthesis & ClickUp Integration** - Use LLM/OpenAI to analyze customer feedback table, synthesize into actionable feature proposals with: reason, market fit, customer experience impact. Auto-post to ClickUp via MCP capabilities for product backlog management.
- [ ] Voice personality customization
- [ ] Parent dashboard
- [ ] Usage analytics API


---

## Documentation Index

| Category | Location | Purpose |
|----------|----------|---------|
| **Active Work** | `docs/active/<feature>/` | Ongoing feature development |
| **Archive** | `docs/archive/` | Completed feature documentation |
| **Design** | `docs/design/` | Architecture & design specs |
| **Integration** | `docs/integration/` | Cross-system contracts |
| **Ops** | `docs/` (root) | Deployment, quickstart, architecture |

---

## Quick Links

- [Architecture Overview](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Quick Start](./QUICK_START.md)
- [Cloudflare Tunnel Setup](./CLOUDFLARE_TUNNEL_SETUP.md)
