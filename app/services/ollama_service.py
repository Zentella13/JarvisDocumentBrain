import json
import os
import urllib.request
import urllib.error
from typing import Any

DEFAULT_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen3:1.7b"
MAX_CONTEXT_CHARS = 7000


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _build_context(sources: list[dict[str, object]]) -> tuple[str, int, list[dict[str, object]]]:
    parts = []
    included_sources: list[dict[str, object]] = []
    total_chars = 0
    max_total_chars = 6000
    max_snippet_chars = 1000

    for index, source in enumerate(sources, start=1):
        filename = source.get("filename", "")
        path = source.get("path", "")
        snippet = source.get("snippet", "") or ""
        if len(snippet) > max_snippet_chars:
            snippet = snippet[:max_snippet_chars] + "..."

        source_block = (
            f"FUENTE [{index}]\n"
            f"Archivo: {filename}\n"
            f"Ruta: {path}\n"
            f"Contenido:\n{snippet}"
        )
        projected = "\n\n".join(parts + [source_block])
        if len(projected) > max_total_chars:
            break

        parts.append(source_block)
        included_sources.append({
            "id": source.get("id"),
            "filename": filename,
            "path": path,
            "extension": source.get("extension", ""),
            "snippet": snippet,
            "score": source.get("score", 0),
            "matched_terms": source.get("matched_terms", []),
        })
        total_chars = len(projected)

    return "\n\n".join(parts), total_chars, included_sources


def ask_ollama(question: str, sources: list[dict[str, object]]) -> dict[str, object]:
    url = _get_env("OLLAMA_CHAT_URL", DEFAULT_URL)
    model = _get_env("JARVIS_MODEL", DEFAULT_MODEL)

    if not sources:
        return {
            "answer": "",
            "model": model,
            "sources": sources,
            "context_characters": 0,
        }

    context, context_characters, sent_sources = _build_context(sources)
    payload_text = f"{context}\n\nPregunta: {question}"

    body = {
        "model": model,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 180,
            "num_ctx": 4096,
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres JARVIS, un asistente documental profesional. "
                    "Responde siempre en español. "
                    "Sé breve y directo. "
                    "Máximo aproximado de 180 palabras. "
                    "Usa únicamente lo dicho literalmente en las fuentes. "
                    "No confundas el contenido con el título o nombre del archivo. "
                    "No atribuyas información a una ubicación donde no aparece. "
                    "No inventes conclusiones. "
                    "Cita cada afirmación relevante usando [1], [2], etc. "
                    "Si falta información, dilo claramente. "
                    "No muestres razonamiento interno."
                ),
            },
            {"role": "user", "content": payload_text},
        ],
    }

    request_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar a Ollama: {exc}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Respuesta JSON inválida de Ollama: {exc}")
    except Exception as exc:
        raise RuntimeError(f"Error al solicitar a Ollama: {exc}")

    message = data.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("Respuesta de Ollama sin campo 'message'.")

    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("Respuesta de Ollama sin 'message.content'.")

    return {
        "answer": content.strip(),
        "model": model,
        "sources": sent_sources,
        "context_characters": context_characters,
    }
