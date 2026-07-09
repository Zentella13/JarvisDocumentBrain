import hashlib
import importlib
import os
from pathlib import Path


def _reload_indexer(tmp_path: Path):
    os.environ["JARVIS_DB_PATH"] = str(tmp_path / "documents.db")
    import app.database.connection as connection
    import app.database.schema as schema
    import app.indexers.document_indexer as document_indexer

    importlib.reload(connection)
    importlib.reload(schema)
    importlib.reload(document_indexer)
    return connection, schema, document_indexer


def test_indexer_reuses_existing_record_for_same_content_and_updates_for_changed_content(tmp_path: Path) -> None:
    connection, schema, document_indexer = _reload_indexer(tmp_path)
    schema.init_db()

    folder = tmp_path / "docs"
    folder.mkdir()
    file_path = folder / "notes.txt"
    file_path.write_text("first version", encoding="utf-8")

    indexer = document_indexer.DocumentIndexer(folder)
    first_run = indexer.index_folder()
    assert len(first_run) == 1

    conn = connection.get_connection()
    first_row = conn.execute(
        "SELECT path, sha256, size_bytes, extension FROM documents WHERE path = ?",
        (str(file_path),),
    ).fetchone()
    conn.close()

    assert first_row["sha256"] == hashlib.sha256(b"first version").hexdigest()
    assert first_row["size_bytes"] == len(b"first version")
    assert first_row["extension"] == ".txt"

    second_run = indexer.index_folder()
    assert len(second_run) == 1

    conn = connection.get_connection()
    rows = conn.execute("SELECT path, sha256 FROM documents WHERE path = ?", (str(file_path),)).fetchall()
    conn.close()
    assert len(rows) == 1

    file_path.write_text("second version", encoding="utf-8")
    third_run = indexer.index_folder()
    assert len(third_run) == 1

    conn = connection.get_connection()
    updated_row = conn.execute(
        "SELECT path, sha256, size_bytes, extension FROM documents WHERE path = ?",
        (str(file_path),),
    ).fetchone()
    conn.close()

    assert updated_row["sha256"] == hashlib.sha256(b"second version").hexdigest()
    assert updated_row["size_bytes"] == len(b"second version")
