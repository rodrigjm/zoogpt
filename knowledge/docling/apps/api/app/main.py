"""
FastAPI main application entry point.
Implements /health endpoint per CONTRACT.md Part 4.
"""

from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routers import session_router, chat_router, voice_router

# Create FastAPI app
app = FastAPI(
    title="Zoocari API",
    description="Voice-first zoo Q&A chatbot backend",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint (CONTRACT.md Part 4: Health)
@app.get("/health")
async def health_check():
    """Simple health check returning {"ok": true}."""
    return {"ok": True}


# Create API router with /api prefix for production
# In dev, Vite proxies /api/* and strips prefix; in prod, FastAPI handles it directly
api_router = APIRouter(prefix="/api")
api_router.include_router(session_router)
api_router.include_router(chat_router)
api_router.include_router(voice_router)
app.include_router(api_router)

# Also register routers without prefix for dev compatibility (Vite strips /api)
app.include_router(session_router)
app.include_router(chat_router)
app.include_router(voice_router)

# Mount static files (production frontend)
# Only mount if static directory exists (production mode)
# MUST be last - catches all unmatched routes for SPA routing
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
