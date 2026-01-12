# Code Style and Conventions

## Python (Backend)

### General
- **Version**: Python 3.12+
- **Type Hints**: Required for all function signatures
- **Docstrings**: Triple-quoted docstrings for modules, classes, functions
- **Imports**: Relative within package (`from ..models import ...`)

### FastAPI
- Use `APIRouter` with prefix and tags
- Return dicts for exact CONTRACT.md compliance (not Pydantic models)
- Error responses use standard shape:
  ```python
  {"error": {"code": "ERROR_CODE", "message": "...", "details": {}}}
  ```
- Use `fastapi.status` constants

### Pydantic
- Inherit from `pydantic.BaseModel`
- Use `Field()` for validation constraints
- Settings via `pydantic_settings.BaseSettings`

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_underscore_prefix`

## TypeScript (Frontend)

### General
- Strict TypeScript enabled
- Types in `src/types/`
- Must align with CONTRACT.md Part 4

### React
- Functional components with hooks
- Zustand for state management
- Components in `src/components/`

### Naming
- Files: `PascalCase.tsx` for components
- Types/Interfaces: `PascalCase`
- Functions: `camelCase`

## Testing

### Python
- Files: `test_*.py` in `tests/`
- Classes: `Test*`
- Functions: `test_*`
- Use `TestClient` for endpoint tests

### TypeScript
- Files: `*.test.ts` or `*.spec.ts`
- Use Vitest for unit tests
- Use Playwright for e2e tests

## Subagent Conventions
- Subagents collaborate through CONTRACT.md and STATUS.md only
- Return concise summaries (≤15 bullets)
- List files changed and verification steps
- Do NOT paste large logs or code dumps
