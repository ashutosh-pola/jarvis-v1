import sqlite3
import logging
from typing import List, Dict, Any
from config import DB_PATH, MAX_CONTEXT_TURNS

logger = logging.getLogger("jarvis.memory")

class ConversationMemory:
    """Persistent SQLite-backed rolling context memory for Jarvis."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create sqlite tables if not present."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing SQLite memory DB: {e}")

    def add_message(self, role: str, content: str):
        """Insert user or assistant turn into SQLite database."""
        if not content or not content.strip():
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO history (role, content) VALUES (?, ?)", (role, content.strip()))
                conn.commit()
            self._trim_history()
        except Exception as e:
            logger.error(f"Error inserting memory turn: {e}")

    def get_recent_history(self, limit: int = MAX_CONTEXT_TURNS) -> List[Dict[str, str]]:
        """Retrieve recent conversation history formatted for model messages."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content FROM history
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                # Reverse to chronological order
                return [{"role": r, "content": c} for r, c in reversed(rows)]
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            return []

    def clear_history(self):
        """Clear all stored history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history")
                conn.commit()
            logger.info("Memory history cleared.")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")

    def _trim_history(self, keep_last: int = MAX_CONTEXT_TURNS * 2):
        """Keep database small to preserve RAM and fast query times."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM history WHERE id NOT IN (
                        SELECT id FROM history ORDER BY id DESC LIMIT ?
                    )
                """, (keep_last,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error trimming memory: {e}")

# Global memory instance
memory = ConversationMemory()
