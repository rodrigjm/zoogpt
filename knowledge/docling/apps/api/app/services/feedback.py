"""
Feedback Service for SQLite-based persistence.
Stores user ratings (thumbs up/down) and survey feedback.

Uses the same sessions.db database as SessionService.
"""

import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from ..config import settings


class FeedbackService:
    """
    Feedback service with SQLite persistence.
    Stores ratings and survey responses in the feedback table.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize feedback service.

        Args:
            db_path: Path to SQLite database. If None, uses settings.session_db_path
        """
        self.db_path = Path(db_path or settings.session_db_path)
        self._ensure_db_exists()
        self._init_schema()

    def _ensure_db_exists(self):
        """Ensure the data directory and database exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize feedback table schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id TEXT,
                    feedback_type TEXT NOT NULL,
                    comment TEXT,
                    flagged BOOLEAN DEFAULT 0,
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for session lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_session
                ON feedback(session_id)
            """)

            # Index for message lookups (for rating updates)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_message
                ON feedback(session_id, message_id)
            """)

            # Index for admin filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_flagged
                ON feedback(flagged, created_at DESC)
            """)

            conn.commit()

    def save_rating(
        self,
        session_id: str,
        message_id: str,
        rating: str
    ) -> Dict[str, Any]:
        """
        Save or update a thumbs up/down rating.

        Args:
            session_id: Session identifier
            message_id: Message identifier
            rating: "up" or "down"

        Returns:
            Dict with id, created_at, success
        """
        feedback_type = "thumbs_up" if rating == "up" else "thumbs_down"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if rating already exists for this message
            cursor.execute(
                """SELECT id FROM feedback
                   WHERE session_id = ? AND message_id = ?
                   AND feedback_type IN ('thumbs_up', 'thumbs_down')""",
                (session_id, message_id)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing rating
                cursor.execute(
                    """UPDATE feedback
                       SET feedback_type = ?, created_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (feedback_type, existing["id"])
                )
                feedback_id = existing["id"]
            else:
                # Insert new rating
                cursor.execute(
                    """INSERT INTO feedback (session_id, message_id, feedback_type)
                       VALUES (?, ?, ?)""",
                    (session_id, message_id, feedback_type)
                )
                feedback_id = cursor.lastrowid

            conn.commit()

            return {
                "id": feedback_id,
                "created_at": datetime.now(UTC).isoformat(),
                "success": True
            }

    def save_survey(
        self,
        session_id: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Save survey feedback.

        Args:
            session_id: Session identifier
            comment: Free-text feedback

        Returns:
            Dict with id, created_at, success
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO feedback (session_id, feedback_type, comment)
                   VALUES (?, 'survey', ?)""",
                (session_id, comment)
            )
            feedback_id = cursor.lastrowid
            conn.commit()

            return {
                "id": feedback_id,
                "created_at": datetime.now(UTC).isoformat(),
                "success": True
            }

    def get_feedback(
        self,
        feedback_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single feedback entry by ID.

        Args:
            feedback_id: Feedback entry ID

        Returns:
            Feedback dict or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM feedback WHERE id = ?",
                (feedback_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row["id"],
                "session_id": row["session_id"],
                "message_id": row["message_id"],
                "feedback_type": row["feedback_type"],
                "comment": row["comment"],
                "flagged": bool(row["flagged"]),
                "reviewed_at": row["reviewed_at"],
                "created_at": row["created_at"]
            }

    def list_feedback(
        self,
        feedback_type: Optional[str] = None,
        flagged: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List feedback entries with optional filtering.

        Args:
            feedback_type: Filter by type (thumbs_up, thumbs_down, survey)
            flagged: Filter by flagged status
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            Dict with total count and list of feedback entries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["1=1"]
            params: List[Any] = []

            if feedback_type:
                where_clauses.append("feedback_type = ?")
                params.append(feedback_type)

            if flagged is not None:
                where_clauses.append("flagged = ?")
                params.append(1 if flagged else 0)

            where_sql = " AND ".join(where_clauses)

            # Get total count
            cursor.execute(
                f"SELECT COUNT(*) FROM feedback WHERE {where_sql}",
                params
            )
            total = cursor.fetchone()[0]

            # Get entries
            cursor.execute(
                f"""SELECT * FROM feedback
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?""",
                params + [limit, offset]
            )

            items = []
            for row in cursor.fetchall():
                items.append({
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "message_id": row["message_id"],
                    "feedback_type": row["feedback_type"],
                    "comment": row["comment"],
                    "flagged": bool(row["flagged"]),
                    "reviewed_at": row["reviewed_at"],
                    "created_at": row["created_at"]
                })

            return {"total": total, "items": items}

    def toggle_flag(self, feedback_id: int) -> Optional[bool]:
        """
        Toggle the flagged status of a feedback entry.

        Args:
            feedback_id: Feedback entry ID

        Returns:
            New flagged status, or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT flagged FROM feedback WHERE id = ?",
                (feedback_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            new_flagged = not bool(row["flagged"])
            cursor.execute(
                "UPDATE feedback SET flagged = ? WHERE id = ?",
                (1 if new_flagged else 0, feedback_id)
            )
            conn.commit()

            return new_flagged

    def mark_reviewed(self, feedback_id: int) -> bool:
        """
        Mark a feedback entry as reviewed.

        Args:
            feedback_id: Feedback entry ID

        Returns:
            True if updated, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """UPDATE feedback
                   SET reviewed_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (feedback_id,)
            )
            conn.commit()

            return cursor.rowcount > 0

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Args:
            days: Number of days to include

        Returns:
            Dict with counts and rates
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down,
                    SUM(CASE WHEN feedback_type = 'survey' THEN 1 ELSE 0 END) as surveys,
                    SUM(CASE WHEN flagged = 1 THEN 1 ELSE 0 END) as flagged
                FROM feedback
                WHERE created_at >= DATE('now', '-{days} days')
            """)
            row = cursor.fetchone()

            total = row["total"] or 0
            thumbs_up = row["thumbs_up"] or 0
            thumbs_down = row["thumbs_down"] or 0
            total_ratings = thumbs_up + thumbs_down

            return {
                "total": total,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "surveys": row["surveys"] or 0,
                "flagged": row["flagged"] or 0,
                "positive_rate": round(thumbs_up / total_ratings, 4) if total_ratings > 0 else None
            }

    def get_daily_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily feedback trends.

        Args:
            days: Number of days to include

        Returns:
            List of daily stats
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT
                    DATE(created_at) as date,
                    SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down,
                    SUM(CASE WHEN feedback_type = 'survey' THEN 1 ELSE 0 END) as surveys
                FROM feedback
                WHERE created_at >= DATE('now', '-{days} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)

            return [
                {
                    "date": row["date"],
                    "thumbs_up": row["thumbs_up"] or 0,
                    "thumbs_down": row["thumbs_down"] or 0,
                    "surveys": row["surveys"] or 0
                }
                for row in cursor.fetchall()
            ]


# Singleton instance
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get or create the feedback service singleton."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
