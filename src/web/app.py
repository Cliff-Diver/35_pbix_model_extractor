"""FastAPI aplikace pro PBIX Model Extractor.

Webové rozhraní pro nahrání PBIX souboru, zobrazení Power Query dotazů,
odeslání na OpenAI API a zobrazení diffu mezi původním a novým kódem.
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.diff_engine import diff_to_html, generate_diff
from src.extractor import extract_from_pbix
from src.openai_client import OpenAIClient, OpenAIClientError, load_instructions
from src.web.models import AnalyzeResponse, AnalyzeResultItem, QueryNode, UploadResponse

# Načtení env proměnných při startu aplikace
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="PBIX Model Extractor", version="0.2.0")

# Cesty ke statickým souborům a šablonám
_WEB_DIR = Path(__file__).parent
_STATIC_DIR = _WEB_DIR / "static"
_TEMPLATES_DIR = _WEB_DIR / "templates"

# Mount statických souborů
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Jinja2 šablony
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

# In-memory úložiště session dat (session_id -> data)
_sessions: dict[str, dict[str, Any]] = {}

# Maximální velikost PBIX souboru (100 MB)
_MAX_UPLOAD_SIZE = 100 * 1024 * 1024


# --- Pomocné funkce ---


def _get_session(session_id: str) -> dict[str, Any]:
    """Získá session data nebo vyhodí 404.

    Args:
        session_id: ID session.

    Returns:
        Slovník s daty session.

    Raises:
        HTTPException: Pokud session neexistuje.
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' nenalezena.")
    return _sessions[session_id]


# --- HTML stránky ---


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request) -> HTMLResponse:
    """Hlavní stránka – upload PBIX souboru.

    Args:
        request: HTTP request objekt.

    Returns:
        Renderovaná HTML stránka.
    """
    return templates.TemplateResponse(request, "index.html")


@app.get("/queries/{session_id}", response_class=HTMLResponse)
async def queries_page(request: Request, session_id: str) -> HTMLResponse:
    """Stránka se seznamem extrahovaných dotazů.

    Args:
        request: HTTP request objekt.
        session_id: ID session s extrahovanými daty.

    Returns:
        Renderovaná HTML stránka s dotazy.
    """
    session = _get_session(session_id)
    return templates.TemplateResponse(request, "queries.html", {
        "session_id": session_id,
        "filename": session["filename"],
        "queries": session["queries"],
    })


@app.get("/diff/{session_id}", response_class=HTMLResponse)
async def diff_page(request: Request, session_id: str) -> HTMLResponse:
    """Stránka pro zobrazení výsledků analýzy a diffu.

    Args:
        request: HTTP request objekt.
        session_id: ID session.

    Returns:
        Renderovaná HTML stránka s diff zobrazením.
    """
    session = _get_session(session_id)
    results = session.get("results", [])
    return templates.TemplateResponse(request, "diff_view.html", {
        "session_id": session_id,
        "filename": session["filename"],
        "results": results,
    })


# --- API endpointy ---


