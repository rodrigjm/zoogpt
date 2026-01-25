"""
Zoocari Admin Portal API.
Provides analytics, knowledge base management, and configuration endpoints.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasicCredentials

from config import settings
from auth import login_for_access_token, get_current_user, User, Token, basic_security
from routers import analytics_router, kb_router, config_router, images_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan handler."""
    logger.info("Starting Zoocari Admin Portal API...")
    logger.info(f"Database: {settings.session_db_absolute}")
    logger.info(f"LanceDB: {settings.lancedb_absolute}")
    yield
    logger.info("Shutting down Admin Portal API...")


app = FastAPI(
    title="Zoocari Admin Portal",
    description="Admin interface for Zoocari chatbot analytics and configuration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - Allow admin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Admin dev server
        "http://localhost:8502",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Auth Endpoints
# =============================================================================

@app.post("/auth/login", response_model=Token)
async def login(credentials: HTTPBasicCredentials = Depends(basic_security)):
    """
    Login with HTTP Basic Auth, receive JWT token.

    Use the token in subsequent requests:
    Authorization: Bearer <token>
    """
    return await login_for_access_token(credentials)


@app.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {"username": user.username}


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"ok": True, "service": "admin-portal"}


# =============================================================================
# API Routers
# =============================================================================

app.include_router(analytics_router, prefix="/api/admin")
app.include_router(kb_router, prefix="/api/admin")
app.include_router(config_router, prefix="/api/admin")
app.include_router(images_router, prefix="/api/admin")


# =============================================================================
# Static Files (React SPA)
# =============================================================================

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.admin_api_host,
        port=settings.admin_api_port,
        reload=True,
    )
