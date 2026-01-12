# Suggested Commands

## Backend (apps/api)

### Development Server
```bash
cd apps/api
source ../../.venv/bin/activate  # or use full path
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
cd apps/api
python -m pytest tests/ -v
python -m pytest tests/test_session_endpoints.py -v  # specific file
```

### Type Checking
```bash
pyright apps/api/app/
```

## Frontend (apps/web)

### Development Server
```bash
cd apps/web
npm run dev  # Vite dev server on port 3000
```

### Build
```bash
cd apps/web
npm run build
npm run preview  # preview production build
```

### Testing
```bash
cd apps/web
npm test        # Vitest
npm run test:e2e  # Playwright (if configured)
```

## Docker

### Build and Run
```bash
docker-compose up --build
docker-compose down
```

### Individual Services
```bash
docker-compose up api   # backend only
docker-compose up web   # frontend only
```

## Data / RAG

### Build Knowledge Base
```bash
python zoo_build_knowledge.py
```

## Git Operations
```bash
git status
git diff
git add .
git commit -m "message"
git push origin feature/branch-name
```

## Verification Scripts
```bash
# From apps/api directory
./verify_session_endpoints.sh
./verify_chat_endpoint.sh
```
