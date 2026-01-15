"""
Analytics Service for Admin Portal.
Tracks chat interactions, session metrics, and daily aggregates.
Extends the existing sessions.db with analytics tables.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from ..config import settings
from ..models.analytics import (
    ChatInteraction,
    SessionSummary,
    DailyAnalytics,
    DashboardMetrics,
    TodayMetrics,
    LatencyBreakdown,
    PercentileStats,
)


class AnalyticsService:
    """
    Analytics service for tracking chatbot usage and performance.
    Uses the same SQLite database as SessionService.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize analytics service.

        Args:
            db_path: Path to SQLite database. If None, uses settings.session_db_path
        """
        self.db_path = Path(db_path or settings.session_db_path)
        self._ensure_db_exists()
        self._init_analytics_schema()

    def _ensure_db_exists(self):
        """Ensure the data directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_analytics_schema(self):
        """Initialize analytics-specific tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Chat interactions for Q&A analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources JSON,
                    confidence_score REAL,
                    latency_ms INTEGER,
                    rag_latency_ms INTEGER,
                    llm_latency_ms INTEGER,
                    tts_latency_ms INTEGER,
                    feedback_rating INTEGER
                )
            """)

            # Session aggregates for dashboard
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    message_count INTEGER DEFAULT 0,
                    avg_response_latency_ms REAL,
                    voice_requests INTEGER DEFAULT 0,
                    client_type TEXT,
                    device_info JSON
                )
            """)

            # Daily aggregates for trends
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_analytics (
                    date DATE PRIMARY KEY,
                    total_sessions INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    avg_session_duration_sec REAL,
                    avg_response_latency_ms REAL,
                    unique_animals_queried JSON,
                    top_questions JSON,
                    error_count INTEGER DEFAULT 0
                )
            """)

            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_session
                ON chat_interactions(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
                ON chat_interactions(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_start
                ON session_metrics(start_time)
            """)

            conn.commit()

    # =========================================================================
    # Recording Methods (called from main app)
    # =========================================================================

    def record_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        latency_ms: int = 0,
        rag_latency_ms: Optional[int] = None,
        llm_latency_ms: Optional[int] = None,
        tts_latency_ms: Optional[int] = None,
    ) -> Optional[int]:
        """
        Record a chat interaction for analytics.

        Args:
            session_id: Session identifier
            question: User's question
            answer: Assistant's response
            sources: Retrieved KB sources
            confidence_score: RAG confidence (0.0-1.0)
            latency_ms: Total end-to-end latency
            rag_latency_ms: LanceDB query time
            llm_latency_ms: OpenAI API time
            tts_latency_ms: TTS synthesis time (if voice request)

        Returns:
            Interaction ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO chat_interactions
                   (session_id, question, answer, sources, confidence_score,
                    latency_ms, rag_latency_ms, llm_latency_ms, tts_latency_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    question,
                    answer,
                    json.dumps(sources) if sources else None,
                    confidence_score,
                    latency_ms,
                    rag_latency_ms,
                    llm_latency_ms,
                    tts_latency_ms,
                )
            )
            # Update session metrics
            self._update_session_metrics(cursor, session_id, latency_ms, tts_latency_ms is not None)

            conn.commit()
            return cursor.lastrowid

    def _update_session_metrics(
        self,
        cursor: sqlite3.Cursor,
        session_id: str,
        latency_ms: int,
        is_voice: bool = False,
    ):
        """Update session metrics after an interaction."""
        # Check if metrics exist
        cursor.execute(
            "SELECT * FROM session_metrics WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()

        if row:
            # Update existing metrics
            new_count = row["message_count"] + 1
            current_avg = row["avg_response_latency_ms"] or 0
            new_avg = ((current_avg * row["message_count"]) + latency_ms) / new_count
            voice_count = row["voice_requests"] + (1 if is_voice else 0)

            cursor.execute(
                """UPDATE session_metrics
                   SET message_count = ?, avg_response_latency_ms = ?,
                       voice_requests = ?, end_time = CURRENT_TIMESTAMP
                   WHERE session_id = ?""",
                (new_count, new_avg, voice_count, session_id)
            )
        else:
            # Create new metrics
            cursor.execute(
                """INSERT INTO session_metrics
                   (session_id, start_time, message_count, avg_response_latency_ms, voice_requests)
                   VALUES (?, CURRENT_TIMESTAMP, 1, ?, ?)""",
                (session_id, latency_ms, 1 if is_voice else 0)
            )

    def update_tts_latency(self, session_id: str, tts_latency_ms: int):
        """
        Update the last interaction with TTS latency.
        Called after TTS completes for voice requests.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE chat_interactions
                   SET tts_latency_ms = ?
                   WHERE session_id = ?
                   ORDER BY id DESC LIMIT 1""",
                (tts_latency_ms, session_id)
            )
            conn.commit()

    # =========================================================================
    # Query Methods (called from admin API)
    # =========================================================================

    def get_dashboard_metrics(self, days: int = 7) -> DashboardMetrics:
        """Get dashboard summary metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Today's metrics
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(*) as questions,
                    AVG(latency_ms) as avg_latency
                FROM chat_interactions
                WHERE DATE(timestamp) = DATE('now')
            """)
            today_row = cursor.fetchone()

            # Error rate (approximated by low confidence)
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN confidence_score < 0.3 THEN 1 ELSE 0 END) as low_confidence
                FROM chat_interactions
                WHERE DATE(timestamp) = DATE('now')
            """)
            error_row = cursor.fetchone()
            error_rate = (error_row["low_confidence"] or 0) / max(error_row["total"] or 1, 1)

            today = TodayMetrics(
                sessions=today_row["sessions"] or 0,
                questions=today_row["questions"] or 0,
                avg_latency_ms=today_row["avg_latency"],
                error_rate=error_rate,
            )

            # Trends (last N days)
            cursor.execute(f"""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(*) as questions,
                    AVG(latency_ms) as avg_latency
                FROM chat_interactions
                WHERE timestamp >= DATE('now', '-{days} days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """)
            trends = [
                DailyAnalytics(
                    date=row["date"],
                    total_sessions=row["sessions"],
                    total_questions=row["questions"],
                    avg_response_latency_ms=row["avg_latency"],
                )
                for row in cursor.fetchall()
            ]

            # Top questions
            cursor.execute("""
                SELECT question, COUNT(*) as count
                FROM chat_interactions
                WHERE timestamp >= DATE('now', '-7 days')
                GROUP BY question
                ORDER BY count DESC
                LIMIT 10
            """)
            top_questions = [
                {"question": row["question"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

            # Top animals (extract from sources JSON)
            cursor.execute("""
                SELECT sources
                FROM chat_interactions
                WHERE sources IS NOT NULL
                  AND timestamp >= DATE('now', '-7 days')
            """)
            animal_counts: Dict[str, int] = {}
            for row in cursor.fetchall():
                try:
                    sources = json.loads(row["sources"]) if row["sources"] else []
                    for source in sources:
                        animal = source.get("animal", "Unknown")
                        animal_counts[animal] = animal_counts.get(animal, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            top_animals = sorted(
                [{"name": k, "count": v} for k, v in animal_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:10]

            return DashboardMetrics(
                today=today,
                trends=trends,
                top_questions=top_questions,
                top_animals=top_animals,
            )

    def get_sessions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionSummary]:
        """Get session list with optional date filtering."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    session_id,
                    start_time,
                    end_time,
                    message_count,
                    avg_response_latency_ms,
                    client_type
                FROM session_metrics
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND start_time >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND start_time <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            return [
                SessionSummary(
                    session_id=row["session_id"],
                    start_time=row["start_time"],
                    duration_seconds=self._calc_duration(row["start_time"], row["end_time"]),
                    message_count=row["message_count"],
                    avg_latency_ms=row["avg_response_latency_ms"],
                    client_type=row["client_type"],
                )
                for row in cursor.fetchall()
            ]

    def _calc_duration(self, start: str, end: Optional[str]) -> Optional[int]:
        """Calculate session duration in seconds."""
        if not end:
            return None
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return int((end_dt - start_dt).total_seconds())
        except (ValueError, AttributeError):
            return None

    def get_session_interactions(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[ChatInteraction]:
        """Get all interactions for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """SELECT * FROM chat_interactions
                   WHERE session_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (session_id, limit)
            )

            return [
                ChatInteraction(
                    id=row["id"],
                    session_id=row["session_id"],
                    timestamp=row["timestamp"],
                    question=row["question"],
                    answer=row["answer"],
                    sources=json.loads(row["sources"]) if row["sources"] else None,
                    confidence_score=row["confidence_score"],
                    latency_ms=row["latency_ms"],
                    rag_latency_ms=row["rag_latency_ms"],
                    llm_latency_ms=row["llm_latency_ms"],
                    tts_latency_ms=row["tts_latency_ms"],
                    feedback_rating=row["feedback_rating"],
                )
                for row in cursor.fetchall()
            ]

    def search_interactions(
        self,
        search: Optional[str] = None,
        animal: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_confidence: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, List[ChatInteraction]]:
        """Search interactions with filters. Returns (total_count, interactions)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["1=1"]
            params = []

            if search:
                where_clauses.append("(question LIKE ? OR answer LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])

            if animal:
                where_clauses.append("sources LIKE ?")
                params.append(f'%"{animal}"%')

            if start_date:
                where_clauses.append("timestamp >= ?")
                params.append(start_date.isoformat())

            if end_date:
                where_clauses.append("timestamp <= ?")
                params.append(end_date.isoformat())

            if min_confidence is not None:
                where_clauses.append("confidence_score >= ?")
                params.append(min_confidence)

            where_sql = " AND ".join(where_clauses)

            # Count total
            cursor.execute(f"SELECT COUNT(*) FROM chat_interactions WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            # Get page
            cursor.execute(
                f"""SELECT * FROM chat_interactions
                    WHERE {where_sql}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?""",
                params + [limit, offset]
            )

            interactions = [
                ChatInteraction(
                    id=row["id"],
                    session_id=row["session_id"],
                    timestamp=row["timestamp"],
                    question=row["question"],
                    answer=row["answer"],
                    sources=json.loads(row["sources"]) if row["sources"] else None,
                    confidence_score=row["confidence_score"],
                    latency_ms=row["latency_ms"],
                    rag_latency_ms=row["rag_latency_ms"],
                    llm_latency_ms=row["llm_latency_ms"],
                    tts_latency_ms=row["tts_latency_ms"],
                    feedback_rating=row["feedback_rating"],
                )
                for row in cursor.fetchall()
            ]

            return total, interactions

    def get_latency_breakdown(self, days: int = 7) -> LatencyBreakdown:
        """Get latency percentiles by component."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get all latency values for percentile calculation
            cursor.execute(f"""
                SELECT latency_ms, rag_latency_ms, llm_latency_ms, tts_latency_ms
                FROM chat_interactions
                WHERE timestamp >= DATE('now', '-{days} days')
                  AND latency_ms IS NOT NULL
                ORDER BY latency_ms
            """)
            rows = cursor.fetchall()

            if not rows:
                empty_stats = PercentileStats(count=0)
                return LatencyBreakdown(
                    overall=empty_stats,
                    by_component={"rag": empty_stats, "llm": empty_stats, "tts": empty_stats},
                )

            # Extract values
            overall_vals = [r["latency_ms"] for r in rows if r["latency_ms"]]
            rag_vals = [r["rag_latency_ms"] for r in rows if r["rag_latency_ms"]]
            llm_vals = [r["llm_latency_ms"] for r in rows if r["llm_latency_ms"]]
            tts_vals = [r["tts_latency_ms"] for r in rows if r["tts_latency_ms"]]

            def calc_percentiles(vals: List[int]) -> PercentileStats:
                if not vals:
                    return PercentileStats(count=0)
                sorted_vals = sorted(vals)
                n = len(sorted_vals)
                return PercentileStats(
                    p50=sorted_vals[int(n * 0.5)] if n > 0 else None,
                    p90=sorted_vals[int(n * 0.9)] if n > 0 else None,
                    p99=sorted_vals[int(n * 0.99)] if n > 0 else None,
                    avg=sum(sorted_vals) / n if n > 0 else None,
                    count=n,
                )

            return LatencyBreakdown(
                overall=calc_percentiles(overall_vals),
                by_component={
                    "rag": calc_percentiles(rag_vals),
                    "llm": calc_percentiles(llm_vals),
                    "tts": calc_percentiles(tts_vals),
                },
            )


# Global analytics service instance (lazy-loaded)
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
