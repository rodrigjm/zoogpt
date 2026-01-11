"""
Session-related Pydantic models.
Aligned with CONTRACT.md Part 4: Sessions.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SessionCreate(BaseModel):
    """Request model for POST /session."""
    client: str = "web"
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Response model for session endpoints."""
    session_id: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
