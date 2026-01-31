"""
Knowledge Base management API endpoints.
"""

import os
import sqlite3
import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from auth import get_current_user, User
from config import settings
from models.kb import (
    AnimalCreate,
    AnimalUpdate,
    AnimalResponse,
    AnimalDetailResponse,
    AnimalListResponse,
    SourceCreate,
    SourceResponse,
    IndexStatus,
    IndexRebuildResponse,
    IndexPendingStatus,
)
from services.indexer import IndexerService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

# =============================================================================
# Auto-Rebuild State Management
# =============================================================================

DEBOUNCE_SECONDS = 30  # Wait 30 seconds after last change before auto-rebuild

_rebuild_state = {
    "changes_pending": False,
    "last_change_at": None,
    "debounce_task": None,
}


async def schedule_debounced_rebuild():
    """Wait for debounce period, then trigger rebuild if still pending."""
    try:
        await asyncio.sleep(DEBOUNCE_SECONDS)
        if _rebuild_state["changes_pending"]:
            logger.info("Auto-rebuild triggered after debounce period")
            # Create job in database
            conn = get_db_connection()
            try:
                cursor = conn.cursor()

                # Check if rebuild already running
                cursor.execute("""
                    SELECT job_id FROM kb_index_history
                    WHERE status = 'running'
                """)
                if cursor.fetchone():
                    logger.info("Skipping auto-rebuild - rebuild already in progress")
                    return

                job_id = str(uuid.uuid4())
                started_at = datetime.utcnow()

                cursor.execute(
                    """INSERT INTO kb_index_history (job_id, started_at, status)
                       VALUES (?, ?, 'running')""",
                    (job_id, started_at),
                )
                conn.commit()

                # Run the rebuild
                await run_index_rebuild(job_id)

            finally:
                conn.close()

            _rebuild_state["changes_pending"] = False
            _rebuild_state["last_change_at"] = None
    except asyncio.CancelledError:
        logger.debug("Debounced rebuild cancelled (new changes detected)")
    except Exception as e:
        logger.error(f"Auto-rebuild failed: {e}", exc_info=True)


def mark_changes_pending():
    """Called after any source CRUD operation to schedule auto-rebuild."""
    _rebuild_state["changes_pending"] = True
    _rebuild_state["last_change_at"] = datetime.utcnow()

    # Cancel existing debounce task
    if _rebuild_state["debounce_task"] and not _rebuild_state["debounce_task"].done():
        _rebuild_state["debounce_task"].cancel()

    # Start new debounce timer
    _rebuild_state["debounce_task"] = asyncio.create_task(
        schedule_debounced_rebuild()
    )
    logger.info(f"Changes pending, auto-rebuild scheduled in {DEBOUNCE_SECONDS}s")


def get_db_connection():
    """Get SQLite connection."""
    db_path = settings.session_db_absolute
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_kb_schema():
    """Initialize KB tables if they don't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_animals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                category TEXT,
                source_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                content TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                last_indexed DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES kb_animals(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_index_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                status TEXT DEFAULT 'running',
                total_documents INTEGER,
                total_chunks INTEGER,
                error_message TEXT
            )
        """)

        conn.commit()
    finally:
        conn.close()


# Initialize schema on module load
init_kb_schema()


# =============================================================================
# Animals CRUD
# =============================================================================

