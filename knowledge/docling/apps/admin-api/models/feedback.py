"""
Feedback API response models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class FeedbackItem(BaseModel):
    """Single feedback item with message context."""
    id: int
    session_id: str
    message_id: Optional[str] = None
    feedback_type: str
    comment: Optional[str] = None
    flagged: bool
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    message_content: Optional[str] = None


class FeedbackListResponse(BaseModel):
    """Paginated list of feedback items."""
    total: int
    items: List[FeedbackItem]


class DailyTrend(BaseModel):
    """Daily feedback aggregation."""
    date: str
    total: int
    thumbs_up: int
    thumbs_down: int
    surveys: int


class FeedbackStats(BaseModel):
    """Aggregated feedback statistics."""
    total: int
    thumbs_up: int
    thumbs_down: int
    surveys: int
    flagged: int
    positive_rate: Optional[float] = None
    daily_trends: List[DailyTrend]


class FeedbackDetail(BaseModel):
    """Detailed feedback with full chat history context."""
    id: int
    session_id: str
    message_id: Optional[str] = None
    feedback_type: str
    comment: Optional[str] = None
    flagged: bool
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    chat_context: Optional[List[Dict[str, Any]]] = None


class FlagUpdateRequest(BaseModel):
    """Request to toggle flagged status."""
    flagged: bool


class ReviewedUpdateRequest(BaseModel):
    """Request to mark feedback as reviewed."""
    reviewed: bool
