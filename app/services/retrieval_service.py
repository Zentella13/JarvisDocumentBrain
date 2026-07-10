import re
from pathlib import Path
from typing import Iterable

from app.database.connection import get_connection

STOPWORDS = {
    "que", "como", "cuál", "cuáles", "los", "las", "del", "para", "por", "una", "unos",
    "qué", "dónde", "cuándo", "documento", "documentos", "información", "dime",
    "sobre", "menciona", "mencionan", "el", "la", "en", "de", "y", "o", "se", "con",
}

MAX_SNIPPET_LENGTH = 1200
MAX_TERMS = 10


def _normalize_text(text: str) -> str:
    text = text.lower()
    return re.sub(r"[^0-9a-záéíóúüñ]+", " ", text)


def _extract_terms(question: str) -> list[str]:
    normalized = _normalize_text(question)
    tokens = [token for token in normalized.split() if token and token not in STOPWORDS]
    unique_terms = []
    for token in tokens:
        if token not in unique_terms:
            unique_terms.append(token)
        if len(unique_terms) >= MAX_TERMS:
            break
    return unique_terms


def _build_snippet(content: str, terms: Iterable[str]) -> str:
    text = content.replace("\r", " ").replace("\n", " ")
    lower_text = text.lower()
    first_index = None
    first_term = None
    for term in terms:
        idx = lower_text.find(term)
        if idx >= 0 and (first_index is None or idx < first_index):
            first_index = idx
            first_term = term
    if first_index is None:
        snippet = text[:MAX_SNIPPET_LENGTH]
        return snippet.strip() + ("..." if len(text) > MAX_SNIPPET_LENGTH else "")

    start = max(0, first_index - MAX_SNIPPET_LENGTH // 2)
    end = start + MAX_SNIPPET_LENGTH
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def retrieve_relevant_documents(question: str, limit: int = 5) -> list[dict[str, object]]:
    terms = _extract_terms(question or "")
    if not terms:
        return []

    params = []
    where_clauses = []
    score_clauses = []
    for term in terms:
        pattern = f"%{term}%"
        where_clauses.append("lower(filename) LIKE ?")
        where_clauses.append("lower(content) LIKE ?")
        params.extend([pattern, pattern])
        score_clauses.append("CASE WHEN lower(filename) LIKE ? THEN 1 ELSE 0 END")
        score_clauses.append("CASE WHEN lower(content) LIKE ? THEN 1 ELSE 0 END")
        params.extend([pattern, pattern])

    where_sql = " OR ".join(where_clauses)
    score_sql = " + ".join(score_clauses)
    sql = f"""
        SELECT id, filename, path, extension, content,
            ({score_sql}) AS score
        FROM documents
        WHERE {where_sql}
        ORDER BY score DESC, id DESC
        LIMIT ?
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params + [limit])
        rows = cursor.fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        score = int(row["score"] or 0)
        if score == 0:
            continue
        content = row["content"] or ""
        snippet = _build_snippet(content, terms)
        matched_terms = [term for term in terms if term in row["filename"].lower() or term in content.lower()]
        results.append(
            {
                "id": row["id"],
                "filename": row["filename"],
                "path": row["path"],
                "extension": row["extension"] or "",
                "snippet": snippet,
                "matched_terms": matched_terms,
                "score": score,
            }
        )
        if len(results) >= limit:
            break

    return results
