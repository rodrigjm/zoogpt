# Zoocari Project Plan

> **Last Updated:** 2026-01-25 (KB Park Animals Expansion Complete)
> **Status:** Active Development
> **Branch:** feature/node-fastapi-migration

---

## Current Deployment

| Component | Status | Version/Notes |
|-----------|--------|---------------|
| API (FastAPI) | ✅ Running | Port 8000, Python 3.12+ |
| Web Frontend | ✅ Running | Port 3000, React/TypeScript |
| Admin Portal API | ✅ Running | Port 8001, Image Management |
| Admin Portal Web | ✅ Running | Port 3001, React/TypeScript |
| Kokoro-TTS | ✅ Healthy | Port 8880, ONNX streaming |
| Ollama (Phi-4) | ✅ Running | Port 11434, local inference |
| LlamaGuard | ✅ Active | Content safety via Ollama |
| LanceDB | ✅ Built | `data/zoo_lancedb/` |

### Infrastructure
- **Hosting:** Docker Compose (local/staging)
- **SSL:** Cloudflare Tunnel (production HTTPS)
- **Database:** LanceDB vector store for RAG

---

## Active Features (In Progress)

### 🔄 Multi-Lingual Support (English/Spanish)
- **Directory:** `docs/active/multilingual-support/`
- **Status:** Phase 0 of 6 (Planning Complete)
- **Owner:** TBD
- **Started:** 2026-01-20

| Task | Status | Notes |
|------|--------|-------|
| Design & Planning | ✅ | [design.md](./active/multilingual-support/design.md) |
| Phase 1: API Contracts | ⬜ | Foundation for all phases |
| Phase 2-4: Voice/RAG/Frontend | ⬜ | Parallel execution |
| Phase 5-6: KB/Safety | ⬜ | Sequential |
| QA Validation | ⬜ | |
| Deployment | ⬜ | |

### ✅ Animal Pictures in Chat
- **Directory:** `docs/active/animal-pictures/`
- **Status:** Complete
- **Owner:** Frontend Agent
- **Started:** 2026-01-20
- **Completed:** 2026-01-24

| Task | Status | Notes |
|------|--------|-------|
| UX Decision | ✅ Done | Collapsible Gallery (Option C) |
| Image Source Decision | ✅ Done | JSON config file |
| Implementation | ✅ Done | 4 components, 8 animals configured |
| QA & Polish | ✅ Done | Images show by default |

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
| 1 | block intrasession questions/text before audio has completed | - | - | - |
| 2 | admin portal model or prompt panel not showing ollama parameters | - | - | - |
| 3 | admin portal KB vector index not showing any animals | - | - | - |
---

## Completed (Recent)

| Feature | Completed | Documentation |
|---------|-----------|---------------|
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
- [x] Multi-language support → **Active:** `docs/active/multilingual-support/`
- [ ] admin app - Analytics dashboard - ability to review per model performance & ability to change ollama models (with ollama endpoint instantiaion and retireing old model)
- [x] feedback text/record button for additional feedback on experience → **Complete:** `docs/active/feedback-system/`
- [ ] local ollama hosted embedding model

### Q2 2026
- [ ] Mobile app companion
- [ ] Offline mode support

### Backlog
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
