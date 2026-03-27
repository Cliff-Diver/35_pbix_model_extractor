"""Engine pro generování diffu mezi původním a upraveným Power Query kódem.

Podporuje dva režimy zobrazení:
- unified: klasický diff s +/- řádky (jako v git diff),
- side-by-side: původní a nový kód vedle sebe se zvýrazněním změn.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from html import escape

_INLINE_TOKEN_PATTERN = re.compile(r"\s+|[\w]+|[^\w\s]", re.UNICODE)
_LINE_MATCH_THRESHOLD = 0.55
_GAP_COST = 0.65


@dataclass
class DiffLine:
    """Jeden řádek diffu.

    Attributes:
        left: Text na levé straně (původní). Prázdný řetězec pokud řádek přidán.
        right: Text na pravé straně (nový). Prázdný řetězec pokud řádek odebrán.
        change_type: Typ změny – 'equal', 'added', 'removed', 'modified'.
        left_lineno: Číslo řádku na levé straně (None pokud přidán).
        right_lineno: Číslo řádku na pravé straně (None pokud odebrán).
    """

    left: str = ""
    right: str = ""
    change_type: str = "equal"
    left_lineno: int | None = None
    right_lineno: int | None = None


@dataclass
class DiffResult:
    """Výsledek porovnání dvou textů.

    Attributes:
        original: Původní text.
        modified: Upravený text.
        lines: Seznam řádků diffu pro side-by-side zobrazení.
        unified_diff: Textový unified diff.
        has_changes: True pokud byly nalezeny rozdíly.
    """

    original: str = ""
    modified: str = ""
    lines: list[DiffLine] = field(default_factory=list)
    unified_diff: str = ""
    has_changes: bool = False


def generate_diff(original: str, modified: str) -> DiffResult:
    """Porovná původní a upravený kód a vrátí strukturovaný výsledek.

    Args:
        original: Původní Power Query (M) kód.
        modified: Upravený kód vrácený z OpenAI.

    Returns:
        DiffResult s unified diff i side-by-side řádky.
    """
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()

    # Unified diff – standardní textový formát
    unified = list(difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original",
        tofile="modified",
        lineterm="",
    ))
    unified_text = "\n".join(unified)

    # Side-by-side diff – strukturovaný výstup pro HTML rendering
    side_by_side_lines = _build_side_by_side(original_lines, modified_lines)

    has_changes = original_lines != modified_lines

    return DiffResult(
        original=original,
        modified=modified,
        lines=side_by_side_lines,
        unified_diff=unified_text,
        has_changes=has_changes,
    )


def _build_side_by_side(original_lines: list[str], modified_lines: list[str]) -> list[DiffLine]:
    """Sestaví side-by-side řádky z výsledku SequenceMatcher.

    Args:
        original_lines: Řádky původního textu.
        modified_lines: Řádky upraveného textu.

    Returns:
        Seznam DiffLine objektů pro side-by-side zobrazení.
    """
    result: list[DiffLine] = []
    matcher = difflib.SequenceMatcher(None, original_lines, modified_lines, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # Stejné řádky na obou stranách
            for idx in range(i2 - i1):
                result.append(DiffLine(
                    left=original_lines[i1 + idx],
                    right=modified_lines[j1 + idx],
                    change_type="equal",
                    left_lineno=i1 + idx + 1,
                    right_lineno=j1 + idx + 1,
                ))
        elif tag == "replace":
            # Změněné bloky párujeme podle podobnosti řádků, aby se vložené
            # komentáře a skutečně upravené výrazy neposouvaly proti sobě.
            result.extend(_align_replace_block(
                original_lines[i1:i2],
                modified_lines[j1:j2],
                left_start=i1 + 1,
                right_start=j1 + 1,
            ))
        elif tag == "delete":
            # Odebrané řádky – jen na levé straně
            for idx in range(i2 - i1):
                result.append(DiffLine(
                    left=original_lines[i1 + idx],
                    right="",
                    change_type="removed",
                    left_lineno=i1 + idx + 1,
                    right_lineno=None,
                ))
        elif tag == "insert":
            # Přidané řádky – jen na pravé straně
            for idx in range(j2 - j1):
                result.append(DiffLine(
                    left="",
                    right=modified_lines[j1 + idx],
                    change_type="added",
                    left_lineno=None,
                    right_lineno=j1 + idx + 1,
                ))

    return result


def _align_replace_block(
    original_block: list[str],
    modified_block: list[str],
    left_start: int,
    right_start: int,
) -> list[DiffLine]:
    """Zarovná blok `replace` pomocí jednoduchého DP nad podobností řádků."""
    if not original_block:
        return [
            DiffLine(right=line, change_type="added", right_lineno=right_start + idx)
            for idx, line in enumerate(modified_block)
        ]
    if not modified_block:
        return [
            DiffLine(left=line, change_type="removed", left_lineno=left_start + idx)
            for idx, line in enumerate(original_block)
        ]

    left_len = len(original_block)
    right_len = len(modified_block)
    costs = [[0.0] * (right_len + 1) for _ in range(left_len + 1)]
    moves: list[list[tuple[str, float | None]]] = [
        [("", None) for _ in range(right_len + 1)]
        for _ in range(left_len + 1)
    ]

    for left_idx in range(1, left_len + 1):
        costs[left_idx][0] = costs[left_idx - 1][0] + _GAP_COST
        moves[left_idx][0] = ("delete", None)

    for right_idx in range(1, right_len + 1):
        costs[0][right_idx] = costs[0][right_idx - 1] + _GAP_COST
        moves[0][right_idx] = ("insert", None)

    for left_idx in range(1, left_len + 1):
        for right_idx in range(1, right_len + 1):
            best_cost = costs[left_idx - 1][right_idx] + _GAP_COST
            best_move: tuple[str, float | None] = ("delete", None)

            insert_cost = costs[left_idx][right_idx - 1] + _GAP_COST
            if insert_cost < best_cost:
                best_cost = insert_cost
                best_move = ("insert", None)

            similarity = _line_similarity(
                original_block[left_idx - 1],
                modified_block[right_idx - 1],
            )
            if similarity >= _LINE_MATCH_THRESHOLD:
                pair_cost = costs[left_idx - 1][right_idx - 1] + (1.0 - similarity)
                if pair_cost <= best_cost:
                    best_cost = pair_cost
                    best_move = ("pair", similarity)

            costs[left_idx][right_idx] = best_cost
            moves[left_idx][right_idx] = best_move

    aligned: list[DiffLine] = []
    left_idx = left_len
    right_idx = right_len

    while left_idx > 0 or right_idx > 0:
        move, _score = moves[left_idx][right_idx]

        if move == "pair":
            aligned.append(DiffLine(
                left=original_block[left_idx - 1],
                right=modified_block[right_idx - 1],
                change_type="modified",
                left_lineno=left_start + left_idx - 1,
                right_lineno=right_start + right_idx - 1,
            ))
            left_idx -= 1
            right_idx -= 1
        elif move == "delete":
            aligned.append(DiffLine(
                left=original_block[left_idx - 1],
                right="",
                change_type="removed",
                left_lineno=left_start + left_idx - 1,
                right_lineno=None,
            ))
            left_idx -= 1
        else:
            aligned.append(DiffLine(
                left="",
                right=modified_block[right_idx - 1],
                change_type="added",
                left_lineno=None,
                right_lineno=right_start + right_idx - 1,
            ))
            right_idx -= 1

    aligned.reverse()
    return aligned


def _line_similarity(left: str, right: str) -> float:
    """Vrátí podobnost dvou řádků bez vlivu okolních mezer."""
    left_text = left.strip()
    right_text = right.strip()

    if not left_text and not right_text:
        return 1.0
    if not left_text or not right_text:
        return 0.0

    return difflib.SequenceMatcher(None, left_text, right_text, autojunk=False).ratio()


def diff_to_html(diff_result: DiffResult, mode: str = "side-by-side") -> str:
    """Převede DiffResult na HTML řetězec.

    Args:
        diff_result: Výsledek z generate_diff().
        mode: Režim zobrazení – 'unified' nebo 'side-by-side'.

    Returns:
        HTML řetězec s formátovaným diffem.
    """
    if mode == "unified":
        return _render_unified_html(diff_result)
    return _render_side_by_side_html(diff_result)


def _render_unified_html(diff_result: DiffResult) -> str:
    """Renderuje unified diff jako HTML.

    Args:
        diff_result: Výsledek z generate_diff().

    Returns:
        HTML řetězec s unified diff zobrazením.
    """
    if not diff_result.has_changes:
        return '<div class="diff-container unified"><p class="no-changes">Žádné změny</p></div>'

    lines_html: list[str] = []
    for raw_line in diff_result.unified_diff.split("\n"):
        escaped = escape(raw_line)
        if raw_line.startswith("+++") or raw_line.startswith("---"):
            css_class = "diff-header"
            # Préfix pro čitelnost – soubor
            marker = ""
        elif raw_line.startswith("@@"):
            css_class = "diff-hunk"
            marker = ""
        elif raw_line.startswith("+"):
            css_class = "diff-added"
            marker = "+"
            escaped = escaped[1:]  # Odstránít symbol z textu, zobrazíme ho přes pseudo-element
        elif raw_line.startswith("-"):
            css_class = "diff-removed"
            marker = "−"  # Minus znak (Unicode)
            escaped = escaped[1:]
        else:
            css_class = "diff-context"
            marker = ""
            # Unified diff přidává mezeru na začátek kontextových řádků – odebereme ji
            if escaped.startswith(" "):
                escaped = escaped[1:]

        blank_class = ""
        if css_class not in ("diff-header", "diff-hunk") and escaped == "":
            blank_class = " diff-line-blank"

        if css_class in ("diff-added", "diff-removed"):
            lines_html.append(
                f'<span class="diff-line {css_class}{blank_class}">'
                f'<span class="diff-sign">{marker}</span>{escaped}</span>'
            )
        else:
            lines_html.append(f'<span class="diff-line {css_class}{blank_class}">{escaped}</span>')

    content = "\n".join(lines_html)
    return f'<div class="diff-container unified"><pre class="diff-content">{content}</pre></div>'


def _render_side_by_side_html(diff_result: DiffResult) -> str:
    """Renderuje side-by-side diff jako HTML tabulku.

    Args:
        diff_result: Výsledek z generate_diff().

    Returns:
        HTML řetězec s tabulkou pro side-by-side zobrazení.
    """
    if not diff_result.has_changes:
        return '<div class="diff-container side-by-side"><p class="no-changes">Žádné změny</p></div>'

    rows: list[str] = []
    for line in diff_result.lines:
        left_no = str(line.left_lineno) if line.left_lineno is not None else ""
        right_no = str(line.right_lineno) if line.right_lineno is not None else ""

        # CSS třída řádku podle typu změny
        row_class = f"diff-row-{line.change_type}"
        if not line.left.strip() and not line.right.strip():
            row_class += " diff-row-blank"

        # Vizualní marker pro změněné buňky
        left_sign = "−" if line.change_type in ("removed", "modified") else ""
        right_sign = "+" if line.change_type in ("added", "modified") else ""

        if line.change_type == "modified":
            left_text, right_text = _render_inline_diff_pair(line.left, line.right)
        else:
            left_text = escape(line.left)
            right_text = escape(line.right)

        rows.append(
            f'<tr class="{row_class}">'
            f'<td class="line-no">{left_no}</td>'
            f'<td class="diff-left"><pre><span class="diff-sign">{left_sign}</span>{left_text}</pre></td>'
            f'<td class="line-no">{right_no}</td>'
            f'<td class="diff-right"><pre><span class="diff-sign">{right_sign}</span>{right_text}</pre></td>'
            f"</tr>"
        )

    table_content = "\n".join(rows)
    return (
        '<div class="diff-container side-by-side">'
        '<table class="diff-table">'
        "<thead><tr>"
        '<th colspan="2">◄&nbsp;Původní kód</th>'
        '<th colspan="2">Nový kód&nbsp;►</th>'
        "</tr></thead>"
        f"<tbody>{table_content}</tbody>"
        "</table></div>"
    )


def _render_inline_diff_pair(left: str, right: str) -> tuple[str, str]:
    """Vrátí HTML s jemným zvýrazněním vnitrořádkových změn."""
    left_tokens = _tokenize_inline_diff(left)
    right_tokens = _tokenize_inline_diff(right)
    matcher = difflib.SequenceMatcher(None, left_tokens, right_tokens, autojunk=False)

    left_parts: list[str] = []
    right_parts: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        left_chunk = "".join(left_tokens[i1:i2])
        right_chunk = "".join(right_tokens[j1:j2])

        if tag == "equal":
            left_parts.append(escape(left_chunk))
            right_parts.append(escape(right_chunk))
        elif tag == "delete":
            left_parts.append(_wrap_inline_change(left_chunk, "removed"))
        elif tag == "insert":
            right_parts.append(_wrap_inline_change(right_chunk, "added"))
        elif tag == "replace":
            left_parts.append(_wrap_inline_change(left_chunk, "removed"))
            right_parts.append(_wrap_inline_change(right_chunk, "added"))

    return "".join(left_parts), "".join(right_parts)


def _tokenize_inline_diff(text: str) -> list[str]:
    """Rozdělí řádek na tokeny tak, aby diff zvýrazňoval i části kódu."""
    if not text:
        return []
    return _INLINE_TOKEN_PATTERN.findall(text)


def _wrap_inline_change(text: str, change_type: str) -> str:
    """Obalí změněný úsek třídou pro vnitrořádkové zvýraznění."""
    if not text:
        return ""
    return f'<span class="diff-inline-{change_type}">{escape(text)}</span>'
