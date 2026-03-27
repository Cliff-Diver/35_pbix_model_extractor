"""Testy pro modul openai_client – komunikace s OpenAI API.

Všechny testy používají mocknutý OpenAI klient, takže nepotřebují reálný API klíč.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.openai_client import OpenAIClient, OpenAIClientError, load_instructions


# --- Testy load_instructions ---


class TestLoadInstructions:
    """Testy pro funkci load_instructions."""

    def test_load_single_file(self, tmp_path: Path) -> None:
        """Načtení jednoho markdown souboru vrátí jeho obsah."""
        md_file = tmp_path / "instructions.md"
        md_file.write_text("# Optimalizuj dotazy", encoding="utf-8")

        result = load_instructions([md_file])

        assert result == "# Optimalizuj dotazy"

    def test_load_multiple_files(self, tmp_path: Path) -> None:
        """Načtení více souborů je spojí prázdným řádkem."""
        file_a = tmp_path / "a.md"
        file_b = tmp_path / "b.md"
        file_a.write_text("Instrukce A", encoding="utf-8")
        file_b.write_text("Instrukce B", encoding="utf-8")

        result = load_instructions([file_a, file_b])

        assert "Instrukce A" in result
        assert "Instrukce B" in result
        assert "\n\n" in result

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Chybějící soubor vyhodí FileNotFoundError."""
        missing = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="neexistuje"):
            load_instructions([missing])

    def test_empty_list_returns_empty_string(self) -> None:
        """Prázdný seznam vrátí prázdný řetězec."""
        result = load_instructions([])

        assert result == ""


# --- Testy OpenAIClient ---


def _make_mock_response(content: str = "optimized code") -> MagicMock:
    """Vytvoří mockovanou odpověď z OpenAI API."""
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestOpenAIClientInit:
    """Testy inicializace OpenAI klienta."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123", "OPENAI_MODEL": "gpt-test"})
    def test_init_from_env(self) -> None:
        """Klient se inicializuje z env proměnných."""
        client = OpenAIClient()

        assert client.model == "gpt-test"

    @patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False)
    def test_missing_api_key_raises_error(self) -> None:
        """Chybějící API klíč vyhodí OpenAIClientError."""
        # Vyčistíme klíč kompletně
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            import os
            original = os.environ.pop("OPENAI_API_KEY", None)
            try:
                with pytest.raises(OpenAIClientError, match="klíč"):
                    OpenAIClient()
            finally:
                if original is not None:
                    os.environ["OPENAI_API_KEY"] = original

    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_explicit_key_overrides_env(self) -> None:
        """Explicitně předaný klíč má přednost před env proměnnou."""
        client = OpenAIClient(api_key="explicit-key", model="gpt-custom")

        assert client.model == "gpt-custom"


class TestOpenAIClientAnalyze:
    """Testy metod analyze_query a analyze_queries_batch."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_analyze_query_returns_response(self) -> None:
        """analyze_query vrátí text odpovědi z API."""
        client = OpenAIClient()
        mock_response = _make_mock_response("let\n    Source = optimized\nin\n    Source")
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = mock_response

        result = client.analyze_query("let Source = 1 in Source", "Optimalizuj kód")

        assert "optimized" in result
        # Ověření, že API bylo zavoláno se správnými parametry
        call_kwargs = client._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_analyze_queries_batch(self) -> None:
        """analyze_queries_batch zpracuje všechny dotazy a vrátí výsledky."""
        client = OpenAIClient()
        mock_response = _make_mock_response("optimized")
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = mock_response

        queries = [
            {"name": "Query1", "m_code": "let A = 1 in A"},
            {"name": "Query2", "m_code": "let B = 2 in B"},
        ]
        results = client.analyze_queries_batch(queries, "Instrukce")

        assert len(results) == 2
        assert results[0]["name"] == "Query1"
        assert results[1]["name"] == "Query2"
        assert all(r["result"] == "optimized" for r in results)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_authentication_error(self) -> None:
        """Neplatný klíč vyhodí srozumitelnou chybu."""
        from openai import AuthenticationError

        client = OpenAIClient()
        client._client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        client._client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body=None,
        )

        with pytest.raises(OpenAIClientError, match="Neplatný"):
            client.analyze_query("code", "instructions")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_rate_limit_error(self) -> None:
        """Rate limit vyhodí srozumitelnou chybu."""
        from openai import RateLimitError

        client = OpenAIClient()
        client._client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        client._client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body=None,
        )

        with pytest.raises(OpenAIClientError, match="limit"):
            client.analyze_query("code", "instructions")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_timeout_error(self) -> None:
        """Timeout vyhodí srozumitelnou chybu."""
        from openai import APITimeoutError

        client = OpenAIClient()
        client._client = MagicMock()
        client._client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock(),
        )

        with pytest.raises(OpenAIClientError, match="Timeout"):
            client.analyze_query("code", "instructions")


class TestBuildMessages:
    """Testy pro sestavení zpráv pro API."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_message_structure(self) -> None:
        """Zprávy mají správnou strukturu: system + user."""
        client = OpenAIClient()
        messages = client._build_messages("M kód", "Instrukce")

        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "Instrukce"}
        assert messages[1] == {"role": "user", "content": "M kód"}
