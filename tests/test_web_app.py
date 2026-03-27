"""Testy pro webovou aplikaci – API endpointy.

Používá FastAPI TestClient bez potřeby reálného PBIX souboru nebo OpenAI API.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.diff_engine import diff_to_html, generate_diff
from src.web.app import _sessions, app
from src.web.models import AnalyzeResultItem, QueryNode


@pytest.fixture()
def client() -> TestClient:
    """Vytvoří testovací klient pro FastAPI aplikaci."""
    return TestClient(app)


@pytest.fixture()
def _mock_session() -> str:
    """Vytvoří mock session s testovacími daty a vrátí session_id."""
    session_id = "test123abc"
    _sessions[session_id] = {
        "filename": "test_report.pbix",
        "queries": [
            QueryNode(
                id="query__sales__abc123",
                name="Sales",
                kind="query",
                m_code='let\n    Source = Sql.Database("srv", "db")\nin\n    Source',
                load_enabled=True,
            ),
            QueryNode(
                id="query__customers__def456",
                name="Customers",
                kind="query",
                m_code='let\n    Source = Excel.Workbook(File.Contents("data.xlsx"))\nin\n    Source',
                load_enabled=True,
            ),
            QueryNode(
                id="function__transform__ghi789",
                name="fnTransform",
                kind="function",
                m_code="(input as table) => Table.TransformColumns(input, {})",
                load_enabled=None,
            ),
        ],
        "results": [],
    }
    yield session_id
    # Úklid po testu
    _sessions.pop(session_id, None)


class TestIndexPage:
    """Testy hlavní stránky."""

    def test_index_returns_html(self, client: TestClient) -> None:
        """Hlavní stránka vrátí HTML s upload formulářem."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestUploadEndpoint:
    """Testy pro POST /upload."""

    def test_upload_invalid_extension(self, client: TestClient) -> None:
        """Soubor s nevalidní příponou vrátí chybu 400."""
        response = client.post("/upload", files={"file": ("report.txt", b"data", "text/plain")})

        assert response.status_code == 400
        assert "pbix" in response.json()["detail"].lower()

    @patch("src.web.app.extract_from_pbix")
    def test_upload_success(self, mock_extract: MagicMock, client: TestClient) -> None:
        """Úspěšný upload vytvoří session a vrátí dotazy."""
        mock_extract.return_value = [
            {
                "id": "query__test__abc",
                "name": "TestQuery",
                "kind": "query",
                "m_code": "let Source = 1 in Source",
                "group": None,
                "load_enabled": True,
            }
        ]

        response = client.post(
            "/upload",
            files={"file": ("report.pbix", b"fake-pbix-content", "application/octet-stream")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "report.pbix"
        assert data["query_count"] == 1
        assert len(data["queries"]) == 1
        assert data["session_id"]

        # Úklid – smazat session vytvořenou testem
        _sessions.pop(data["session_id"], None)

    @patch("src.web.app.extract_from_pbix", side_effect=Exception("Invalid PBIX"))
    def test_upload_extraction_error(self, mock_extract: MagicMock, client: TestClient) -> None:
        """Chyba při extrakci vrátí srozumitelnou chybu 400."""
        response = client.post(
            "/upload",
            files={"file": ("report.pbix", b"bad-content", "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "Chyba" in response.json()["detail"]


class TestQueriesEndpoints:
    """Testy pro stránku dotazů a API endpointy."""

    def test_queries_page(self, client: TestClient, _mock_session: str) -> None:
        """Stránka dotazů se renderuje pro existující session."""
        response = client.get(f"/queries/{_mock_session}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_queries_api(self, client: TestClient, _mock_session: str) -> None:
        """API endpoint vrátí seznam dotazů pro session."""
        response = client.get(f"/api/queries/{_mock_session}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Sales"

    def test_nonexistent_session_returns_404(self, client: TestClient) -> None:
        """Neexistující session vrátí 404."""
        response = client.get("/queries/nonexistent")

        assert response.status_code == 404

    def test_api_nonexistent_session_returns_404(self, client: TestClient) -> None:
        """API pro neexistující session vrátí 404."""
        response = client.get("/api/queries/nonexistent")

        assert response.status_code == 404


class TestAnalyzeEndpoint:
    """Testy pro POST /analyze."""

    @patch("src.web.app.OpenAIClient")
    def test_analyze_selected_queries(
        self, mock_client_cls: MagicMock, client: TestClient, _mock_session: str
    ) -> None:
        """Analýza vybraných dotazů vrátí výsledky s diffem."""
        mock_instance = MagicMock()
        mock_instance.analyze_query.return_value = "let\n    Source = OptimizedSource\nin\n    Source"
        mock_client_cls.return_value = mock_instance

        response = client.post("/analyze", data={
            "session_id": _mock_session,
            "query_ids": "query__sales__abc123",
            "instructions_text": "Optimalizuj dotaz",
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["query_name"] == "Sales"
        assert data["error"] is None

    @patch("src.web.app.OpenAIClient")
    def test_analyze_all_queries(
        self, mock_client_cls: MagicMock, client: TestClient, _mock_session: str
    ) -> None:
        """Prázdný query_ids analyzuje všechny dotazy."""
        mock_instance = MagicMock()
        mock_instance.analyze_query.return_value = "modified code"
        mock_client_cls.return_value = mock_instance

        response = client.post("/analyze", data={
            "session_id": _mock_session,
            "query_ids": "",
            "instructions_text": "Optimalizuj",
        })

        assert response.status_code == 200
        data = response.json()
        # Všechny 3 dotazy (Sales, Customers, fnTransform) by měly být analyzovány
        assert len(data["results"]) == 3

    def test_analyze_no_instructions(self, client: TestClient, _mock_session: str) -> None:
        """Chybějící instrukce vrátí chybu 400."""
        response = client.post("/analyze", data={
            "session_id": _mock_session,
            "query_ids": "",
            "instructions_text": "",
        })

        assert response.status_code == 400

    def test_analyze_nonexistent_session(self, client: TestClient) -> None:
        """Neexistující session vrátí 404."""
        response = client.post("/analyze", data={
            "session_id": "nonexistent",
            "query_ids": "",
            "instructions_text": "test",
        })

        assert response.status_code == 404

    @patch("src.web.app.OpenAIClient")
    def test_analyze_with_file_instructions(
        self, mock_client_cls: MagicMock, client: TestClient, _mock_session: str
    ) -> None:
        """Analýza s nahranými markdown soubory."""
        mock_instance = MagicMock()
        mock_instance.analyze_query.return_value = "optimized"
        mock_client_cls.return_value = mock_instance

        md_content = b"# Optimalizuj\nPridej komentare"

        response = client.post(
            "/analyze",
            data={
                "session_id": _mock_session,
                "query_ids": "query__sales__abc123",
                "instructions_text": "",
            },
            files=[("instruction_files", ("instructions.md", md_content, "text/markdown"))],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1


class TestDiffPage:
    """Testy pro stránku s diff zobrazením."""

    def test_diff_page_renders(self, client: TestClient, _mock_session: str) -> None:
        """Diff stránka se renderuje pro existující session."""
        diff_result = generate_diff("line1\n\nline2", "line1\n\nline3")
        _sessions[_mock_session]["results"] = [
            AnalyzeResultItem(
                query_name="Sales",
                original_code="line1\n\nline2",
                modified_code="line1\n\nline3",
                diff_html_unified=diff_to_html(diff_result, mode="unified"),
                diff_html_side_by_side=diff_to_html(diff_result, mode="side-by-side"),
                has_changes=True,
            )
        ]

        response = client.get(f"/diff/{_mock_session}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Široké zobrazení" in response.text
        assert "Zobrazit prázdné řádky" in response.text
        assert 'data-diff-page' in response.text

    def test_diff_nonexistent_session(self, client: TestClient) -> None:
        """Neexistující session vrátí 404."""
        response = client.get("/diff/nonexistent")

        assert response.status_code == 404
