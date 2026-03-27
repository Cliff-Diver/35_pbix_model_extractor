"""Pydantic modely pro webové API – request a response schémata.

Definuje datové struktury pro komunikaci mezi frontendem a backendem.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryNode(BaseModel):
    """Reprezentace jednoho Power Query dotazu/funkce/parametru.

    Attributes:
        id: Unikátní identifikátor uzlu.
        name: Název dotazu.
        kind: Typ uzlu (query, function, parameter).
        m_code: Zdrojový kód Power Query (M).
        group: Volitelná skupina dotazu.
        load_enabled: Zda je dotaz načítán do modelu.
    """

    id: str
    name: str
    kind: str
    m_code: str
    group: str | None = None
    load_enabled: bool | None = None


class UploadResponse(BaseModel):
    """Odpověď po nahrání PBIX souboru.

    Attributes:
        session_id: ID session pro další práci s extrahovanými daty.
        filename: Název nahraného souboru.
        query_count: Počet extrahovaných dotazů.
        queries: Seznam extrahovaných dotazů.
    """

    session_id: str
    filename: str
    query_count: int
    queries: list[QueryNode]


class AnalyzeRequest(BaseModel):
    """Požadavek na analýzu dotazů přes OpenAI API.

    Attributes:
        session_id: ID session s extrahovanými daty.
        query_ids: Seznam ID dotazů k analýze. Prázdný = všechny.
        instructions: Textové instrukce pro model (obsah MD souborů).
    """

    session_id: str
    query_ids: list[str] = Field(default_factory=list)
    instructions: str = ""


class AnalyzeResultItem(BaseModel):
    """Výsledek analýzy jednoho dotazu.

    Attributes:
        query_name: Název dotazu.
        original_code: Původní M kód.
        modified_code: Upravený kód z OpenAI.
        diff_html_unified: HTML diff v unified režimu.
        diff_html_side_by_side: HTML diff v side-by-side režimu.
        has_changes: Zda byly nalezeny změny.
    """

    query_name: str
    original_code: str
    modified_code: str
    diff_html_unified: str = ""
    diff_html_side_by_side: str = ""
    has_changes: bool = False


class AnalyzeResponse(BaseModel):
    """Odpověď po analýze dotazů.

    Attributes:
        session_id: ID session.
        results: Seznam výsledků pro jednotlivé dotazy.
        error: Chybová zpráva, pokud analýza selhala.
    """

    session_id: str
    results: list[AnalyzeResultItem] = Field(default_factory=list)
    error: str | None = None
