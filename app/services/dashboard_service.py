from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.connection import get_connection


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    return f"{size_bytes / (1024 ** 3):.2f} GB"


def _format_datetime(value: str | None) -> str | None:
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    else:
        parsed = parsed.astimezone(ZoneInfo("UTC"))

    ny_time = parsed.astimezone(ZoneInfo("America/New_York"))
    return ny_time.strftime("%d/%m/%Y %I:%M %p")


def get_dashboard_stats() -> dict[str, object]:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) AS total_documents, COALESCE(SUM(size_bytes), 0) AS total_size_bytes, MAX(indexed_at) AS last_indexed_at FROM documents"
        )
        row = cursor.fetchone()
        total_documents = row["total_documents"] if row else 0
        total_size_bytes = row["total_size_bytes"] if row else 0
        last_indexed_at = row["last_indexed_at"] if row else None

        cursor.execute(
            "SELECT extension, COUNT(*) AS count FROM documents GROUP BY extension ORDER BY count DESC"
        )
        by_extension = [
            {"extension": r["extension"] or "", "count": r["count"]}
            for r in cursor.fetchall()
        ]

        cursor.execute(
            "SELECT filename, path, extension, size_bytes, indexed_at FROM documents ORDER BY datetime(indexed_at) DESC LIMIT 5"
        )
        recent_documents = [
            {
                "filename": r["filename"],
                "path": r["path"],
                "extension": r["extension"] or "",
                "size_bytes": r["size_bytes"],
                "indexed_at": _format_datetime(r["indexed_at"] if r["indexed_at"] else None),
            }
            for r in cursor.fetchall()
        ]

        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size_bytes,
            "total_size_display": _format_size(total_size_bytes),
            "last_indexed_at": _format_datetime(last_indexed_at),
            "by_extension": by_extension,
            "recent_documents": recent_documents,
        }
    finally:
        conn.close()
