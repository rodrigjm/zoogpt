"""
Session router - implements POST /session and GET /session/{session_id}.
Per CONTRACT.md Part 4: Sessions.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import uuid

from ..models import SessionCreate, ErrorResponse
from ..services.session import SessionService

router = APIRouter(prefix="/session", tags=["session"])

# SQLite session storage
_session_service = SessionService()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Session created successfully"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
)
async def create_session(body: SessionCreate):
    """
    Create a new session.

    Per CONTRACT.md:
    - Request: {client: "web", metadata: {}}
    - Response: {session_id, created_at} (only these two fields)
    """
    session_id = str(uuid.uuid4())

    # Create session in database
    session_data = _session_service.get_or_create_session(
        session_id=session_id,
        metadata=body.metadata or {}
    )

    # Return only session_id and created_at per CONTRACT.md
    return {
        "session_id": session_data["session_id"],
        "created_at": session_data["created_at"],
    }


@router.get(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Session found"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def get_session(session_id: str):
    """
    Fetch session info by ID.

    Per CONTRACT.md:
    - Response 200: {session_id, created_at, metadata}
    - Response 404: Standard error shape {error: {code, message, details}}
    """
    session_data = _session_service.get_session(session_id)

    if not session_data:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session {session_id} not found",
                    "details": {},
                }
            },
        )

    return {
        "session_id": session_data["session_id"],
        "created_at": session_data["created_at"],
        "metadata": session_data["metadata"],
    }
