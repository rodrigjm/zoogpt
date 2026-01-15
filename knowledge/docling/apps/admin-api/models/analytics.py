"""Analytics models for Admin API."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class TodayMetrics(BaseModel):
    """Today's summary metrics."""
    sessions: int = 0
    questions: int = 0
    avg_latency_ms: Optional[float] = None
    error_rate: float = 0.0


class DailyTrend(BaseModel):
    """Daily trend data point."""
    date: str
    sessions: int
    questions: int
    avg_latency_ms: Optional[float] = None


class TopQuestion(BaseModel):
    """Frequently asked question."""
    question: str
    count: int


class TopAnimal(BaseModel):
    """Frequently queried animal."""
    name: str
    count: int


class DashboardResponse(BaseModel):
    """Dashboard summary response."""
    today: TodayMetrics
    trends: List[DailyTrend]
    top_questions: List[TopQuestion]
    top_animals: List[TopAnimal]


class SessionSummary(BaseModel):
    """Session list item."""
    session_id: str
    start_time: datetime
    duration_seconds: Optional[int] = None
    message_count: int
    avg_latency_ms: Optional[float] = None
    client_type: Optional[str] = None


class SessionListResponse(BaseModel):
    """Session list response."""
    total: int
    sessions: List[SessionSummary]


class InteractionDetail(BaseModel):
    """Single Q&A interaction."""
    id: int
    timestamp: datetime
    question: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    latency_ms: int
    rag_latency_ms: Optional[int] = None
    llm_latency_ms: Optional[int] = None
    tts_latency_ms: Optional[int] = None


class InteractionListResponse(BaseModel):
    """Interaction search response."""
    total: int
    interactions: List[InteractionDetail]


class PercentileStats(BaseModel):
    """Latency percentile statistics."""
    p50: Optional[float] = None
    p90: Optional[float] = None
    p99: Optional[float] = None
    avg: Optional[float] = None
    count: int = 0


class LatencyBreakdownResponse(BaseModel):
    """Latency breakdown by component."""
    overall: PercentileStats
    rag: PercentileStats
    llm: PercentileStats
    tts: PercentileStats
