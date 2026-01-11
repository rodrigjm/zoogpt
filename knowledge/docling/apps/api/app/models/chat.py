"""
Chat-related Pydantic models.
Aligned with CONTRACT.md Part 4: Chat.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for POST /chat."""
    session_id: str
    message: str
    mode: str = "rag"
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for POST /chat."""
    session_id: str
    message_id: str
    reply: str
    sources: List[Dict[str, Any]] = []
    created_at: datetime
