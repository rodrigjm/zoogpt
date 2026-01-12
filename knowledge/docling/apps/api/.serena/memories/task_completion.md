# Task Completion Checklist

## After Completing a Task

### 1. Run Tests
```bash
python -m pytest tests/ -v
```
Ensure all tests pass before considering task complete.

### 2. Check Types (if available)
```bash
pyright app/
```

### 3. Verify Imports
- Use relative imports within the package (`from ..models import ...`)
- Remove unused imports (check Pyright/IDE warnings)

### 4. Update Documentation
- Update `docs/integration/STATUS.md` if completing a Phase 1+ task
- Add decisions to the Decisions Log if relevant

### 5. Manual Verification
- Run the server: `uvicorn app.main:app --port 8000`
- Test endpoints with curl or verification scripts

## Code Quality Checks
- [ ] All tests pass
- [ ] No unused imports
- [ ] Type hints on function signatures
- [ ] Docstrings on modules and public functions
- [ ] Response shapes match CONTRACT.md exactly
- [ ] Error responses use standard error shape