@app.post("/upload")
async def upload_pbix(file: UploadFile = File(...)) -> UploadResponse:
    """Nahraje PBIX soubor, extrahuje Power Query dotazy a vytvoří session.

    Args:
        file: Nahraný PBIX soubor.

    Returns:
        UploadResponse s ID session a seznamem dotazů.

    Raises:
        HTTPException: Pokud soubor není validní PBIX nebo je příliš velký.
    """
    # Validace přípony souboru
    if not file.filename or not file.filename.lower().endswith(".pbix"):
        raise HTTPException(status_code=400, detail="Soubor musí mít příponu .pbix")

    # Načtení obsahu souboru s kontrolou velikosti
    content = await file.read()
    if len(content) > _MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Soubor je příliš velký (max 100 MB).")

    # Uložení do temp souboru pro zpracování pbixray
    with tempfile.NamedTemporaryFile(suffix=".pbix", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Extrakce Power Query dotazů ze souboru
        nodes = extract_from_pbix(tmp_path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        logger.exception("Chyba při extrakci PBIX souboru: %s", file.filename)
        raise HTTPException(status_code=400, detail=f"Chyba při zpracování PBIX: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    # Převod na Pydantic modely
    queries = [QueryNode(**node) for node in nodes]

    # Vytvoření session
    session_id = uuid.uuid4().hex[:12]
    _sessions[session_id] = {
        "filename": file.filename,
        "queries": queries,
        "results": [],
    }

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        query_count=len(queries),
        queries=queries,
    )


@app.post("/analyze")
async def analyze_queries(
    session_id: str = Form(...),
    query_ids: str = Form(""),
    instructions_text: str = Form(""),
    instruction_files: list[UploadFile] = File(default=[]),
) -> AnalyzeResponse:
    """Odešle vybrané dotazy na OpenAI API k analýze.

    Args:
        session_id: ID session s extrahovanými daty.
        query_ids: Čárkou oddělené ID dotazů k analýze. Prázdný = všechny.
        instructions_text: Přímé textové instrukce (volitelné).
        instruction_files: Nahrané markdown soubory s instrukcemi.

    Returns:
        AnalyzeResponse s výsledky analýzy pro každý dotaz.
    """
    session = _get_session(session_id)
    queries: list[QueryNode] = session["queries"]

    # Výběr dotazů k analýze
    if query_ids.strip():
        selected_ids = {qid.strip() for qid in query_ids.split(",")}
        selected_queries = [q for q in queries if q.id in selected_ids]
    else:
        # Prázdný výběr = všechny dotazy
        selected_queries = list(queries)

    if not selected_queries:
        raise HTTPException(status_code=400, detail="Žádné dotazy k analýze.")

    # Sestavení instrukcí z nahraných MD souborů + přímého textu
    instructions_parts: list[str] = []

    # Načtení obsahu z nahraných souborů
    for upload_file in instruction_files:
        if upload_file.filename:
            file_content = await upload_file.read()
            instructions_parts.append(file_content.decode("utf-8").strip())

    # Přidání přímého textu
    if instructions_text.strip():
        instructions_parts.append(instructions_text.strip())

    if not instructions_parts:
        raise HTTPException(status_code=400, detail="Nejsou zadány žádné instrukce pro model.")

    combined_instructions = "\n\n".join(instructions_parts)

    # Volání OpenAI API
    try:
        client = OpenAIClient()
    except OpenAIClientError as exc:
        return AnalyzeResponse(session_id=session_id, error=str(exc))

    results: list[AnalyzeResultItem] = []
    try:
        for query in selected_queries:
            modified_code = client.analyze_query(query.m_code, combined_instructions)

            # Generování diffu mezi původním a novým kódem
            diff_result = generate_diff(query.m_code, modified_code)

            results.append(AnalyzeResultItem(
                query_name=query.name,
                original_code=query.m_code,
                modified_code=modified_code,
                diff_html_unified=diff_to_html(diff_result, mode="unified"),
                diff_html_side_by_side=diff_to_html(diff_result, mode="side-by-side"),
                has_changes=diff_result.has_changes,
            ))
    except OpenAIClientError as exc:
        return AnalyzeResponse(session_id=session_id, results=results, error=str(exc))

    # Uložení výsledků do session pro pozdější zobrazení
    session["results"] = results

    return AnalyzeResponse(session_id=session_id, results=results)


@app.get("/api/queries/{session_id}")
async def get_queries_api(session_id: str) -> list[QueryNode]:
    """Vrátí seznam extrahovaných dotazů pro session (JSON API).

    Args:
        session_id: ID session.

    Returns:
        Seznam dotazů.
    """
    session = _get_session(session_id)
    return session["queries"]


@app.get("/api/results/{session_id}")
async def get_results_api(session_id: str) -> AnalyzeResponse:
    """Vrátí výsledky analýzy pro session (JSON API).

    Args:
        session_id: ID session.

    Returns:
        AnalyzeResponse s výsledky.
    """
    session = _get_session(session_id)
    return AnalyzeResponse(
        session_id=session_id,
        results=session.get("results", []),
    )
