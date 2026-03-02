# Task Completion Checklist

## After Completing Any Task

### 1. Run Tests
```bash
# Backend
cd apps/api && python -m pytest tests/ -v

# Frontend
cd apps/web && npm test
```

### 2. Verify Types
```bash
# Backend
pyright apps/api/app/

# Frontend
cd apps/web && npm run type-check  # or tsc --noEmit
```

### 3. Clean Up
- Remove unused imports
- Ensure relative imports in Python (`from ..models import ...`)
- No console.logs left in production code

### 4. Update Documentation
- Update `docs/integration/STATUS.md` if completing a Phase task
- Add decisions to Decisions Log if relevant
- Update CONTRACT.md if API shapes changed

### 5. Manual Verification
```bash
# Start backend
cd apps/api && uvicorn app.main:app --port 8000

# Test endpoints
curl http://localhost:8000/health
./verify_session_endpoints.sh
./verify_chat_endpoint.sh
```

## Subagent Reporting Format
When completing a task as a subagent, return:
```
## Summary
- [1-3 bullets: what was done]

## Files Changed
- `path/to/file` — description

## Contract Impact
- None | Updated CONTRACT.md section X | Question added to STATUS.md

## Verification
```bash
# Command to verify
```

## Issues Found (if any)
- Issue → Resolution
```

## Quality Checklist
- [ ] All tests pass
- [ ] No type errors
- [ ] Response shapes match CONTRACT.md
- [ ] Error responses use standard shape
- [ ] STATUS.md updated (if Phase 1+ task)
