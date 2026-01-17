# Zoocari Project Plan

> **Last Updated:** 2026-01-17
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

### 🔄 [Feature Name]
- **Directory:** `docs/active/<feature-name>/`
- **Status:** Phase X of Y
- **Owner:** [Agent/Team]
- **Started:** YYYY-MM-DD

| Task | Status | Notes |
|------|--------|-------|
| Research/Design | ⬜ | |
| Implementation | ⬜ | |
| QA Validation | ⬜ | |
| Deployment | ⬜ | |

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
- [ ] add picture slideshow of animals in question - maybe of park animals
- [ ] Multi-language support
- [ ] Analytics dashboard

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
