"""Knowledge Base models for Admin API."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AnimalCreate(BaseModel):
    """Create animal request."""
    name: str
    display_name: str
    category: Optional[str] = None


class AnimalUpdate(BaseModel):
    """Update animal request."""
    display_name: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class SourceCreate(BaseModel):
    """Create source document request."""
    title: str
    url: Optional[str] = None
    content: str


class SourceResponse(BaseModel):
    """Source document response."""
    id: int
    title: str
    url: Optional[str] = None
    chunk_count: int = 0
    last_indexed: Optional[datetime] = None
    created_at: datetime


class AnimalResponse(BaseModel):
    """Animal response."""
    id: int
    name: str
    display_name: str
    category: Optional[str] = None
    source_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class AnimalDetailResponse(AnimalResponse):
    """Animal with sources."""
    sources: List[SourceResponse] = []


class AnimalListResponse(BaseModel):
    """Animal list response."""
    total: int
    animals: List[AnimalResponse]


class IndexStatus(BaseModel):
    """Vector index status."""
    status: str  # "ready", "rebuilding", "failed"
    last_rebuild: Optional[datetime] = None
    document_count: int = 0
    chunk_count: int = 0
    error_message: Optional[str] = None


class IndexRebuildResponse(BaseModel):
    """Index rebuild job response."""
    job_id: str
    status: str
    started_at: datetime
