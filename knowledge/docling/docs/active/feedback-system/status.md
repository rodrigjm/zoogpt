# Feedback System - Status

> **Last Updated:** 2026-01-25
> **Phase:** Complete
> **Status:** ✅ All Phases Done

## Progress Tracker

### Phase 1: Backend API
| Task | Subagent | Status | Notes |
|------|----------|--------|-------|
| Feedback Models | backend-1 | ✅ Done | `apps/api/app/models/feedback.py` |
| Feedback Service | backend-2 | ✅ Done | `apps/api/app/services/feedback.py` |
| Feedback Router | backend-3 | ✅ Done | `apps/api/app/routers/feedback.py`, router registered |

### Phase 2: Frontend
| Task | Subagent | Status | Notes |
|------|----------|--------|-------|
| Web API + Store | frontend-1 | ✅ Done | Added types and API functions |
| Chat UI Components | frontend-2 | ✅ Done | Thumbs + Modal implemented |
| Admin API + UI | frontend-3 | ✅ Done | Dashboard, Table, Page, Navigation |

### Phase 3-6: QA / Troubleshoot / DevOps / PM
| Phase | Status | Notes |
|-------|--------|-------|
| QA | ✅ Passed | All builds successful, see qa-report.md |
| Troubleshooting | ⏭️ Skipped | No issues to fix |
| DevOps | ✅ Done | Deployed via docker-compose rebuild |
| PM Documentation | ✅ Done | ProjectPlan.md updated |

## Files Changed
- `apps/web/src/types/index.ts` - Added feedback types
- `apps/web/src/lib/api.ts` - Added submitRating and submitSurvey functions
- `apps/web/src/components/MessageBubble.tsx` - Added thumbs up/down with state management
- `apps/web/src/components/ChatInterface/index.tsx` - Added feedback modal and "Share your thoughts" link

## Deployment (2026-01-25)
- Rebuilt containers: `api`, `admin-api`, `web`, `admin-web`
- Containers healthy and running
- Main API endpoints verified: `/api/feedback/survey`, `/api/feedback/rating`
- Admin API endpoints registered: `/api/admin/feedback/stats`, `/api/admin/feedback/list`
- Database verified: Feedback stored in `sessions.db`
- Web frontends serving at: `http://localhost:3000` (main), `http://localhost:3001` (admin)

## Bug Fixes (2026-01-25)

### Message Content Not Showing in Admin Panel
**Issue:** `message_content` was always `null` in the feedback list.

**Root Cause:**
- Frontend generates `message_id = "assistant-{Date.now()}"` with epoch milliseconds
- Admin API container runs in UTC timezone
- Chat history timestamps stored as naive datetime strings in host local time
- Timezone mismatch caused time-based queries to miss messages

**Fix Applied:** Changed query strategy to match messages by `session_id` + `role='assistant'` + `timestamp <= feedback.created_at + 1 hour`, sorted by most recent. This avoids timezone conversion issues.

**File Changed:** `apps/admin-api/routers/feedback.py:180-200`

## Blockers
- (none)
