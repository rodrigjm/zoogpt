# Zoocari API Backend

FastAPI backend for Zoocari voice-first zoo Q&A chatbot.

## Setup

1. Create virtual environment:
```bash
cd apps/api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Run development server:
```bash
uvicorn app.main:app --reload --port 8000
```

Or using Python directly:
```bash
python -m app.main
```

## Verification

Test health endpoint:
```bash
curl http://localhost:8000/health
# Expected: {"ok":true}
```

Run tests:
```bash
pytest
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contract

API contracts are defined in `/docs/integration/CONTRACT.md`.
