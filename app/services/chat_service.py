import time

from app.services.ollama_service import ask_ollama
from app.services.retrieval_service import retrieve_relevant_documents


def answer_document_question(question: str) -> dict[str, object]:
    if not question or not question.strip():
        return {
            "answer": "La pregunta está vacía. Por favor ingresa una consulta.",
            "sources": [],
            "model": None,
            "elapsed_seconds": 0.0,
        }

    if len(question) > 2000:
        return {
            "answer": "La pregunta excede el límite de 2000 caracteres.",
            "sources": [],
            "model": None,
            "elapsed_seconds": 0.0,
        }

    start = time.perf_counter()
    sources = retrieve_relevant_documents(question, limit=5)
    if not sources:
        elapsed = time.perf_counter() - start
        return {
            "answer": "No encontré información relacionada en los documentos indexados.",
            "sources": [],
            "model": None,
            "elapsed_seconds": elapsed,
            "error": "",
        }

    try:
        response = ask_ollama(question, sources)
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "answer": f"Error al obtener respuesta de Ollama: {exc}",
            "sources": sources,
            "model": None,
            "elapsed_seconds": elapsed,
            "error": str(exc),
        }

    elapsed = time.perf_counter() - start
    return {
        "answer": response.get("answer", ""),
        "sources": response.get("sources", []),
        "model": response.get("model"),
        "elapsed_seconds": elapsed,
        "error": "",
    }
