"""Testy pro modul diff_engine – generování diffu mezi Power Query kódy."""

from __future__ import annotations

import pytest

from src.diff_engine import DiffLine, DiffResult, diff_to_html, generate_diff


# --- Testovací data ---

ORIGINAL_M_CODE = """\
let
    Source = Sql.Database("server", "db"),
    Filtered = Table.SelectRows(Source, each [Status] = "Active"),
    Result = Table.SelectColumns(Filtered, {"Name", "Value"})
in
    Result"""

MODIFIED_M_CODE = """\
let
    // Připojení ke zdroji dat
    Source = Sql.Database("server", "db"),
    // Filtrování aktivních záznamů s query folding
    Filtered = Table.SelectRows(Source, each [Status] = "Active" and [Year] > 2020),
    // Výběr relevantních sloupců
    Result = Table.SelectColumns(Filtered, {"Name", "Value", "Year"})
in
    Result"""


class TestGenerateDiff:
    """Testy pro funkci generate_diff."""

    def test_identical_code_no_changes(self) -> None:
        """Identický kód neobsahuje změny."""
        result = generate_diff(ORIGINAL_M_CODE, ORIGINAL_M_CODE)

        assert not result.has_changes
        assert all(line.change_type == "equal" for line in result.lines)

    def test_different_code_has_changes(self) -> None:
        """Odlišný kód obsahuje změny."""
        result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)

        assert result.has_changes
        change_types = {line.change_type for line in result.lines}
        assert change_types != {"equal"}

    def test_empty_original(self) -> None:
        """Prázdný původní kód – vše je přidáno."""
        result = generate_diff("", "let\n    Source = 1\nin\n    Source")

        assert result.has_changes
        assert any(line.change_type == "added" for line in result.lines)

    def test_empty_modified(self) -> None:
        """Prázdný nový kód – vše je odebráno."""
        result = generate_diff("let\n    Source = 1\nin\n    Source", "")

        assert result.has_changes
        assert any(line.change_type == "removed" for line in result.lines)

    def test_both_empty(self) -> None:
        """Oba kódy prázdné – žádné změny."""
        result = generate_diff("", "")

        assert not result.has_changes

    def test_result_contains_original_and_modified(self) -> None:
        """Výsledek obsahuje původní i upravený kód."""
        result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)

        assert result.original == ORIGINAL_M_CODE
        assert result.modified == MODIFIED_M_CODE

    def test_unified_diff_format(self) -> None:
        """Unified diff obsahuje standardní +/- formát."""
        result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)

        assert "---" in result.unified_diff or "+++" in result.unified_diff

    def test_unified_diff_does_not_add_blank_rows(self) -> None:
        """Unified diff nepřidává prázdné řádky mezi běžné změny."""
        result = generate_diff("line1\nline2", "line1\nline2\nline3")

        assert "" not in result.unified_diff.splitlines()

    def test_line_numbers_are_set(self) -> None:
        """Čísla řádků jsou správně nastavena."""
        result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)

        for line in result.lines:
            if line.change_type == "equal":
                assert line.left_lineno is not None
                assert line.right_lineno is not None
            elif line.change_type == "removed":
                assert line.left_lineno is not None
            elif line.change_type == "added":
                assert line.right_lineno is not None


