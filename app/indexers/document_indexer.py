import hashlib
from datetime import datetime, timezone
from pathlib import Path

from app.database.connection import get_connection
from app.database.schema import init_db
from app.services.document_service import extract_text


class DocumentIndexer:
    def __init__(self, root_folder: str | Path) -> None:
        self.root_folder = Path(root_folder)
        init_db()

    def _compute_sha256(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def index_folder(self) -> list[dict[str, object]]:
        indexed: list[dict[str, object]] = []
        for file_path in self.root_folder.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".markdown"}:
                continue

            sha256 = self._compute_sha256(file_path)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sha256, content FROM documents WHERE path = ?",
                (str(file_path),),
            )
            existing = cursor.fetchone()
            if existing and existing[0] == sha256:
                text = existing[1]
            else:
                text = extract_text(file_path)

            size_bytes = file_path.stat().st_size
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
            indexed_at = datetime.now(timezone.utc).isoformat()

            cursor.execute(
                """
                INSERT INTO documents (filename, path, extension, size_bytes, sha256, last_modified, indexed_at, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename = excluded.filename,
                    extension = excluded.extension,
                    size_bytes = excluded.size_bytes,
                    sha256 = excluded.sha256,
                    last_modified = excluded.last_modified,
                    indexed_at = excluded.indexed_at,
                    content = excluded.content
                WHERE excluded.sha256 != documents.sha256
                """,
                (
                    file_path.name,
                    str(file_path),
                    suffix,
                    size_bytes,
                    sha256,
                    last_modified,
                    indexed_at,
                    text,
                ),
            )
            conn.commit()
            conn.close()
            indexed.append({"filename": file_path.name, "path": str(file_path), "content": text})

        return indexed

    def search(self, query: str) -> list[dict[str, object]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, filename, path, content FROM documents WHERE content LIKE ? ORDER BY id DESC LIMIT 20",
            (f"%{query}%",),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
