"""
Session-related Pydantic models.
Aligned with CONTRACT.md Part 4: Sessions.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class SessionCreate(BaseModel):
    """Request model for POST /session."""
    client: str = "web"
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """
    Response model for session endpoints.
    Per CONTRACT.md Part 4: Sessions.

    POST /session returns: {session_id, created_at}
    GET /session/{id} returns: {session_id, created_at, metadata}
    """
    session_id: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Session(BaseModel):
    """Full session representation."""
    session_id: str
    created_at: datetime
    last_active: Optional[datetime] = None
    message_count: int = 0
    client: str = "web"
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """Single chat message in history."""
    message_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
