import sqlite3
import json
from datetime import datetime
from vanta.config import DB_PATH

def init_db():
    """Create sqlite database schemas for memory, history, and settings."""
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request TEXT NOT NULL,
                tools_used TEXT,
                findings TEXT,
                recommendations TEXT,
                action_approved INTEGER DEFAULT 0,
                action_completed INTEGER DEFAULT 0,
                verification TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        con.commit()

def log_session(request: str, tools_used: list, findings: list, recommendations: str,
                action_approved: bool = False, action_completed: bool = False, verification: str = ""):
    """Save user interaction session details to local SQLite history database."""
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO history (timestamp, request, tools_used, findings, recommendations, action_approved, action_completed, verification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().astimezone().isoformat(timespec="seconds"),
            request,
            ", ".join(tools_used),
            json.dumps(findings),
            recommendations,
            1 if action_approved else 0,
            1 if action_completed else 0,
            verification
        ))
        con.commit()

def get_history(limit: int = 50) -> list:
    """Get list of past diagnostic sessions."""
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("""
            SELECT id, timestamp, request, tools_used, recommendations, action_completed, verification
            FROM history ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        
    sessions = []
    for r in rows:
        sessions.append({
            "id": r[0],
            "timestamp": r[1],
            "request": r[2],
            "tools": r[3],
            "recommendations": r[4],
            "completed": bool(r[5]),
            "verification": r[6]
        })
    return sessions

def get_last_scan_report() -> dict:
    """Get the findings and score of the most recent diagnostic scan."""
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("""
            SELECT findings, timestamp, request FROM history 
            WHERE request LIKE '%scan%' OR request LIKE '%check%' 
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        
    if row and row[0]:
        try:
            return {
                "findings": json.loads(row[0]),
                "timestamp": row[1],
                "request": row[2]
            }
        except Exception:
            pass
    return {}
