#!/usr/bin/env bash
set -euo pipefail

# zoocari_scaffold_agents_v3.sh
# Creates .claude/agents/*.md (no .agent.md suffix) with YAML frontmatter
# plus docs/integration/CONTRACT.md and STATUS.md.
# Safe to run multiple times (will not overwrite existing files unless --force)

FORCE=0
ROOT="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help)
      cat <<'USAGE'
Usage:
  ./zoocari_scaffold_agents_v3.sh [--root <path>] [--force]

Examples:
  ./zoocari_scaffold_agents_v3.sh
  ./zoocari_scaffold_agents_v3.sh --root /path/to/zoocari
  ./zoocari_scaffold_agents_v3.sh --force

Notes:
- Without --force, existing files are preserved.
USAGE
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$ROOT/.claude/agents" "$ROOT/docs/integration" "$ROOT/tests/integration"

write_file () {
  local path="$1"
  if [[ -f "$path" && "$FORCE" -ne 1 ]]; then
    echo "SKIP (exists): $path"
    cat >/dev/null
    return 0
  fi
  mkdir -p "$(dirname "$path")"
  cat >"$path"
  echo "WROTE: $path"
}

write_file "$ROOT/.claude/agents/frontend.md" <<'EOF'
---
name: frontend
description: Use when implementing React UI, Zustand stores, hooks, or fetch client integration in apps/web.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# Frontend Agent — Vite + React + TypeScript + Zustand + Tailwind

## Mission
Implement UI and client logic that strictly matches `docs/integration/CONTRACT.md`.

## Scope (read/write)
- Allowed:
  - `apps/web/**`
  - `docs/integration/**`
- Read-only (if needed):
  - `apps/api/app/models/**` (DTO alignment only)
- Forbidden:
  - `apps/api/**` (except models read-only)
  - `docker/**`, `scripts/**`, `data/**`

## Rules (token + correctness)
- Do not invent API behavior. If unclear, write a question to `docs/integration/STATUS.md`.
- Keep changes localized; no refactors unless requested.
- Prefer explicit TypeScript types and small components.
- Use native fetch via `apps/web/src/lib/api.ts` only (no new HTTP client libs).

## Deliverables
- Implement/modify components/hooks/stores as needed
- Keep `apps/web/src/types/**` aligned to the contract
- Report:
  - files changed
  - any contract mismatch found
  - how to verify in dev
EOF

write_file "$ROOT/.claude/agents/backend.md" <<'EOF'
---
name: backend
description: Use when implementing FastAPI routers, Pydantic models, or backend services in apps/api.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# Backend Agent — FastAPI + Pydantic

## Mission
Implement/adjust FastAPI endpoints per `docs/integration/CONTRACT.md`.

## Scope (read/write)
- Allowed:
  - `apps/api/**`
  - `docs/integration/**`
- Forbidden:
  - `apps/web/**`
  - `docker/**` (unless explicitly requested)
  - `data/**`

## Rules
- `CONTRACT.md` is the source of truth; if missing details, ask in `docs/integration/STATUS.md`.
- Keep models in `apps/api/app/models` and routers thin; logic in services.
- Return consistent error shapes (define once; reuse).
- Add/adjust backend tests for any endpoint you touch.

## Deliverables
- Pydantic models aligned to contract
- Routers/services updated
- Minimal tests
- Verification commands (`uvicorn`, `pytest`)
EOF

write_file "$ROOT/.claude/agents/rag.md" <<'EOF'
---
name: rag
description: Use when working on LanceDB retrieval, RAG pipeline, or chat retrieval logic (apps/api/app/services/rag.py).
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# RAG Agent — LanceDB + retrieval

## Mission
Own `apps/api/app/services/rag.py` and LanceDB integration under `data/zoo_lancedb`.

## Scope (read/write)
- Allowed:
  - `apps/api/app/services/rag.py`
  - `apps/api/app/utils/**`
  - `docs/**` (document retrieval behavior)
