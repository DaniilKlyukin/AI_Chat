import sqlite3
import time
from typing import Dict, List
from app.core.config import settings

class HistoryService:
    def __init__(self):
        self.db_path = str(settings.DB_PATH)
        self._init_db()
        self.MAX_HISTORY = 30

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history 
                (session_id TEXT, role TEXT, content TEXT, timestamp REAL)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits
                (session_id TEXT, model_id TEXT, last_time REAL, PRIMARY KEY(session_id, model_id))
            """)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT role, content FROM history WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            return [{"role": r, "content": c} for r, c in rows]

    def add_message(self, session_id: str, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time())
            )

    def replace_with_summary(self, session_id: str, count: int, summary: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT rowid FROM history WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, count)
            )
            ids = [r[0] for r in cursor.fetchall()]
            if ids:
                conn.execute(f"DELETE FROM history WHERE rowid IN ({','.join(map(str, ids))})")
                conn.execute(
                    "INSERT INTO history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                    (session_id, "assistant", summary, time.time() - 100)
                )

    def clear(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM history WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM rate_limits WHERE session_id = ?", (session_id,))

    def get_display_history(self, session_id: str) -> List[Dict[str, str]]:
        return self.get_history(session_id)

    def check_rate_limit(self, session_id: str, model_id: str, cooldown: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_time FROM rate_limits WHERE session_id = ? AND model_id = ?",
                (session_id, model_id)
            )
            row = cursor.fetchone()
            if row:
                elapsed = time.time() - row[0]
                if elapsed < cooldown:
                    return int(cooldown - elapsed)
            return 0

    def update_timestamp(self, session_id: str, model_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO rate_limits (session_id, model_id, last_time) VALUES (?, ?, ?)",
                (session_id, model_id, time.time())
            )

history_manager = HistoryService()