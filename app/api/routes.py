from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.indexers.document_indexer import DocumentIndexer

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "results": []})


@router.post("/scan", response_class=HTMLResponse)
async def scan_folder(request: Request, folder_path: str = Form(...)) -> HTMLResponse:
    indexer = DocumentIndexer(folder_path)
    results = indexer.index_folder()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "results": results, "folder_path": folder_path},
    )


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "") -> HTMLResponse:
    results = []
    if q:
        indexer = DocumentIndexer(".")
        results = indexer.search(q)
    return templates.TemplateResponse("index.html", {"request": request, "results": results, "query": q})
