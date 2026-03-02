"""
Feedback-related Pydantic models.
Handles user ratings (thumbs up/down) and survey submissions.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class RatingRequest(BaseModel):
    """Request model for POST /feedback/rating."""
    session_id: str = Field(..., description="Links to chat session")
    message_id: str = Field(..., description="Links to specific response")
    rating: Literal["up", "down"] = Field(..., description="Thumbs up or down")


class SurveyRequest(BaseModel):
    """Request model for POST /feedback/survey."""
    session_id: str = Field(..., description="Links to chat session")
    comment: str = Field(..., min_length=1, max_length=2000, description="Free-text feedback")


class FeedbackResponse(BaseModel):
    """Response model for feedback submissions."""
    id: int = Field(..., description="Feedback entry ID")
    created_at: datetime = Field(..., description="When submitted")
    success: bool = Field(default=True, description="Whether submission succeeded")


class FeedbackItem(BaseModel):
    """Full feedback representation for admin queries."""
    id: int
    session_id: str
    message_id: Optional[str] = None
    feedback_type: Literal["thumbs_up", "thumbs_down", "survey"]
    comment: Optional[str] = None
    flagged: bool = False
    reviewed_at: Optional[datetime] = None
    created_at: datetime
