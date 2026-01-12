"""
Chat-related Pydantic models.
Aligned with CONTRACT.md Part 4: Chat.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for POST /chat."""
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)
    mode: str = "rag"
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for POST /chat."""
    session_id: str
    message_id: str
    reply: str
    sources: List[Dict[str, Any]] = []
    created_at: datetime
    followup_questions: List[str] = []
    confidence: float = Field(default=1.0, ge=0, le=1)


class StreamChunk(BaseModel):
    """SSE streaming chunk for POST /chat/stream."""
    type: Literal["text", "done", "error"]
    content: Optional[str] = None
    followup_questions: Optional[List[str]] = None
    sources: Optional[List[Dict[str, Any]]] = None
