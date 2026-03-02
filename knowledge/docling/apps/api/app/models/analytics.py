"""
Analytics Pydantic models for Admin Portal.
Tracks chat interactions, session metrics, and daily aggregates.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date


# =============================================================================
# Chat Interaction Models
# =============================================================================

class ChatInteraction(BaseModel):
    """Single Q&A interaction with timing data."""
    id: int
    session_id: str
    timestamp: datetime
    question: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    latency_ms: int
    rag_latency_ms: Optional[int] = None
    llm_latency_ms: Optional[int] = None
    tts_latency_ms: Optional[int] = None
    feedback_rating: Optional[int] = None


class ChatInteractionCreate(BaseModel):
    """Data for recording a new interaction."""
    session_id: str
    question: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    latency_ms: int
    rag_latency_ms: Optional[int] = None
    llm_latency_ms: Optional[int] = None
    tts_latency_ms: Optional[int] = None


# =============================================================================
# Session Metrics Models
# =============================================================================

class SessionMetrics(BaseModel):
    """Aggregated metrics for a single session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    message_count: int = 0
    avg_response_latency_ms: Optional[float] = None
    voice_requests: int = 0
    client_type: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


class SessionSummary(BaseModel):
    """Session summary for list views."""
    session_id: str
    start_time: datetime
    duration_seconds: Optional[int] = None
    message_count: int
    avg_latency_ms: Optional[float] = None
    client_type: Optional[str] = None


# =============================================================================
# Daily Analytics Models
# =============================================================================

class DailyAnalytics(BaseModel):
    """Daily aggregate metrics."""
    date: date
    total_sessions: int = 0
    total_questions: int = 0
    avg_session_duration_sec: Optional[float] = None
    avg_response_latency_ms: Optional[float] = None
    unique_animals_queried: Optional[List[str]] = None
    top_questions: Optional[List[Dict[str, Any]]] = None
    error_count: int = 0


# =============================================================================
# Dashboard Models
# =============================================================================

class DashboardMetrics(BaseModel):
    """Real-time dashboard summary."""
    today: "TodayMetrics"
    trends: List[DailyAnalytics]
    top_questions: List[Dict[str, Any]]
    top_animals: List[Dict[str, Any]]


class TodayMetrics(BaseModel):
    """Today's summary metrics."""
    sessions: int = 0
    questions: int = 0
    avg_latency_ms: Optional[float] = None
    error_rate: float = 0.0


class LatencyBreakdown(BaseModel):
    """Latency percentiles by component."""
    overall: "PercentileStats"
    by_component: Dict[str, "PercentileStats"]


class PercentileStats(BaseModel):
    """Percentile statistics."""
    p50: Optional[float] = None
    p90: Optional[float] = None
    p99: Optional[float] = None
    avg: Optional[float] = None
    count: int = 0


# =============================================================================
# Query/Filter Models
# =============================================================================

class InteractionQuery(BaseModel):
    """Query parameters for searching interactions."""
    search: Optional[str] = None
    animal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = None
    limit: int = 50
    offset: int = 0


class SessionQuery(BaseModel):
    """Query parameters for listing sessions."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_duration: Optional[int] = None
    client_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


# Forward references for nested models
DashboardMetrics.model_rebuild()
LatencyBreakdown.model_rebuild()
