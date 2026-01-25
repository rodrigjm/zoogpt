# Zoocari API Test Suite

This directory contains the test suite for the Zoocari API backend.

## Test Types

### Unit Tests
Test individual components in isolation (models, validators, utilities).

- `test_models.py` - Pydantic model validation tests

### Integration Tests
Test individual API endpoints.

- `test_health.py` - Health endpoint tests
- `test_session_endpoints.py` - Session creation and retrieval tests
- `test_chat_endpoints.py` - Chat endpoint tests
- `test_voice_endpoints.py` - Voice STT/TTS endpoint tests
- `test_kb_park_animals.py` - Park animal KB entry integration tests (new species, locations, individual names)

### Smoke Tests
End-to-end integration tests that verify complete user flows across multiple endpoints.

- `test_integration_smoke.py` - Phase 1 integration smoke tests

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest test_models.py
```

### Integration Tests
```bash
pytest test_*_endpoints.py test_health.py
```

### Smoke Tests Only
```bash
# Using pytest marker
pytest -m smoke

# Using the smoke test file directly
pytest tests/test_integration_smoke.py

# Using the convenience script
./run_smoke_tests.sh

# With options
./run_smoke_tests.sh --verbose
./run_smoke_tests.sh --failfast
```

### Specific Test Classes
```bash
pytest tests/test_integration_smoke.py::TestFullVoiceAssistantFlowSmoke
```

### Specific Test Function
```bash
pytest tests/test_integration_smoke.py::TestChatFlowSmoke::test_session_to_chat_flow -v
```

### KB Park Animals Tests
```bash
# Run all KB park animal tests
pytest apps/api/tests/test_kb_park_animals.py -v

# Run specific test
pytest apps/api/tests/test_kb_park_animals.py::test_new_species_cotton_top_tamarin -v
```

## Test Coverage by Flow

### Smoke Tests Cover:
1. **Health check** - Basic service availability
2. **Session flow** - Create → retrieve → verify shapes
3. **Chat flow** - Session → chat → verify response
4. **Voice STT flow** - Session → audio → transcription
5. **Voice TTS flow** - Session → text → audio
6. **Full voice assistant** - Session → STT → chat → TTS
7. **Chat with TTS** - Session → chat → TTS reply
8. **Error handling** - 404s, 422s with correct shapes
9. **Cross-endpoint integration** - Session reuse across endpoints

## CI/CD Integration

### Docker Environment
Tests can run inside the Docker container:

```bash
# Run smoke tests
docker-compose exec api pytest -m smoke

# Run KB park animal tests (rebuild container first if new test added)
docker-compose up -d --build api
docker exec zoocari-api pytest tests/test_kb_park_animals.py -v
```

### GitHub Actions
Add to `.github/workflows/test.yml`:

```yaml
- name: Run smoke tests
  run: |
    cd apps/api
    pytest -m smoke --tb=short
```

## Test Conventions

### Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Markers
Tests are organized with pytest markers:
- `@pytest.mark.smoke` - Integration smoke tests
- `@pytest.mark.unit` - Unit tests (future)
- `@pytest.mark.integration` - Integration tests (future)

### Structure
Each test should:
1. Follow Arrange-Act-Assert pattern
2. Have a clear docstring explaining what it tests
3. Verify response shapes per CONTRACT.md
4. Use descriptive assertion messages where helpful

## Mock Data

### Audio Files
Smoke tests use mock audio data:
```python
io.BytesIO(b"mock audio content")
```

No external audio files required.

### Sessions
Each test creates its own session to ensure isolation.

## Debugging Failed Tests

### Verbose Output
```bash
pytest -vv tests/test_integration_smoke.py
```

### Show Print Statements
```bash
pytest -s tests/test_integration_smoke.py
```

### Stop on First Failure
```bash
pytest -x tests/test_integration_smoke.py
```

### Show Full Traceback
```bash
pytest --tb=long tests/test_integration_smoke.py
```

## Requirements

- Python 3.12+
- FastAPI test client
- All dependencies in `requirements.txt`

## Notes

- Tests use in-memory SQLite (configured in test environment)
- No external services required (STT/TTS use mock implementations)
- Tests are designed to be fast (<30 seconds total)
- All tests are deterministic and repeatable
