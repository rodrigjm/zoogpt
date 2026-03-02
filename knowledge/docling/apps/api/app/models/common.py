"""
Common models used across all endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response shape per CONTRACT.md Part 4."""
    error: ErrorDetail
