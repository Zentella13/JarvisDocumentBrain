import time

from app.services.ollama_service import ask_ollama
from app.services.retrieval_service import retrieve_relevant_documents


def answer_document_question(question: str) -> dict[str, object]:
    base_result = {
        "answer": "",
        "sources": [],
        "model": None,
        "retrieval_seconds": 0.0,
        "ollama_seconds": 0.0,
        "elapsed_seconds": 0.0,
        "source_count": 0,
        "context_characters": 0,
        "error": "",
    }

    if not question or not question.strip():
        return {
            **base_result,
            "answer": "La pregunta está vacía. Por favor ingresa una consulta.",
        }

    if len(question) > 2000:
        return {
            **base_result,
            "answer": "La pregunta excede el límite de 2000 caracteres.",
        }

    start = time.perf_counter()
    retrieval_start = time.perf_counter()
    sources = retrieve_relevant_documents(question, limit=5)
    retrieval_seconds = time.perf_counter() - retrieval_start

    if not sources:
        elapsed = time.perf_counter() - start
        return {
            **base_result,
            "answer": "No encontré información relacionada en los documentos indexados.",
            "retrieval_seconds": retrieval_seconds,
            "elapsed_seconds": elapsed,
        }

    try:
        ollama_start = time.perf_counter()
        response = ask_ollama(question, sources)
        ollama_seconds = time.perf_counter() - ollama_start
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            **base_result,
            "answer": f"Error al obtener respuesta de Ollama: {exc}",
            "sources": sources,
            "retrieval_seconds": retrieval_seconds,
            "ollama_seconds": ollama_seconds if 'ollama_seconds' in locals() else 0.0,
            "elapsed_seconds": elapsed,
            "source_count": len(sources),
            "context_characters": response.get("context_characters", 0) if 'response' in locals() else 0,
            "error": str(exc),
        }

    elapsed = time.perf_counter() - start
    actual_sources = response.get("sources", [])
    return {
        "answer": response.get("answer", ""),
        "sources": actual_sources,
        "model": response.get("model"),
        "retrieval_seconds": retrieval_seconds,
        "ollama_seconds": ollama_seconds,
        "elapsed_seconds": elapsed,
        "source_count": len(actual_sources),
        "context_characters": response.get("context_characters", 0),
        "error": "",
    }
