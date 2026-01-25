# Feedback System Design

## Overview
Add user feedback capture (thumbs up/down per response + survey form) with admin review in management app.

## Data Model

**New SQLite table: `feedback`** (in `data/sessions.db`)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT | Links to chat session |
| message_id | TEXT | Links to specific response (null for survey) |
| feedback_type | TEXT | "thumbs_up", "thumbs_down", or "survey" |
| comment | TEXT | Free-text (survey only) |
| flagged | BOOLEAN | Admin flag for follow-up |
| reviewed_at | TIMESTAMP | When admin reviewed |
| created_at | TIMESTAMP | When submitted |

---

## Implementation Phases

### Phase 1: Backend API (3 parallel subagents)

| Subagent | Task | Files |
|----------|------|-------|
| backend-1 | Feedback Models | `apps/api/app/models/feedback.py` |
| backend-2 | Feedback Service | `apps/api/app/services/feedback.py` |
| backend-3 | Feedback Router + Registration | `apps/api/app/routers/feedback.py`, `main.py` |

### Phase 2: Frontend (3 parallel subagents)

| Subagent | Task | Files |
|----------|------|-------|
| frontend-1 | Web API Client + Chat Store | `apps/web/src/lib/api.ts`, `stores/chatStore.ts` |
| frontend-2 | Chat UI (Thumbs + Modal) | `apps/web/src/components/MessageBubble.tsx`, `ChatInterface/` |
| frontend-3 | Admin API + UI | `apps/admin-api/routers/feedback.py`, `apps/admin/src/` |

### Phase 3: QA Subagent
- Run backend tests
- Run frontend build verification
- Test API endpoints manually

### Phase 4: Troubleshooting Subagent (iterative)
- Fix issues identified by QA
- Repeat QA → Troubleshoot until passing

### Phase 5: DevOps Subagent
- Update Docker configurations if needed
- Deploy to staging

### Phase 6: PM Subagent
- Update `docs/ProjectPlan.md`
- Archive feature documentation

---

## Verification Commands

### Backend API
```bash
cd apps/api && uvicorn app.main:app --reload --port 8000

# Test rating endpoint
curl -X POST http://localhost:8000/api/feedback/rating \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message_id": "msg1", "rating": "up"}'

# Test survey endpoint
curl -X POST http://localhost:8000/api/feedback/survey \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "comment": "Great experience!"}'
```

### Database Verification
```bash
sqlite3 data/sessions.db "SELECT * FROM feedback;"
```

### Frontend
```bash
cd apps/web && npm run build
cd apps/admin && npm run build
```