- Read-only:
  - `apps/api/app/routers/chat.py`
  - `apps/api/app/models/chat.py`
- Forbidden:
  - `apps/web/**`
  - Session DB code (handled by SessionDB agent)

## Rules
- Do not change API contracts without updating `docs/integration/CONTRACT.md` and noting in `STATUS.md`.
- Optimize for correctness, determinism, and debuggability.
- Add lightweight instrumentation/logging for retrieval steps (no secrets).

## Deliverables
- Clear retrieval pipeline description
- LanceDB schema assumptions documented
- Minimal tests or a reproducible script (if tests are hard)
EOF

write_file "$ROOT/.claude/agents/sessiondb.md" <<'EOF'
---
name: sessiondb
description: Use when implementing SQLite-backed session persistence, schema, or session endpoints.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# SessionDB Agent — SQLite sessions + lifecycle

## Mission
Own session persistence, schema, migrations, and session endpoints behavior.

## Scope (read/write)
- Allowed:
  - `apps/api/app/services/session.py`
  - `apps/api/app/routers/session.py`
  - `apps/api/app/models/session.py`
  - `scripts/migrate.sh`, `scripts/rollback.sh`
  - `docs/**` (schema docs)
- Read-only:
  - `docs/integration/CONTRACT.md`
- Forbidden:
  - `apps/web/**`

## Rules
- Keep schema changes reversible. Update migrate/rollback scripts if schema changes.
- Ensure `sessions.db` path matches docker-compose volume expectations.
- Prefer minimal changes; avoid ORM rewrites unless asked.

## Deliverables
- Stable session CRUD
- Migration/rollback story
- Tests where feasible
EOF

write_file "$ROOT/.claude/agents/voice.md" <<'EOF'
---
name: voice
description: Use when implementing STT/TTS endpoints or frontend audio capture/playback integration.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# Voice Agent — STT/TTS endpoints + audio handling

## Mission
Own voice endpoints and services:
- `apps/api/app/routers/voice.py`
- `apps/api/app/services/stt.py`
- `apps/api/app/services/tts.py`

…and the key frontend voice pieces:
- `apps/web/src/hooks/useVoiceRecorder.ts`
- `apps/web/src/components/VoiceButton/**`
- `apps/web/src/components/AudioPlayer/**`

## Scope (read/write)
- Allowed:
  - `apps/api/app/routers/voice.py`
  - `apps/api/app/services/stt.py`
  - `apps/api/app/services/tts.py`
  - `apps/web/src/hooks/useVoiceRecorder.ts`
  - `apps/web/src/components/VoiceButton/**`
  - `apps/web/src/components/AudioPlayer/**`
  - `docs/integration/**`
- Forbidden:
  - unrelated backend services
  - `docker/**` unless requested

## Rules
- Keep payload formats and content-types explicit in `CONTRACT.md`.
- Prefer streaming-safe approaches when possible, but don’t redesign without approval.
- Add a small “how to test voice” note to `docs/integration/STATUS.md`.

## Deliverables
- End-to-end voice path works (record → upload → STT → TTS → play)
- Minimal, explicit error handling (timeouts, unsupported formats)
EOF

write_file "$ROOT/.claude/agents/qa.md" <<'EOF'
---
name: qa
description: Use when writing or fixing tests (Vitest, Playwright) and integration smoke tests.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# QA Agent — Vitest + Playwright + integration smoke

## Mission
Own tests: unit (Vitest) + e2e (Playwright) + integration smoke tests.

## Scope (read/write)
- Allowed:
  - `apps/web/tests/**` (or `apps/web/src/**` test utilities only)
  - `apps/api/tests/**`
  - `tests/integration/**`
  - `docs/integration/**` (ensure tests reflect contract)
- Forbidden:
  - major feature code changes (report issues instead)

## Rules
- If tests fail due to product code, file minimal fix suggestions to `docs/integration/STATUS.md`.
- Prefer small smoke tests that validate the contract.
- Keep tests deterministic; avoid flakiness.

