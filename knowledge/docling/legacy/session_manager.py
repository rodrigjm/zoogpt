"""
Session Manager for Zoocari Chatbot
Handles unique device sessions and persistent chat history storage using SQLite.

Features:
- Device fingerprinting via browser-based session ID
- Persistent session tracking across page refreshes
- Chat history storage with timestamps
- Session metadata (created_at, last_active, message_count)
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Database path (same directory as LanceDB for consistency)
DB_PATH = Path("data/sessions.db")


def _ensure_db_exists():
    """Ensure the data directory and database exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection():
    """Context manager for database connections with proper cleanup."""
    _ensure_db_exists()
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_session_db():
    """Initialize the session database schema."""
    with get_db_connection() as conn:
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


def generate_device_fingerprint(streamlit_session_id: str, user_agent: str = "",
                                 screen_info: str = "") -> str:
    """
    Generate a stable device fingerprint from available browser info.

    Args:
        streamlit_session_id: Streamlit's internal session ID
        user_agent: Browser User-Agent string (if available)
        screen_info: Screen resolution info (if available)

    Returns:
        16-character hex fingerprint
    """
    # Combine available identifiers
    fingerprint_data = f"{streamlit_session_id}:{user_agent}:{screen_info}"

    # Generate stable hash
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]


def get_or_create_session(session_id: str, device_fingerprint: Optional[str] = None) -> dict:
    """
    Get existing session or create new one.

    Args:
        session_id: Unique session identifier (from Streamlit or cookie)
        device_fingerprint: Optional device fingerprint for tracking

    Returns:
        Session dict with id, created_at, last_active, message_count
    """
    with get_db_connection() as conn:
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
                "is_new": False
            }

        # Create new session
        cursor.execute(
            """INSERT INTO sessions (session_id, device_fingerprint, metadata)
               VALUES (?, ?, ?)""",
            (session_id, device_fingerprint, json.dumps({}))
        )
        conn.commit()

        return {
            "session_id": session_id,
            "device_fingerprint": device_fingerprint,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_count": 0,
            "is_new": True
        }


def save_message(session_id: str, role: str, content: str,
                 metadata: Optional[dict] = None) -> int | None:
    """
    Save a chat message to history.

    Args:
        session_id: Session identifier
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Optional metadata (sources, confidence, etc.)

    Returns:
        Message ID
    """
    with get_db_connection() as conn:
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


def get_chat_history(session_id: str, limit: int = 50,
                     include_metadata: bool = False) -> list[dict]:
    """
    Retrieve chat history for a session.

    Args:
        session_id: Session identifier
        limit: Maximum messages to return (most recent)
        include_metadata: Whether to include message metadata

    Returns:
        List of message dicts with role, content, timestamp
    """
    with get_db_connection() as conn:
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


def get_recent_messages(session_id: str, count: int = 10) -> list[dict]:
    """
    Get the most recent N messages for a session (for context).

    Args:
        session_id: Session identifier
        count: Number of recent messages

    Returns:
        List of recent messages (oldest first for context building)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get recent messages in descending order, then reverse
        cursor.execute(
            """SELECT role, content FROM chat_history
               WHERE session_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (session_id, count)
        )

        messages = [{"role": row["role"], "content": row["content"]}
                   for row in cursor.fetchall()]

        # Reverse to get chronological order
        return list(reversed(messages))


def get_session_stats(session_id: str) -> dict:
    """
    Get statistics for a session.

    Returns:
        Dict with message_count, first_message, last_message, duration
    """
    with get_db_connection() as conn:
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


def cleanup_old_sessions(days: int = 30):
    """
    Remove sessions older than specified days.

    Args:
        days: Number of days after which to delete sessions
    """
    cutoff = datetime.now() - timedelta(days=days)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get sessions to delete
        cursor.execute(
            "SELECT session_id FROM sessions WHERE last_active < ?",
            (cutoff.isoformat(),)
        )
        old_sessions = [row["session_id"] for row in cursor.fetchall()]

        if old_sessions:
            # Delete chat history first (foreign key)
            placeholders = ",".join("?" * len(old_sessions))
            cursor.execute(
                f"DELETE FROM chat_history WHERE session_id IN ({placeholders})",
                old_sessions
            )

            # Delete sessions
            cursor.execute(
                f"DELETE FROM sessions WHERE session_id IN ({placeholders})",
                old_sessions
            )

            conn.commit()

        return len(old_sessions)


def get_all_sessions(limit: int = 100) -> list[dict]:
    """
    Get all sessions (admin/debug use).

    Returns:
        List of session dicts
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """SELECT session_id, device_fingerprint, created_at, last_active, message_count
               FROM sessions
               ORDER BY last_active DESC
               LIMIT ?""",
            (limit,)
        )

        return [dict(row) for row in cursor.fetchall()]


# Initialize database on module import
init_session_db()
