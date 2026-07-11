from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.indexers.document_indexer import DocumentIndexer
from app.services.chat_service import answer_document_question
from app.services.dashboard_service import get_dashboard_stats

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _build_template_context(request: Request, extra: dict[str, object] | None = None) -> dict[str, object]:
    base = {
        "request": request,
        "results": [],
        "folder_path": "",
        "dashboard": get_dashboard_stats(),
        "query": "",
        "summary": None,
        "files": [],
        "error": "",
        "question": "",
        "chat_answer": "",
        "chat_sources": [],
        "chat_model": None,
        "chat_elapsed": None,
        "chat_retrieval_seconds": None,
        "chat_ollama_seconds": None,
        "chat_source_count": 0,
        "chat_context_characters": 0,
        "chat_error": "",
    }
    if extra:
        base.update(extra)
    return base


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_template_context(request),
    )


@router.post("/scan", response_class=HTMLResponse)
async def scan_folder(request: Request, folder_path: str = Form(...)) -> HTMLResponse:
    error = ""
    scan_result = {"summary": {"total": 0, "new": 0, "updated": 0, "unchanged": 0, "errors": 0}, "files": []}
    try:
        indexer = DocumentIndexer(folder_path)
        scan_result = indexer.index_folder()
    except Exception as exc:
        error = str(exc) or "Error al escanear la carpeta."
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_template_context(request, {
            "folder_path": folder_path,
            "error": error,
            "summary": scan_result["summary"],
            "files": scan_result["files"],
        }),
    )


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", folder_path: str = "") -> HTMLResponse:
    results = []
    if q:
        indexer = DocumentIndexer(".")
        results = indexer.search(q)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_template_context(request, {
            "results": results,
            "query": q,
            "folder_path": folder_path,
        }),
    )


@router.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, question: str = Form(...), folder_path: str = Form("")) -> HTMLResponse:
    chat_result = answer_document_question(question)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_template_context(request, {
            "folder_path": folder_path,
            "question": question,
            "chat_answer": chat_result.get("answer", ""),
            "chat_sources": chat_result.get("sources", []),
            "chat_model": chat_result.get("model"),
            "chat_elapsed": chat_result.get("elapsed_seconds"),
            "chat_retrieval_seconds": chat_result.get("retrieval_seconds"),
            "chat_ollama_seconds": chat_result.get("ollama_seconds"),
            "chat_source_count": chat_result.get("source_count", 0),
            "chat_context_characters": chat_result.get("context_characters", 0),
            "chat_error": chat_result.get("error", ""),
        }),
    )
