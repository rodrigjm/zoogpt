"""
Feedback API endpoints for Admin Portal.
"""

import sqlite3
import json
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user, User
from config import settings
from models.feedback import (
    FeedbackStats,
    FeedbackListResponse,
    FeedbackItem,
    FeedbackDetail,
    DailyTrend,
    FlagUpdateRequest,
    ReviewedUpdateRequest,
)


router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_db_connection():
    """Get SQLite connection to sessions.db."""
    db_path = settings.session_db_absolute
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
):
    """
    Get aggregated feedback statistics.

    Returns counts by type, positive rate, and daily trends.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Overall counts
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down,
                SUM(CASE WHEN feedback_type = 'survey' THEN 1 ELSE 0 END) as surveys,
                SUM(CASE WHEN flagged = 1 THEN 1 ELSE 0 END) as flagged
            FROM feedback
            WHERE created_at >= DATE('now', '-' || ? || ' days')
        """, (days,))

        row = cursor.fetchone()
        total = row["total"] or 0
        thumbs_up = row["thumbs_up"] or 0
        thumbs_down = row["thumbs_down"] or 0
        surveys = row["surveys"] or 0
        flagged = row["flagged"] or 0

        # Calculate positive rate
        positive_rate = None
        rating_total = thumbs_up + thumbs_down
        if rating_total > 0:
            positive_rate = round(thumbs_up / rating_total, 4)

        # Daily trends
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down,
                SUM(CASE WHEN feedback_type = 'survey' THEN 1 ELSE 0 END) as surveys
            FROM feedback
            WHERE created_at >= DATE('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (days,))

        daily_trends = [
            DailyTrend(
                date=r["date"],
                total=r["total"],
                thumbs_up=r["thumbs_up"],
                thumbs_down=r["thumbs_down"],
                surveys=r["surveys"],
            )
            for r in cursor.fetchall()
        ]

        return FeedbackStats(
            total=total,
            thumbs_up=thumbs_up,
            thumbs_down=thumbs_down,
            surveys=surveys,
            flagged=flagged,
            positive_rate=positive_rate,
            daily_trends=daily_trends,
        )
    finally:
        conn.close()


@router.get("/list", response_model=FeedbackListResponse)
async def get_feedback_list(
    feedback_type: Optional[str] = Query(default=None, description="Filter by type: thumbs_up, thumbs_down, survey"),
    flagged: Optional[bool] = Query(default=None, description="Filter by flagged status"),
    start_date: Optional[datetime] = Query(default=None, description="Filter from date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter to date"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """
    Get paginated list of feedback with optional filters.

    Includes message content from chat_history when message_id is present.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Build WHERE clauses
        where_clauses = ["1=1"]
        params: List[Any] = []

        if feedback_type:
            where_clauses.append("feedback_type = ?")
            params.append(feedback_type)

        if flagged is not None:
            where_clauses.append("flagged = ?")
            params.append(1 if flagged else 0)

        if start_date:
            where_clauses.append("created_at >= ?")
            params.append(start_date.isoformat())

        if end_date:
            where_clauses.append("created_at <= ?")
            params.append(end_date.isoformat())

        where_sql = " AND ".join(where_clauses)

        # Get total count
        cursor.execute(
            f"SELECT COUNT(*) FROM feedback WHERE {where_sql}",
            params,
        )
        total = cursor.fetchone()[0]

        # Get feedback items
        cursor.execute(
            f"""
            SELECT * FROM feedback
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        items = []
        for row in cursor.fetchall():
            # Try to get message content from chat_history
            message_content = None
            if row["message_id"]:
                # message_id format is "assistant-{timestamp_ms}" or "user-{timestamp_ms}"
                # Parse timestamp and find closest message by session + time window
                try:
                    parts = row["message_id"].split("-")
                    if len(parts) >= 2 and parts[-1].isdigit():
                        # Get the most recent assistant message in this session
                        # before or around the feedback timestamp.
                        # Use feedback.created_at for matching since it's stored
                        # in the same timezone convention as chat_history.
                        cursor.execute(
                            """
                            SELECT content FROM chat_history
                            WHERE session_id = ?
                              AND role = 'assistant'
                              AND timestamp <= datetime(?, '+1 hour')
                            ORDER BY timestamp DESC
                            LIMIT 1
                            """,
                            (row["session_id"], row["created_at"]),
                        )
                        msg_row = cursor.fetchone()
                        if msg_row:
                            message_content = msg_row["content"]
                except (ValueError, IndexError):
                    pass  # Invalid message_id format, skip

            items.append(FeedbackItem(
                id=row["id"],
                session_id=row["session_id"],
                message_id=row["message_id"],
                feedback_type=row["feedback_type"],
                comment=row["comment"],
                flagged=bool(row["flagged"]),
                reviewed_at=row["reviewed_at"],
                created_at=row["created_at"],
                message_content=message_content,
            ))

        return FeedbackListResponse(total=total, items=items)
    finally:
        conn.close()


# --- Blocked Messages (Abuse Monitoring) ---
# NOTE: These routes must be defined BEFORE /{feedback_id} to avoid route conflicts


class BlockedMessageItem(BaseModel):
    """Blocked message item for list view."""
    id: int
    session_id: str
    message: str
    block_reason: str
    block_source: str
    timestamp: str
    reviewed_at: Optional[str] = None


class BlockedMessagesResponse(BaseModel):
    """Response for blocked messages list."""
    total: int
    items: List[BlockedMessageItem]


@router.get("/blocked", response_model=BlockedMessagesResponse)
async def get_blocked_messages(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """
    Get list of blocked messages for abuse monitoring.

    Shows messages that were blocked by safety filters (LlamaGuard, etc.)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='blocked_messages'"
        )
        if not cursor.fetchone():
            return BlockedMessagesResponse(total=0, items=[])

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM blocked_messages")
        total = cursor.fetchone()[0]

        # Get blocked messages
        cursor.execute(
            """
            SELECT id, session_id, message, block_reason, block_source, timestamp, reviewed_at
            FROM blocked_messages
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        items = [
            BlockedMessageItem(
                id=row[0],
                session_id=row[1],
                message=row[2],
                block_reason=row[3],
                block_source=row[4] or "llamaguard",
                timestamp=row[5],
                reviewed_at=row[6],
            )
            for row in cursor.fetchall()
        ]

        return BlockedMessagesResponse(total=total, items=items)
    finally:
        conn.close()


@router.patch("/blocked/{blocked_id}/reviewed")
async def mark_blocked_reviewed(
    blocked_id: int,
    request: ReviewedUpdateRequest,
    user: User = Depends(get_current_user),
):
    """Mark a blocked message as reviewed."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        reviewed_at = datetime.now(UTC).isoformat() if request.reviewed else None

        cursor.execute(
            "UPDATE blocked_messages SET reviewed_at = ? WHERE id = ?",
            (reviewed_at, blocked_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Blocked message not found")

        conn.commit()

        return {"ok": True, "reviewed_at": reviewed_at}
    finally:
        conn.close()


# --- Feedback Detail and Updates (parameterized routes must come last) ---


@router.get("/{feedback_id}", response_model=FeedbackDetail)
async def get_feedback_detail(
    feedback_id: int,
    user: User = Depends(get_current_user),
):
    """
    Get single feedback item with full chat history context.

    Includes surrounding messages from the session for context.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Get feedback item
        cursor.execute(
            "SELECT * FROM feedback WHERE id = ?",
            (feedback_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Feedback not found")

        # Get chat context (last 10 messages before and after the feedback)
        chat_context = None
        if row["session_id"]:
            cursor.execute(
                """
                SELECT id, role, content, timestamp
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                (row["session_id"],),
            )
            chat_context = [
                {
                    "id": r["id"],
                    "role": r["role"],
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                }
                for r in cursor.fetchall()
            ]

        return FeedbackDetail(
            id=row["id"],
            session_id=row["session_id"],
            message_id=row["message_id"],
            feedback_type=row["feedback_type"],
            comment=row["comment"],
            flagged=bool(row["flagged"]),
            reviewed_at=row["reviewed_at"],
            created_at=row["created_at"],
            chat_context=chat_context,
        )
    finally:
        conn.close()


@router.patch("/{feedback_id}/flag")
async def update_flagged_status(
    feedback_id: int,
    request: FlagUpdateRequest,
    user: User = Depends(get_current_user),
):
    """Toggle flagged status on a feedback item."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE feedback SET flagged = ? WHERE id = ?",
            (1 if request.flagged else 0, feedback_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Feedback not found")

        conn.commit()

        return {"ok": True, "flagged": request.flagged}
    finally:
        conn.close()


@router.patch("/{feedback_id}/reviewed")
async def mark_as_reviewed(
    feedback_id: int,
    request: ReviewedUpdateRequest,
    user: User = Depends(get_current_user),
):
    """Mark feedback as reviewed (sets reviewed_at timestamp)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        reviewed_at = datetime.now(UTC).isoformat() if request.reviewed else None

        cursor.execute(
            "UPDATE feedback SET reviewed_at = ? WHERE id = ?",
            (reviewed_at, feedback_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Feedback not found")

        conn.commit()

        return {"ok": True, "reviewed_at": reviewed_at}
    finally:
        conn.close()
