# Subagent Registry

Per CONTRACT.md Part 1, these are the available subagents and their scopes:

| Agent | Domain | Scope | Primary Artifacts |
|-------|--------|-------|-------------------|
| **frontend** | React UI, Zustand, hooks | `apps/web/**` | Components, stores, types |
| **backend** | FastAPI, Pydantic | `apps/api/**` | Routers, models, services |
| **rag** | LanceDB, retrieval | `apps/api/app/services/rag.py` | RAG pipeline, embeddings |
| **sessiondb** | SQLite, sessions | Session service/router/model | Schema, migrations |
| **voice** | STT/TTS endpoints + audio | Voice router/services + FE hooks | Audio pipeline |
| **qa** | Vitest, Playwright | `**/tests/**` | Unit, e2e, smoke tests |
| **devops** | Docker, compose | `docker/**` | Containers, volumes |
| **troubleshoot** | Logs, errors | Read-only + STATUS.md | Diagnosis, minimal fixes |

## Boundary Rules (Hard)
- **frontend** NEVER writes to `apps/api/**`
- **backend** NEVER writes to `apps/web/**`
- **rag/sessiondb/voice** stay within their declared file scope
- **qa** does NOT fix product code—only reports issues
- **troubleshoot** is read-only unless explicitly authorized
- **devops** does NOT modify feature logic

## When to Delegate

| Situation | Delegate To |
|-----------|-------------|
| Implement React component/hook | `frontend` |
| Implement FastAPI endpoint | `backend` |
| Modify RAG retrieval logic | `rag` |
| Session schema/persistence | `sessiondb` |
| Audio capture/playback issues | `voice` |
| Write or fix tests | `qa` |
| Docker/compose issues | `devops` |
| Diagnose failing logs/tests | `troubleshoot` |

## Collaboration Model
- Subagents collaborate ONLY through shared artifacts:
  - `docs/integration/CONTRACT.md`
  - `docs/integration/STATUS.md`
  - shared types and integration tests
- Subagents must NOT negotiate behavior in chat
- If behavior is unclear, write a question to STATUS.md
