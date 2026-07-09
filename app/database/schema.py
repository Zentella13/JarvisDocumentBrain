from app.database.connection import get_connection


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            path TEXT UNIQUE NOT NULL,
            extension TEXT,
            size_bytes INTEGER,
            sha256 TEXT,
            last_modified TEXT,
            indexed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()
