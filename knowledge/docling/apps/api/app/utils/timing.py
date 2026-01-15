"""
Timing utility for end-to-end request tracing.
Provides timestamped print statements for understanding user experience latency.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class ComponentTimings:
    """Stores component-level latency measurements."""
    rag_ms: Optional[int] = None
    llm_ms: Optional[int] = None
    tts_ms: Optional[int] = None
    total_ms: Optional[int] = None


class RequestTimer:
    """Timer for tracking request latency with timestamped prints."""

    def __init__(self, request_type: str, request_id: Optional[str] = None):
        self.start_time = time.perf_counter()
        self.request_type = request_type
        self.request_id = request_id or datetime.now().strftime("%H%M%S%f")[:10]
        self.component_timings: Dict[str, int] = {}
        self._component_start: Optional[float] = None
        self._component_name: Optional[str] = None
        self._print(f"▶ START {request_type}")

    def _print(self, message: str):
        """Print with timestamp and elapsed time."""
        elapsed = (time.perf_counter() - self.start_time) * 1000  # ms
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{self.request_id}] [{elapsed:7.1f}ms] {message}")

    def mark(self, action: str):
        """Mark a point in the request flow."""
        self._print(f"  • {action}")

    @contextmanager
    def component(self, name: str):
        """
        Context manager for timing a component.

        Usage:
            with timer.component("rag"):
                # do RAG stuff
            # timer.component_timings["rag"] now contains duration in ms
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self.component_timings[name] = elapsed_ms

    def get_timings(self) -> ComponentTimings:
        """Get component timings as a structured object."""
        return ComponentTimings(
            rag_ms=self.component_timings.get("rag"),
            llm_ms=self.component_timings.get("llm"),
            tts_ms=self.component_timings.get("tts"),
            total_ms=int((time.perf_counter() - self.start_time) * 1000),
        )

    def end(self, status: str = "COMPLETE") -> int:
        """Mark the end of the request. Returns total elapsed time in ms."""
        elapsed = int((time.perf_counter() - self.start_time) * 1000)
        self._print(f"◀ END {self.request_type} ({status}) - Total: {elapsed}ms")
        return elapsed


def timed_print(message: str):
    """Simple timestamped print without a timer context."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")
