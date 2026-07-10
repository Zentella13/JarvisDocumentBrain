from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.indexers.document_indexer import DocumentIndexer

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "results": [], "folder_path": ""},
    )


@router.post("/scan", response_class=HTMLResponse)
async def scan_folder(request: Request, folder_path: str = Form(...)) -> HTMLResponse:
    error = ""
    results = []
    try:
        indexer = DocumentIndexer(folder_path)
        results = indexer.index_folder()
    except Exception as exc:
        error = str(exc) or "Error al escanear la carpeta."
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "results": results, "folder_path": folder_path, "error": error},
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
        context={"request": request, "results": results, "query": q, "folder_path": folder_path},
    )
