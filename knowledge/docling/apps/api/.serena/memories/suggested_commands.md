# Suggested Commands

## Development Server
```bash
# Run the FastAPI server (from apps/api directory)
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using the venv python directly
/path/to/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_session_endpoints.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Linting & Formatting
```bash
# Type checking (if pyright installed)
pyright app/

# Format with black (if installed)
black app/ tests/

# Sort imports (if isort installed)
isort app/ tests/
```

## Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Upgrade a specific package
pip install --upgrade fastapi
```

## Verification Scripts
```bash
# Verify session endpoints (requires server running)
./verify_session_endpoints.sh

# Verify chat endpoint (requires server running)
./verify_chat_endpoint.sh
```

## System Utilities (Darwin/macOS)
```bash
# List files
ls -la

# Find files
find . -name "*.py"

# Search in files
grep -r "pattern" app/

# Git operations
git status
git diff
git add .
git commit -m "message"
```
