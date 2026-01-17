# Zoocari Integration Contract

This document is the **source of truth** for:
1. API contracts between frontend and backend
2. Subagent collaboration protocols
3. Delegation and reporting standards

**Rule:** If behavior is unclear, add a question to `docs/integration/STATUS.md`.
Do **not** invent API behavior in implementation.

---

## Part 1: Subagent Collaboration Protocol

### Orchestrator Authority
The main session agent (orchestrator) has **final decision authority** over:
- Which subagent to invoke
- When to approve/reject subagent proposals
- Cross-domain integration decisions
- CONTRACT.md and STATUS.md modifications

Subagents **propose**; the orchestrator **decides**.

### Subagent Registry

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

### Boundary Rules (Hard)

```
┌─────────────┐     ┌─────────────┐
│  frontend   │◄───►│  CONTRACT   │◄───►│  backend    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   ▲                   │
       │                   │                   │
       ▼                   │                   ▼
  apps/web/**         (source of          apps/api/**
                       truth)
```

- **frontend** NEVER writes to `apps/api/**`
- **backend** NEVER writes to `apps/web/**`
- **rag/sessiondb/voice** stay within their declared file scope
- **qa** does NOT fix product code—only reports issues
- **troubleshoot** is read-only unless explicitly authorized
- **devops** does NOT modify feature logic

### Cross-Domain Coordination
When a task spans multiple domains:
1. Orchestrator breaks task into domain-specific subtasks
2. Each subagent works within its scope
3. Integration happens via CONTRACT.md types/shapes
4. Orchestrator validates integration points

---

## Part 2: Delegation Protocol

### When Orchestrator Should Delegate

| Situation | Delegate To |
|-----------|-------------|
| Implement React component/hook | `frontend` |
| Implement FastAPI endpoint | `backend` |
| Modify RAG retrieval logic | `rag` |
| Session schema/persistence changes | `sessiondb` |
| Audio capture/playback issues | `voice` |
| Write or fix tests | `qa` |
| Docker/compose issues | `devops` |
| Diagnose failing logs/tests | `troubleshoot` |

### Delegation Message Format

When delegating, orchestrator provides:

```
## Task
[One-sentence goal]

## Context
- Relevant CONTRACT.md section (if any)
- Related files to read (max 3)
- Constraints or decisions already made

## Expected Deliverables
- [ ] Specific output 1
- [ ] Specific output 2

## Do NOT
- [Explicit boundaries]
```

### Subagent Report Format (Required)

Every subagent MUST return:

```
## Summary
[1-3 bullets: what was done]

## Files Changed
- `path/to/file1.ts` — description
- `path/to/file2.py` — description

## Contract Impact
- None | Updated CONTRACT.md section X | Question added to STATUS.md

## Verification
```bash
# Command to verify the change
```

## Issues Found (if any)
- Issue 1 → Proposed resolution
```

**Anti-patterns (DO NOT return):**
- Raw logs or stack traces (summarize instead)
- Large code dumps (reference file paths)
- Exploratory reasoning (only conclusions)
- Re-explanation of context already provided

---

## Part 3: Shared Artifacts

### CONTRACT.md (this file)
- **Purpose:** API shapes, types, collaboration rules
- **Writers:** Orchestrator primarily; subagents may propose edits
- **Readers:** All agents

### STATUS.md
- **Purpose:** Questions, blockers, decisions, checklist
- **Writers:** Any agent may add questions/findings
- **Readers:** All agents
- **Format:**
  - `## Open Questions / Blockers` — unresolved items
  - `## Decisions Log` — resolved items with rationale
  - `## Integration Checklist` — done/not-done tracking

### Shared Types
- Backend: `apps/api/app/models/**`
- Frontend: `apps/web/src/types/**`
- Must stay aligned to CONTRACT.md Part 4

---

## Part 4: API Contracts

### Conventions

#### Base URLs
- Local (docker compose): `http://api:8000`
- Local (host): `http://localhost:8000`

#### Error Shape (standard)
All non-2xx responses should use this JSON shape:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

---

### Sessions

#### POST /session
Create a new session.

Request
```json
{
  "client": "web",
  "metadata": {}
}
```

Response 200
```json
{
  "session_id": "uuid-or-string",
  "created_at": "iso-8601"
}
```

#### GET /session/{session_id}
Fetch session info.

Response 200
```json
{
  "session_id": "string",
  "created_at": "iso-8601",
  "metadata": {}
}
```

---

### Chat

#### POST /chat
Send a chat message for a given session.

Request
```json
{
  "session_id": "string",
  "message": "string",
  "mode": "rag",
  "metadata": {}
}
```

Response 200
```json
{
  "session_id": "string",
  "message_id": "string",
  "reply": "string",
  "sources": [],
  "created_at": "iso-8601"
}
```

---

### Voice (STT/TTS)

#### POST /voice/stt
Speech-to-text.

Request
- Content-Type: `multipart/form-data`
- Fields:
  - `session_id`: string
  - `audio`: file (recommended: webm/wav)

Response 200
```json
{
  "session_id": "string",
  "text": "string"
}
```

#### POST /voice/tts
Text-to-speech.

Request
```json
{
  "session_id": "string",
  "text": "string",
  "voice": "default"
}
```

Response 200
- Content-Type: `audio/mpeg` or `audio/wav` (pick one and document)
- Body: audio bytes

---

### Health

#### GET /health
Simple health check.

Response 200
```json
{ "ok": true }
```

---

## Part 5: Orchestrator Checklist

Before delegating:
- [ ] Task fits within one subagent's scope
- [ ] Provided CONTRACT.md section reference (if API-related)
- [ ] Listed expected deliverables explicitly
- [ ] Set clear boundaries (what NOT to do)

After subagent returns:
- [ ] Summary is concise (≤5 bullets)
- [ ] Files changed are listed
- [ ] Verification command provided
- [ ] No raw logs or code dumps in response
- [ ] CONTRACT.md updated if shapes changed
- [ ] STATUS.md updated if questions arose

---

## Part 6: Escalation Protocol

### When Subagents Should Escalate to Orchestrator

1. **Scope conflict** — Task requires writing outside allowed scope
2. **Contract ambiguity** — API shape unclear, need decision
3. **Cross-domain dependency** — Change requires another agent's domain
4. **Breaking change** — Proposal would alter existing contract
5. **Authorization needed** — troubleshoot agent needs write permission

### Escalation Format

```
## Escalation: [type]

**Issue:** [one sentence]

**Options:**
1. Option A — tradeoffs
2. Option B — tradeoffs

**Recommendation:** Option X because [reason]

**Blocked until:** Orchestrator decision
```

Subagent STOPS work on blocked item until orchestrator responds.
