"""
Feedback API endpoints.
Handles user ratings (thumbs up/down) and survey submissions.
"""

import logging
from fastapi import APIRouter, HTTPException

from ..models.feedback import RatingRequest, SurveyRequest, FeedbackResponse
from ..services.feedback import get_feedback_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/rating", response_model=FeedbackResponse)
async def submit_rating(request: RatingRequest):
    """
    Submit a thumbs up/down rating for a specific message.

    - **session_id**: Links to the chat session
    - **message_id**: Links to the specific assistant response
    - **rating**: "up" for thumbs up, "down" for thumbs down

    If a rating already exists for this message, it will be updated.
    """
    try:
        service = get_feedback_service()
        result = service.save_rating(
            session_id=request.session_id,
            message_id=request.message_id,
            rating=request.rating
        )
        return FeedbackResponse(
            id=result["id"],
            created_at=result["created_at"],
            success=result["success"]
        )
    except Exception as e:
        logger.error(f"Failed to save rating: {e}")
        raise HTTPException(status_code=500, detail="Failed to save rating")


@router.post("/survey", response_model=FeedbackResponse)
async def submit_survey(request: SurveyRequest):
    """
    Submit survey feedback for a session.

    - **session_id**: Links to the chat session
    - **comment**: Free-text feedback (max 2000 characters)
    """
    try:
        service = get_feedback_service()
        result = service.save_survey(
            session_id=request.session_id,
            comment=request.comment
        )
        return FeedbackResponse(
            id=result["id"],
            created_at=result["created_at"],
            success=result["success"]
        )
    except Exception as e:
        logger.error(f"Failed to save survey: {e}")
        raise HTTPException(status_code=500, detail="Failed to save survey")