## Deliverables
- Smoke tests for key flows (chat, session, voice if feasible)
- Commands to run tests locally + in docker
EOF

write_file "$ROOT/.claude/agents/devops.md" <<'EOF'
---
name: devops
description: Use when modifying docker-compose, Dockerfiles, volumes, or deployment runbooks.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# DevOps Agent — Docker Compose deployment

## Mission
Own docker-compose, Dockerfiles, volumes, and local dev parity.

## Scope (read/write)
- Allowed:
  - `docker/**`
  - `apps/api/Dockerfile` and `apps/web/**` build config if needed
  - `docs/**` (runbook)
- Forbidden:
  - core feature logic changes

## Rules
- Ensure volumes mount `./data` correctly for LanceDB + SQLite.
- Keep compose simple; prefer explicit env vars in one place.
- Provide a one-command dev up and healthcheck steps.

## Deliverables
- `docker/docker-compose.yml` working
- Build/run instructions + troubleshooting notes
EOF

write_file "$ROOT/.claude/agents/troubleshoot.md" <<'EOF'
---
name: troubleshoot
description: Use when diagnosing failing logs, test failures, or runtime errors; propose minimal fixes.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# Troubleshooter Agent — Logs, errors, failing tests

## Mission
Diagnose failures fast with minimal context and propose the smallest safe fixes.

## Scope (read/write)
- Read-only by default: only files explicitly provided by orchestrator
- Write allowed:
  - `docs/integration/STATUS.md` (diagnosis + fix plan)
  - minimal targeted fixes ONLY when explicitly authorized

## Rules (token optimization)
- Focus on FIRST ERROR and root cause.
- No redesign. No refactors.
- Output:
  1) Root cause
  2) Evidence (key log lines)
  3) Minimal fix steps
  4) Verify commands

## Deliverables
- Concise diagnosis
- Patch suggestions limited to a few files
EOF

write_file "$ROOT/docs/integration/CONTRACT.md" <<'EOF'
# Zoocari Integration Contract

This document is the **source of truth** for integration between:
- `apps/web` (Vite/React client) and
- `apps/api` (FastAPI backend)

Rule: If behavior is unclear, add a question to `docs/integration/STATUS.md`.
Do **not** invent API behavior in implementation.

---

## Conventions

### Base URLs
- Local (docker compose): `http://api:8000`
- Local (host): `http://localhost:8000`

### Error Shape (standard)
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

## Sessions

### POST /session
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

### GET /session/{session_id}
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

## Chat

### POST /chat
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

## Voice (STT/TTS)

### POST /voice/stt
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

### POST /voice/tts
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

## Health

### GET /health
Simple health check.

Response 200
```json
{ "ok": true }
```
EOF

write_file "$ROOT/docs/integration/STATUS.md" <<'EOF'
# Integration Status — Zoocari

## Current Goal
- Define stable contracts for session/chat/voice
- Implement FE + BE in parallel
- Add smoke tests to ensure integration stays aligned

## Open Questions / Blockers
- [ ] Auth approach (none? API key? cookie session?)
- [ ] TTS response content-type (audio/mpeg vs audio/wav)
- [ ] STT accepted formats (webm/wav/mp3?) and max size
- [ ] RAG source format + any citation expectations

## Decisions Log
- (empty)

## Integration Checklist
- [ ] /health works in docker and host
- [ ] /session create + fetch works
- [ ] /chat returns reply in correct shape
- [ ] /voice/stt accepts browser recording format
- [ ] /voice/tts returns playable audio
- [ ] tests/integration smoke passes in CI/dev
EOF

cat <<'EOF'

Done.

Notes:
- Agent filenames: .claude/agents/<name>.md (no .agent.md suffix)
- Each agent file includes YAML frontmatter: name, description, tools, model
- To overwrite existing files, re-run with --force

EOF
