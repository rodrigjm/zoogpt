"""
Analytics API endpoints for Admin Portal.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import get_current_user, User
from config import settings
from models.analytics import (
    DashboardResponse,
    TodayMetrics,
    DailyTrend,
    TopQuestion,
    TopAnimal,
    SessionListResponse,
    SessionSummary,
    InteractionListResponse,
    InteractionDetail,
    LatencyBreakdownResponse,
    PercentileStats,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_db_connection():
    """Get SQLite connection to sessions.db."""
    db_path = settings.session_db_absolute
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
):
    """
    Get dashboard summary metrics.

    Returns today's stats, trends over the last N days,
    top questions, and most queried animals.
    """
    conn = get_db_connection()
    try:
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

        # Error rate (low confidence as proxy)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN confidence_score < 0.3 THEN 1 ELSE 0 END) as low_conf
            FROM chat_interactions
            WHERE DATE(timestamp) = DATE('now')
        """)
        err_row = cursor.fetchone()
        total = err_row["total"] or 1
        error_rate = (err_row["low_conf"] or 0) / total

        today = TodayMetrics(
            sessions=today_row["sessions"] or 0,
            questions=today_row["questions"] or 0,
            avg_latency_ms=today_row["avg_latency"],
            error_rate=round(error_rate, 4),
        )

        # Trends
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
            DailyTrend(
                date=row["date"],
                sessions=row["sessions"],
                questions=row["questions"],
                avg_latency_ms=row["avg_latency"],
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
            TopQuestion(question=row["question"], count=row["count"])
            for row in cursor.fetchall()
        ]

        # Top animals (from sources JSON)
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
            [TopAnimal(name=k, count=v) for k, v in animal_counts.items()],
            key=lambda x: x.count,
            reverse=True,
        )[:10]

        return DashboardResponse(
            today=today,
            trends=trends,
            top_questions=top_questions,
            top_animals=top_animals,
        )
    finally:
        conn.close()


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """Get list of sessions with optional date filtering."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Build query
        where_clauses = ["1=1"]
        params: List[Any] = []

        if start_date:
            where_clauses.append("start_time >= ?")
            params.append(start_date.isoformat())
        if end_date:
            where_clauses.append("start_time <= ?")
            params.append(end_date.isoformat())

        where_sql = " AND ".join(where_clauses)

        # Get total count
        cursor.execute(
            f"SELECT COUNT(*) FROM session_metrics WHERE {where_sql}",
            params,
        )
        total = cursor.fetchone()[0]

        # Get sessions
        cursor.execute(
            f"""SELECT
                session_id, start_time, end_time, message_count,
                avg_response_latency_ms, client_type
            FROM session_metrics
            WHERE {where_sql}
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )

        sessions = []
        for row in cursor.fetchall():
            duration = None
            if row["end_time"]:
                try:
                    start = datetime.fromisoformat(row["start_time"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(row["end_time"].replace("Z", "+00:00"))
                    duration = int((end - start).total_seconds())
                except (ValueError, AttributeError):
                    pass

            sessions.append(SessionSummary(
                session_id=row["session_id"],
                start_time=row["start_time"],
                duration_seconds=duration,
                message_count=row["message_count"],
                avg_latency_ms=row["avg_response_latency_ms"],
                client_type=row["client_type"],
            ))

        return SessionListResponse(total=total, sessions=sessions)
    finally:
        conn.close()


@router.get("/sessions/{session_id}/interactions", response_model=InteractionListResponse)
async def get_session_interactions(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
):
    """Get all Q&A interactions for a specific session."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """SELECT * FROM chat_interactions
               WHERE session_id = ?
               ORDER BY timestamp ASC
               LIMIT ?""",
            (session_id, limit),
        )

        interactions = []
        for row in cursor.fetchall():
            interactions.append(InteractionDetail(
                id=row["id"],
                timestamp=row["timestamp"],
                question=row["question"],
                answer=row["answer"],
                sources=json.loads(row["sources"]) if row["sources"] else None,
                confidence_score=row["confidence_score"],
                latency_ms=row["latency_ms"],
                rag_latency_ms=row["rag_latency_ms"],
                llm_latency_ms=row["llm_latency_ms"],
                tts_latency_ms=row["tts_latency_ms"],
            ))

        return InteractionListResponse(total=len(interactions), interactions=interactions)
    finally:
        conn.close()


@router.get("/interactions", response_model=InteractionListResponse)
async def search_interactions(
    search: Optional[str] = None,
    animal: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_confidence: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """Search across all Q&A interactions with filters."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        where_clauses = ["1=1"]
        params: List[Any] = []

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

        # Get total
        cursor.execute(
            f"SELECT COUNT(*) FROM chat_interactions WHERE {where_sql}",
            params,
        )
        total = cursor.fetchone()[0]

        # Get interactions
        cursor.execute(
            f"""SELECT * FROM chat_interactions
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )

        interactions = []
        for row in cursor.fetchall():
            interactions.append(InteractionDetail(
                id=row["id"],
                timestamp=row["timestamp"],
                question=row["question"],
                answer=row["answer"],
                sources=json.loads(row["sources"]) if row["sources"] else None,
                confidence_score=row["confidence_score"],
                latency_ms=row["latency_ms"],
                rag_latency_ms=row["rag_latency_ms"],
                llm_latency_ms=row["llm_latency_ms"],
                tts_latency_ms=row["tts_latency_ms"],
            ))

        return InteractionListResponse(total=total, interactions=interactions)
    finally:
        conn.close()


@router.get("/latency-breakdown", response_model=LatencyBreakdownResponse)
async def get_latency_breakdown(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
):
    """Get latency percentiles by component."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT latency_ms, rag_latency_ms, llm_latency_ms, tts_latency_ms
            FROM chat_interactions
            WHERE timestamp >= DATE('now', '-{days} days')
              AND latency_ms IS NOT NULL
            ORDER BY latency_ms
        """)
        rows = cursor.fetchall()

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

        overall = [r["latency_ms"] for r in rows if r["latency_ms"]]
        rag = [r["rag_latency_ms"] for r in rows if r["rag_latency_ms"]]
        llm = [r["llm_latency_ms"] for r in rows if r["llm_latency_ms"]]
        tts = [r["tts_latency_ms"] for r in rows if r["tts_latency_ms"]]

        return LatencyBreakdownResponse(
            overall=calc_percentiles(overall),
            rag=calc_percentiles(rag),
            llm=calc_percentiles(llm),
            tts=calc_percentiles(tts),
        )
    finally:
        conn.close()
