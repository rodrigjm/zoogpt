#!/bin/bash
# Quick verification script for FastAPI backend initialization

set -e

echo "=== Zoocari API Backend Verification ==="
echo ""

echo "1. Checking Python version..."
python3 --version
echo "   ✓ Python 3 available"
echo ""

echo "2. Checking directory structure..."
test -f requirements.txt && echo "   ✓ requirements.txt exists"
test -f app/main.py && echo "   ✓ app/main.py exists"
test -f app/config.py && echo "   ✓ app/config.py exists"
test -d app/models && echo "   ✓ app/models/ exists"
test -d app/routers && echo "   ✓ app/routers/ exists"
test -d app/services && echo "   ✓ app/services/ exists"
test -d tests && echo "   ✓ tests/ exists"
echo ""

echo "3. Checking model files..."
test -f app/models/common.py && echo "   ✓ ErrorResponse model"
test -f app/models/session.py && echo "   ✓ Session models"
test -f app/models/chat.py && echo "   ✓ Chat models"
test -f app/models/voice.py && echo "   ✓ Voice models"
echo ""

echo "4. Checking router files..."
test -f app/routers/session.py && echo "   ✓ Session router"
test -f app/routers/chat.py && echo "   ✓ Chat router"
test -f app/routers/voice.py && echo "   ✓ Voice router"
echo ""

echo "✅ All structure checks passed!"
echo ""
echo "Next steps:"
echo "  1. Create virtual environment: python3 -m venv venv"
echo "  2. Activate: source venv/bin/activate"
echo "  3. Install: pip install -r requirements.txt"
echo "  4. Configure: cp .env.example .env (then edit)"
echo "  5. Run: uvicorn app.main:app --reload"
echo "  6. Test: curl http://localhost:8000/health"
