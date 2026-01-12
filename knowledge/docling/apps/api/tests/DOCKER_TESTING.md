# Running Tests in Docker

This guide shows how to run the Zoocari API test suite inside Docker containers.

## Prerequisites

Ensure Docker and docker-compose are installed and the containers are running:

```bash
docker-compose up -d
```

## Running Tests in Docker

### All Tests
```bash
docker-compose exec api pytest
```

### Smoke Tests Only
```bash
# Using pytest marker
docker-compose exec api pytest -m smoke

# Using the test file directly
docker-compose exec api pytest tests/test_integration_smoke.py

# Using the convenience script
docker-compose exec api ./run_smoke_tests.sh
```

### Specific Test Categories
```bash
# Unit tests (models)
docker-compose exec api pytest tests/test_models.py

# Integration tests (endpoints)
docker-compose exec api pytest tests/test_*_endpoints.py

# Health check
docker-compose exec api pytest tests/test_health.py
```

### With Options
```bash
# Verbose output
docker-compose exec api pytest -m smoke -vv

# Stop on first failure
docker-compose exec api pytest -m smoke -x

# Show print statements
docker-compose exec api pytest -m smoke -s

# Full traceback on failure
docker-compose exec api pytest -m smoke --tb=long
```

## Continuous Integration (CI/CD)

### Docker-based CI Pipeline

Example GitHub Actions workflow:

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker-compose build api

      - name: Run smoke tests
        run: docker-compose run --rm api pytest -m smoke --tb=short

      - name: Run all tests
        run: docker-compose run --rm api pytest --tb=short
```

### Local Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running smoke tests..."
docker-compose exec -T api pytest -m smoke -q
if [ $? -ne 0 ]; then
    echo "Smoke tests failed. Commit aborted."
    exit 1
fi
```

## Test Database

Tests use an in-memory SQLite database by default, configured via environment variables:

```bash
# In docker-compose.yml or .env
DATABASE_URL=sqlite:///:memory:
```

This ensures:
- Fast test execution
- No persistent data between runs
- Complete test isolation

## Troubleshooting

### Container Not Running
```bash
docker-compose ps
docker-compose up -d api
```

### Permission Issues
```bash
docker-compose exec -u root api pytest -m smoke
```

### View Container Logs
```bash
docker-compose logs api
docker-compose logs -f api  # Follow logs
```

### Rebuild Container
```bash
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

### Interactive Shell
```bash
docker-compose exec api bash
# Now you're inside the container
pytest -m smoke
```

## Performance

Smoke tests are designed to be fast:
- **Target:** <5 seconds in Docker
- **Actual:** ~1-2 seconds (14 tests)
- No external service dependencies
- In-memory database
- Mock audio/STT/TTS implementations

## Notes

- Tests run in the same environment as production code
- All dependencies installed via requirements.txt
- Python 3.12+ required for Kokoro compatibility
- Tests are completely isolated (no shared state)
