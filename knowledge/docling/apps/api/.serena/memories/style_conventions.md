# Code Style and Conventions

## Python Style
- **Version**: Python 3.12+
- **Type Hints**: Required for all function signatures
- **Docstrings**: Triple-quoted docstrings for modules, classes, and functions
- **Imports**: 
  - Use relative imports within the package (e.g., `from ..models import ...`)
  - Group: stdlib, third-party, local imports

## FastAPI Conventions
- **Routers**: Use `APIRouter` with prefix and tags
- **Response Models**: Define in `app/models/`, but return dicts for exact CONTRACT.md compliance
- **Error Handling**: Return `JSONResponse` with standard error shape:
  ```python
  {
      "error": {
          "code": "ERROR_CODE",
          "message": "Human readable message",
          "details": {}
      }
  }
  ```
- **Status Codes**: Use `fastapi.status` constants

## Pydantic Models
- **Base**: Inherit from `pydantic.BaseModel`
- **Optional Fields**: Use `Optional[Type] = None` or `Type | None = None`
- **Field Validation**: Use `Field()` for constraints (min_length, max_length)
- **Settings**: Use `pydantic_settings.BaseSettings` for config

## Naming Conventions
- **Files**: snake_case (e.g., `session.py`, `chat_router.py`)
- **Classes**: PascalCase (e.g., `SessionCreate`, `ChatResponse`)
- **Functions**: snake_case (e.g., `create_session`, `get_health`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_VOICE`)
- **Private vars**: Prefix with underscore (e.g., `_sessions`)

## Testing Conventions
- **Test files**: `test_*.py` in `tests/` directory
- **Test classes**: `Test*` (e.g., `TestSessionEndpoint`)
- **Test functions**: `test_*` (e.g., `test_create_session_success`)
- **Use**: `fastapi.testclient.TestClient` for endpoint tests
