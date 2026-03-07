"""
Classification history database.

SQLite-backed storage for every classification result.
Enables temporal analysis ("how has my audience changed over time").

Uses aiosqlite for async FastAPI compatibility.
Falls back to synchronous sqlite3 for non-async contexts.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")


def _ensure_db():
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            user_id     TEXT,
            bio         TEXT NOT NULL,
            bucket      TEXT NOT NULL,
            confidence  REAL NOT NULL,
            sentiment   TEXT,
            polarity    REAL,
            engagement  INTEGER,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id  TEXT PRIMARY KEY,
            filename    TEXT,
            total_items INTEGER NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session ON classifications(session_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_created ON classifications(created_at)
    """)
    conn.commit()
    conn.close()


# Ensure DB exists on import
_ensure_db()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_session(
    session_id: str,
    classifications: List[Dict],
    filename: Optional[str] = None,
):
    """
    Save a batch of classification results to the database.

    Each item in classifications should have:
        user_id, bio, bucket, confidence, sentiment (optional),
        polarity (optional), engagement (optional)
    """
    conn = sqlite3.connect(DB_PATH)
    now = _now_iso()

    conn.execute(
        "INSERT OR REPLACE INTO sessions (session_id, filename, total_items, created_at) VALUES (?, ?, ?, ?)",
        (session_id, filename, len(classifications), now),
    )

    for c in classifications:
        conn.execute(
            """INSERT INTO classifications
               (session_id, user_id, bio, bucket, confidence, sentiment, polarity, engagement, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                c.get("user_id", ""),
                c.get("bio", ""),
                c.get("bucket", ""),
                c.get("confidence", 0.0),
                c.get("sentiment"),
                c.get("polarity"),
                c.get("engagement"),
                now,
            ),
        )

    conn.commit()
    conn.close()


def get_history(limit: int = 50) -> List[Dict]:
    """
    Get recent classification sessions with aggregate stats.

    Returns list of sessions, most recent first.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    sessions = conn.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()

    result = []
    for s in sessions:
        # Get bucket distribution for this session
        rows = conn.execute(
            "SELECT bucket, COUNT(*) as cnt FROM classifications WHERE session_id = ? GROUP BY bucket",
            (s["session_id"],),
        ).fetchall()
        distribution = {r["bucket"]: r["cnt"] for r in rows}

        # Get avg confidence
        avg_row = conn.execute(
            "SELECT AVG(confidence) as avg_conf, AVG(polarity) as avg_pol, AVG(engagement) as avg_eng FROM classifications WHERE session_id = ?",
            (s["session_id"],),
        ).fetchone()

        result.append({
            "session_id": s["session_id"],
            "filename": s["filename"],
            "total_items": s["total_items"],
            "created_at": s["created_at"],
            "distribution": distribution,
            "avg_confidence": round(avg_row["avg_conf"] or 0, 4),
            "avg_polarity": round(avg_row["avg_pol"] or 0, 4) if avg_row["avg_pol"] else None,
            "avg_engagement": round(avg_row["avg_eng"] or 0, 1) if avg_row["avg_eng"] else None,
        })

    conn.close()
    return result


def get_session_detail(session_id: str) -> Optional[Dict]:
    """Get full detail for a single session."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    session = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()

    if not session:
        conn.close()
        return None

    rows = conn.execute(
        "SELECT * FROM classifications WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()

    items = [dict(r) for r in rows]

    conn.close()
    return {
        "session_id": session["session_id"],
        "filename": session["filename"],
        "total_items": session["total_items"],
        "created_at": session["created_at"],
        "items": items,
    }


def get_timeline(days: int = 30) -> List[Dict]:
    """
    Get daily aggregate stats for the last N days.
    Useful for "how has my audience changed" timeline chart.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            DATE(created_at) as day,
            COUNT(*) as total,
            AVG(confidence) as avg_conf,
            AVG(polarity) as avg_pol,
            AVG(engagement) as avg_eng
        FROM classifications
        WHERE created_at >= datetime('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY day
    """, (f"-{days} days",)).fetchall()

    result = []
    for r in rows:
        # Get bucket distribution per day
        dist_rows = conn.execute("""
            SELECT bucket, COUNT(*) as cnt
            FROM classifications
            WHERE DATE(created_at) = ?
            GROUP BY bucket
        """, (r["day"],)).fetchall()
        distribution = {d["bucket"]: d["cnt"] for d in dist_rows}

        result.append({
            "date": r["day"],
            "total": r["total"],
            "avg_confidence": round(r["avg_conf"] or 0, 4),
            "avg_polarity": round(r["avg_pol"] or 0, 4) if r["avg_pol"] else None,
            "avg_engagement": round(r["avg_eng"] or 0, 1) if r["avg_eng"] else None,
            "distribution": distribution,
        })

    conn.close()
    return result


def clear_history():
    """Delete all history data."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM classifications")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()