@router.get("/animals", response_model=AnimalListResponse)
async def list_animals(
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """List all animals in the knowledge base."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        where_clauses = ["1=1"]
        params: List = []

        if search:
            where_clauses.append("(name LIKE ? OR display_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if category:
            where_clauses.append("category = ?")
            params.append(category)
        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(is_active)

        where_sql = " AND ".join(where_clauses)

        cursor.execute(f"SELECT COUNT(*) FROM kb_animals WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(
            f"""SELECT * FROM kb_animals
                WHERE {where_sql}
                ORDER BY display_name ASC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )

        animals = [
            AnimalResponse(
                id=row["id"],
                name=row["name"],
                display_name=row["display_name"],
                category=row["category"],
                source_count=row["source_count"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in cursor.fetchall()
        ]

        return AnimalListResponse(total=total, animals=animals)
    finally:
        conn.close()


@router.post("/animals", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    body: AnimalCreate,
    user: User = Depends(get_current_user),
):
    """Add a new animal to the knowledge base."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if name already exists
        cursor.execute("SELECT id FROM kb_animals WHERE name = ?", (body.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Animal with name '{body.name}' already exists",
            )

        cursor.execute(
            """INSERT INTO kb_animals (name, display_name, category)
               VALUES (?, ?, ?)""",
            (body.name, body.display_name, body.category),
        )
        conn.commit()

        animal_id = cursor.lastrowid
        cursor.execute("SELECT * FROM kb_animals WHERE id = ?", (animal_id,))
        row = cursor.fetchone()

        return AnimalResponse(
            id=row["id"],
            name=row["name"],
            display_name=row["display_name"],
            category=row["category"],
            source_count=row["source_count"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    finally:
        conn.close()


@router.get("/animals/{animal_id}", response_model=AnimalDetailResponse)
async def get_animal(
    animal_id: int,
    user: User = Depends(get_current_user),
):
    """Get animal details with sources."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM kb_animals WHERE id = ?", (animal_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with id {animal_id} not found",
            )

        cursor.execute(
            "SELECT * FROM kb_sources WHERE animal_id = ? ORDER BY created_at DESC",
            (animal_id,),
        )
        sources = [
            SourceResponse(
                id=src["id"],
                title=src["title"],
                url=src["url"],
                chunk_count=src["chunk_count"],
                last_indexed=src["last_indexed"],
                created_at=src["created_at"],
            )
            for src in cursor.fetchall()
        ]

        return AnimalDetailResponse(
            id=row["id"],
            name=row["name"],
            display_name=row["display_name"],
            category=row["category"],
            source_count=row["source_count"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            sources=sources,
        )
    finally:
        conn.close()


@router.put("/animals/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: int,
    body: AnimalUpdate,
    user: User = Depends(get_current_user),
):
    """Update animal metadata."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM kb_animals WHERE id = ?", (animal_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with id {animal_id} not found",
            )

        updates = []
        params = []
        if body.display_name is not None:
            updates.append("display_name = ?")
            params.append(body.display_name)
        if body.category is not None:
            updates.append("category = ?")
            params.append(body.category)
        if body.is_active is not None:
            updates.append("is_active = ?")
            params.append(body.is_active)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            cursor.execute(
                f"UPDATE kb_animals SET {', '.join(updates)} WHERE id = ?",
                params + [animal_id],
            )
            conn.commit()

        cursor.execute("SELECT * FROM kb_animals WHERE id = ?", (animal_id,))
        row = cursor.fetchone()

        return AnimalResponse(
            id=row["id"],
            name=row["name"],
            display_name=row["display_name"],
            category=row["category"],
            source_count=row["source_count"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    finally:
        conn.close()


@router.delete("/animals/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: int,
    user: User = Depends(get_current_user),
):
    """Delete an animal and its sources."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if animal exists and has sources
        cursor.execute("SELECT id, source_count FROM kb_animals WHERE id = ?", (animal_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with id {animal_id} not found",
            )

        has_sources = row["source_count"] > 0

        cursor.execute("DELETE FROM kb_animals WHERE id = ?", (animal_id,))
        conn.commit()

        # Mark changes pending if animal had sources (affects vector index)
        if has_sources:
            mark_changes_pending()
    finally:
        conn.close()


# =============================================================================
# Sources CRUD
# =============================================================================

@router.post("/animals/{animal_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def add_source(
    animal_id: int,
    body: SourceCreate,
    user: User = Depends(get_current_user),
):
    """Add a source document to an animal."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM kb_animals WHERE id = ?", (animal_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Animal with id {animal_id} not found",
            )

        cursor.execute(
            """INSERT INTO kb_sources (animal_id, title, url, content)
               VALUES (?, ?, ?, ?)""",
            (animal_id, body.title, body.url, body.content),
        )

        # Update source count
        cursor.execute(
            """UPDATE kb_animals
               SET source_count = source_count + 1, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (animal_id,),
        )
        conn.commit()

        source_id = cursor.lastrowid
        cursor.execute("SELECT * FROM kb_sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()

        # Mark changes pending for auto-rebuild
        mark_changes_pending()

        return SourceResponse(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            chunk_count=row["chunk_count"],
            last_indexed=row["last_indexed"],
            created_at=row["created_at"],
        )
    finally:
        conn.close()


@router.delete("/animals/{animal_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    animal_id: int,
    source_id: int,
    user: User = Depends(get_current_user),
):
    """Delete a source document."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM kb_sources WHERE id = ? AND animal_id = ?",
            (source_id, animal_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source {source_id} not found for animal {animal_id}",
            )

        cursor.execute("DELETE FROM kb_sources WHERE id = ?", (source_id,))

        # Update source count
        cursor.execute(
            """UPDATE kb_animals
               SET source_count = source_count - 1, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (animal_id,),
        )
        conn.commit()

        # Mark changes pending for auto-rebuild
        mark_changes_pending()
    finally:
        conn.close()


# =============================================================================
# Index Management
# =============================================================================

@router.get("/index/status", response_model=IndexStatus)
async def get_index_status(
    user: User = Depends(get_current_user),
):
    """Get current vector index status."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Get latest rebuild info
        cursor.execute("""
            SELECT * FROM kb_index_history
            ORDER BY started_at DESC LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            return IndexStatus(
                status="ready",
                last_rebuild=None,
                document_count=0,
                chunk_count=0,
            )

        return IndexStatus(
            status=row["status"],
            last_rebuild=row["completed_at"] or row["started_at"],
            document_count=row["total_documents"] or 0,
            chunk_count=row["total_chunks"] or 0,
            error_message=row["error_message"],
        )
    finally:
        conn.close()


@router.get("/index/pending", response_model=IndexPendingStatus)
async def get_index_pending_status(
    user: User = Depends(get_current_user),
):
    """Check if there are pending changes requiring index rebuild."""
    pending = _rebuild_state["changes_pending"]
    last_change_at = _rebuild_state["last_change_at"]

    auto_rebuild_in_seconds = None
    if pending and last_change_at:
        elapsed = (datetime.utcnow() - last_change_at).total_seconds()
        remaining = max(0, int(DEBOUNCE_SECONDS - elapsed))
        auto_rebuild_in_seconds = remaining

    return IndexPendingStatus(
        pending=pending,
        last_change_at=last_change_at,
        auto_rebuild_in_seconds=auto_rebuild_in_seconds,
    )


@router.post("/index/rebuild", response_model=IndexRebuildResponse)
async def rebuild_index(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """
    Trigger a full vector index rebuild.

    This runs in the background. Check /index/status for progress.
    """
    # Clear pending state since we're doing a manual rebuild
    if _rebuild_state["debounce_task"] and not _rebuild_state["debounce_task"].done():
        _rebuild_state["debounce_task"].cancel()
    _rebuild_state["changes_pending"] = False
    _rebuild_state["last_change_at"] = None

    # Check for OpenAI API key first
    api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY not configured. Cannot generate embeddings.",
        )

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if rebuild already running
        cursor.execute("""
            SELECT job_id FROM kb_index_history
            WHERE status = 'running'
        """)
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Index rebuild already in progress",
            )

        # Create new job
        job_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        cursor.execute(
            """INSERT INTO kb_index_history (job_id, started_at, status)
               VALUES (?, ?, 'running')""",
            (job_id, started_at),
        )
        conn.commit()

        # Schedule background task
        background_tasks.add_task(run_index_rebuild, job_id)

        return IndexRebuildResponse(
            job_id=job_id,
            status="started",
            started_at=started_at,
        )
    finally:
        conn.close()


async def run_index_rebuild(job_id: str):
    """
    Background task to rebuild the vector index.

    Steps:
    1. Read all sources from kb_sources
    2. Chunk text
    3. Generate embeddings via OpenAI
    4. Write to LanceDB
    """
    logger.info(f"Starting index rebuild job: {job_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Initialize indexer service
        indexer = IndexerService(conn)
        logger.info("IndexerService initialized")

        # Run the rebuild process
        logger.info("Running rebuild...")
        total_documents, total_chunks = indexer.rebuild_index()
        logger.info(f"Rebuild complete: {total_documents} docs, {total_chunks} chunks")

        # Update job status
        cursor.execute(
            """UPDATE kb_index_history
               SET status = 'completed',
                   completed_at = CURRENT_TIMESTAMP,
                   total_documents = ?,
                   total_chunks = ?
               WHERE job_id = ?""",
            (total_documents, total_chunks, job_id),
        )
        conn.commit()
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Index rebuild failed: {type(e).__name__}: {e}", exc_info=True)
        cursor.execute(
            """UPDATE kb_index_history
               SET status = 'failed',
                   completed_at = CURRENT_TIMESTAMP,
                   error_message = ?
               WHERE job_id = ?""",
            (str(e), job_id),
        )
        conn.commit()
    finally:
        conn.close()
