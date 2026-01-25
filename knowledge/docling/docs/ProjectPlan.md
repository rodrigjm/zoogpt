# Zoocari Project Plan

> **Last Updated:** 2026-01-24
> **Status:** Active Development
> **Branch:** feature/node-fastapi-migration

---

## Current Deployment

| Component | Status | Version/Notes |
|-----------|--------|---------------|
| API (FastAPI) | ✅ Running | Port 8000, Python 3.12+ |
| Web Frontend | ✅ Running | Port 3000, React/TypeScript |
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
- **Status:** Implementation Complete - Ready for Testing
- **Owner:** Frontend Agent
- **Started:** 2026-01-20
- **Completed:** 2026-01-24

| Task | Status | Notes |
|------|--------|-------|
| UX Decision | ✅ Done | Collapsible Gallery (Option C) |
| Image Source Decision | ✅ Done | JSON config file |
| Implementation | ✅ Done | 4 components, 8 animals configured |
| QA & Polish | ⬜ Pending | Manual testing needed |

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
| TTS Latency Optimization | 2026-01-15 | `docs/archive/TTS_OPTIMIZATION_IMPLEMENTATION.md` |
| Ollama Integration (Phi-4 + LlamaGuard) | 2026-01-15 | `docs/archive/` |
| Local Voice Inference | 2026-01-15 | `docs/archive/` |
| Admin Portal Design | 2026-01-XX | `docs/archive/admin-portal/` |

---

## Roadmap

### Q1 2026
- [x] add picture slideshow of animals in question → **Active:** `docs/active/animal-pictures/`
- [ ] add personalized information for each animal - same vector or seperate pass?
- [ ] Thumbs up/down on answers provided
- [x] Multi-language support → **Active:** `docs/active/multilingual-support/`
- [ ] admin app - Analytics dashboard - ability to review per model performance & ability to change ollama models (with ollama endpoint instantiaion and retireing old model)
- [ ] feedback text/record button for additional feedback on experience
- [ ] local ollama hosted embedding model

### Q2 2026
- [ ] Mobile app companion
- [ ] Offline mode support

### Backlog
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
