from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.indexers.document_indexer import DocumentIndexer
from app.services.dashboard_service import get_dashboard_stats

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    dashboard = get_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "results": [], "folder_path": "", "dashboard": dashboard},
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
    dashboard = get_dashboard_stats()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "results": [],
            "folder_path": folder_path,
            "error": error,
            "summary": scan_result["summary"],
            "files": scan_result["files"],
            "dashboard": dashboard,
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", folder_path: str = "") -> HTMLResponse:
    results = []
    dashboard = get_dashboard_stats()
    if q:
        indexer = DocumentIndexer(".")
        results = indexer.search(q)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "results": results, "query": q, "folder_path": folder_path, "dashboard": dashboard},
    )
