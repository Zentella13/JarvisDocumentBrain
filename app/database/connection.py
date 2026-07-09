import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("JARVIS_DB_PATH", Path(__file__).resolve().parent.parent / "data" / "documents.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
