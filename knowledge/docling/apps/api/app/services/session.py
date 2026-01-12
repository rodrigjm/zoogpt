"""
Session Service for SQLite-based persistence.
Ported from legacy/session_manager.py per migration.md Task 1.2.

Provides:
- Session CRUD operations
- Chat message history persistence
- Session statistics and metadata
- Backward compatible with legacy sessions.db schema
"""

import sqlite3
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from ..config import settings


class SessionService:
    """
    Session service with SQLite persistence.
    Maintains backward compatibility with legacy session_manager.py schema.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize session service.

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
        """
        Initialize database schema.
        Schema matches legacy/session_manager.py exactly for backward compatibility.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table - tracks unique devices/browsers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    device_fingerprint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    metadata JSON
                )
            """)

            # Chat history table - stores all messages per session
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)

            # Index for faster session lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_session
                ON chat_history(session_id)
            """)

            # Index for timestamp-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp
                ON chat_history(session_id, timestamp DESC)
            """)

            conn.commit()

    def get_or_create_session(
        self,
        session_id: str,
        device_fingerprint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one.

        Args:
            session_id: Unique session identifier
            device_fingerprint: Optional device fingerprint for tracking
            metadata: Optional metadata for new sessions

        Returns:
            Session dict with id, created_at, last_active, message_count, is_new
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Try to get existing session
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update last_active timestamp
                cursor.execute(
                    "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()

                return {
                    "session_id": row["session_id"],
                    "device_fingerprint": row["device_fingerprint"],
                    "created_at": row["created_at"],
                    "last_active": row["last_active"],
                    "message_count": row["message_count"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "is_new": False
                }

            # Create new session
            metadata_json = json.dumps(metadata or {})
            cursor.execute(
                """INSERT INTO sessions (session_id, device_fingerprint, metadata)
                   VALUES (?, ?, ?)""",
                (session_id, device_fingerprint, metadata_json)
            )
            conn.commit()

            return {
                "session_id": session_id,
                "device_fingerprint": device_fingerprint,
                "created_at": datetime.now(UTC).isoformat(),
                "last_active": datetime.now(UTC).isoformat(),
                "message_count": 0,
                "metadata": metadata or {},
                "is_new": True
            }

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Save a chat message to history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (sources, confidence, etc.)

        Returns:
            Message ID (integer primary key)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert message
            cursor.execute(
                """INSERT INTO chat_history (session_id, role, content, metadata)
                   VALUES (?, ?, ?, ?)""",
                (session_id, role, content, json.dumps(metadata or {}))
            )
            message_id = cursor.lastrowid

            # Update session message count and last_active
            cursor.execute(
                """UPDATE sessions
                   SET message_count = message_count + 1, last_active = CURRENT_TIMESTAMP
                   WHERE session_id = ?""",
                (session_id,)
            )

            conn.commit()
            return message_id

    def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return (most recent)
            include_metadata: Whether to include message metadata

        Returns:
            List of message dicts with role, content, timestamp
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """SELECT role, content, timestamp, metadata
                   FROM chat_history
                   WHERE session_id = ?
                   ORDER BY id ASC
                   LIMIT ?""",
                (session_id, limit)
            )

            messages = []
            for row in cursor.fetchall():
                msg = {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                }
                if include_metadata and row["metadata"]:
                    msg["metadata"] = json.loads(row["metadata"])
                messages.append(msg)

            return messages

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with message_count, first_message, last_message
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """SELECT
                    COUNT(*) as message_count,
                    MIN(timestamp) as first_message,
                    MAX(timestamp) as last_message
                   FROM chat_history
                   WHERE session_id = ?""",
                (session_id,)
            )
            row = cursor.fetchone()

            return {
                "message_count": row["message_count"] or 0,
                "first_message": row["first_message"],
                "last_message": row["last_message"]
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session dict or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "session_id": row["session_id"],
                "device_fingerprint": row["device_fingerprint"],
                "created_at": row["created_at"],
                "last_active": row["last_active"],
                "message_count": row["message_count"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