class TestDiffToHtmlUnified:
    """Testy pro unified HTML rendering."""

    def test_no_changes_message(self) -> None:
        """Identický kód zobrazí zprávu 'Žádné změny'."""
        diff_result = generate_diff("same", "same")
        html = diff_to_html(diff_result, mode="unified")

        assert "Žádné změny" in html

    def test_added_lines_highlighted(self) -> None:
        """Přidané řádky mají CSS třídu diff-added."""
        diff_result = generate_diff("line1", "line1\nline2")
        html = diff_to_html(diff_result, mode="unified")

        assert "diff-added" in html

    def test_removed_lines_highlighted(self) -> None:
        """Odebrané řádky mají CSS třídu diff-removed."""
        diff_result = generate_diff("line1\nline2", "line1")
        html = diff_to_html(diff_result, mode="unified")

        assert "diff-removed" in html

    def test_html_escaping(self) -> None:
        """Speciální HTML znaky jsou escapovány."""
        diff_result = generate_diff('<script>alert("xss")</script>', "safe code")
        html = diff_to_html(diff_result, mode="unified")

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_blank_unified_lines_have_css_class(self) -> None:
        """Prázdné řádky v unified diffu jsou označené pro pozdější skrytí."""
        diff_result = generate_diff("line1\n\nline2", "line1\n\nline3")
        html = diff_to_html(diff_result, mode="unified")

        assert "diff-line-blank" in html


class TestDiffToHtmlSideBySide:
    """Testy pro side-by-side HTML rendering."""

    def test_no_changes_message(self) -> None:
        """Identický kód zobrazí zprávu 'Žádné změny'."""
        diff_result = generate_diff("same", "same")
        html = diff_to_html(diff_result, mode="side-by-side")

        assert "Žádné změny" in html

    def test_table_structure(self) -> None:
        """Side-by-side diff generuje HTML tabulku."""
        diff_result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)
        html = diff_to_html(diff_result, mode="side-by-side")

        assert "<table" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "Původní kód" in html
        assert "Nový kód" in html

    def test_row_css_classes(self) -> None:
        """Řádky mají správné CSS třídy podle typu změny."""
        diff_result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)
        html = diff_to_html(diff_result, mode="side-by-side")

        # Musí obsahovat alespoň jednu z tříd pro změněné/přidané/odebrané řádky
        assert "diff-row-equal" in html or "diff-row-modified" in html

    def test_html_escaping_side_by_side(self) -> None:
        """Speciální HTML znaky jsou escapovány i v side-by-side režimu."""
        diff_result = generate_diff('Source = "<value>"', 'Source = "<new>"')
        html = diff_to_html(diff_result, mode="side-by-side")

        assert "&lt;" in html or "&quot;" in html

    def test_replace_block_aligns_similar_lines(self) -> None:
        """Vložené komentáře se zobrazí jako added a skutečně podobné řádky jako modified."""
        diff_result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)

        assert any(
            line.change_type == "added"
            and line.left_lineno is None
            and line.right_lineno == 4
            and "query folding" in line.right
            for line in diff_result.lines
        )
        assert any(
            line.change_type == "modified"
            and line.left_lineno == 3
            and line.right_lineno == 5
            and "Filtered = Table.SelectRows" in line.left
            and "Filtered = Table.SelectRows" in line.right
            for line in diff_result.lines
        )
        assert any(
            line.change_type == "modified"
            and line.left_lineno == 4
            and line.right_lineno == 7
            and "Result = Table.SelectColumns" in line.left
            and "Result = Table.SelectColumns" in line.right
            for line in diff_result.lines
        )

    def test_modified_rows_include_inline_highlights(self) -> None:
        """Upravený řádek obsahuje v HTML jemné zvýraznění změněného úseku."""
        diff_result = generate_diff('Source = "<value>"', 'Source = "<new>"')
        html = diff_to_html(diff_result, mode="side-by-side")

        assert "diff-inline-removed" in html
        assert "diff-inline-added" in html

    def test_blank_side_by_side_rows_have_css_class(self) -> None:
        """Prázdné řádky v side-by-side diffu mají vlastní CSS třídu."""
        diff_result = generate_diff("line1\n\nline2", "line1\n\nline3")
        html = diff_to_html(diff_result, mode="side-by-side")

        assert "diff-row-blank" in html

    def test_default_mode_is_side_by_side(self) -> None:
        """Výchozí režim je side-by-side."""
        diff_result = generate_diff(ORIGINAL_M_CODE, MODIFIED_M_CODE)
        html = diff_to_html(diff_result)

        assert "<table" in html
