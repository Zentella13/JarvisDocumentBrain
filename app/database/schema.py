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

    cursor.execute("PRAGMA table_info(documents)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    migrations = {
        "extension": "TEXT",
 "size_bytes": "INTEGER",
        "sha256": "TEXT",
        "last_modified": "TEXT",
        "indexed_at": "TEXT",
    }
    for column_name, column_type in migrations.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN {column_name} {column_type}")
    conn.commit()

    cursor.execute(
        """
        DELETE FROM documents
        WHERE id NOT IN (
            SELECT MAX(id) FROM documents GROUP BY path
        )
        """
    )
    conn.commit()

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_path ON documents(path)"
    )
    conn.commit()
    conn.close()
