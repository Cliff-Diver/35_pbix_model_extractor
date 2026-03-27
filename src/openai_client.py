"""Konektor na OpenAI API pro analýzu a úpravu Power Query (M) kódu.

Modul poskytuje třídu OpenAIClient pro odesílání M kódu spolu s markdown
instrukcemi na OpenAI API a vrácení výsledku.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    import os

import os as _os

from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

# Načtení proměnných z .env souboru
load_dotenv()

logger = logging.getLogger(__name__)

# Výchozí model, lze přepsat přes .env
_DEFAULT_MODEL = "gpt-5.4-mini"


class OpenAIClientError(Exception):
    """Základní výjimka pro chyby OpenAI klienta."""


def load_instructions(paths: list[Path]) -> str:
    """Načte obsah jednoho nebo více markdown souborů a spojí je do jednoho textu.

    Args:
        paths: Seznam cest k markdown souborům s instrukcemi.

    Returns:
        Spojený textový obsah všech souborů oddělený prázdným řádkem.

    Raises:
        FileNotFoundError: Pokud některý soubor neexistuje.
    """
    parts: list[str] = []
    for path in paths:
        resolved = Path(path)
        if not resolved.is_file():
            msg = f"Instrukční soubor neexistuje: {resolved}"
            raise FileNotFoundError(msg)
        # Načtení obsahu souboru
        content = resolved.read_text(encoding="utf-8")
        parts.append(content.strip())
    return "\n\n".join(parts)


class OpenAIClient:
    """Klient pro komunikaci s OpenAI API.

    Umožňuje odesílat Power Query (M) kód spolu s instrukcemi k analýze
    nebo úpravě a vrací výsledek z modelu.

    Args:
        api_key: Volitelný API klíč. Pokud není zadán, načte se z env proměnné OPENAI_API_KEY.
        model: Název modelu. Výchozí hodnota se načte z env proměnné OPENAI_MODEL.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        # Získání API klíče – priorita: argument > env proměnná
        resolved_key = api_key or _os.environ.get("OPENAI_API_KEY", "")
        if not resolved_key:
            msg = (
                "OpenAI API klíč není nastaven. "
                "Nastavte proměnnou OPENAI_API_KEY v souboru .env nebo ji předejte jako argument."
            )
            raise OpenAIClientError(msg)

        self.model = model or _os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)
        self._client = OpenAI(api_key=resolved_key)

    def analyze_query(self, m_code: str, instructions: str) -> str:
        """Odešle jeden Power Query dotaz k analýze přes OpenAI API.

        Args:
            m_code: Zdrojový kód Power Query (M).
            instructions: Textové instrukce pro model (obsah markdown souborů).

        Returns:
            Text odpovědi z modelu.

        Raises:
            OpenAIClientError: Při chybě komunikace s API.
        """
        messages = self._build_messages(m_code, instructions)
        return self._call_api(messages)

    def analyze_queries_batch(self, queries: list[dict[str, str]], instructions: str) -> list[dict[str, str]]:
        """Odešle více Power Query dotazů k analýze.

        Každý dotaz je odeslán jako samostatný požadavek, aby model zpracoval
        každý dotaz individuálně.

        Args:
            queries: Seznam slovníků s klíči 'name' a 'm_code'.
            instructions: Textové instrukce pro model.

        Returns:
            Seznam slovníků s klíči 'name' a 'result'.

        Raises:
            OpenAIClientError: Při chybě komunikace s API.
        """
        results: list[dict[str, str]] = []
        for query in queries:
            name = query["name"]
            m_code = query["m_code"]
            logger.info("Odesílám dotaz '%s' na OpenAI API...", name)
            result_text = self.analyze_query(m_code, instructions)
            results.append({"name": name, "result": result_text})
        return results

    def _build_messages(self, m_code: str, instructions: str) -> list[dict[str, str]]:
        """Sestaví seznam zpráv pro OpenAI API.

        Args:
            m_code: Power Query (M) kód.
            instructions: Instrukce z markdown souborů.

        Returns:
            Seznam zpráv ve formátu očekávaném OpenAI API.
        """
        return [
            {"role": "system", "content": instructions},
            {"role": "user", "content": m_code},
        ]

    def _call_api(self, messages: list[dict[str, str]]) -> str:
        """Zavolá OpenAI API a vrátí textovou odpověď.

        Args:
            messages: Seznam zpráv pro API.

        Returns:
            Text odpovědi modelu.

        Raises:
            OpenAIClientError: Při chybě komunikace s API.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
            )
            # Extrakce textu z odpovědi
            choice = response.choices[0]
            return choice.message.content or ""

        except AuthenticationError as exc:
            msg = "Neplatný OpenAI API klíč. Zkontrolujte konfiguraci v souboru .env."
            raise OpenAIClientError(msg) from exc
        except RateLimitError as exc:
            msg = "Překročen limit požadavků na OpenAI API. Zkuste to později."
            raise OpenAIClientError(msg) from exc
        except APITimeoutError as exc:
            msg = "Timeout při komunikaci s OpenAI API."
            raise OpenAIClientError(msg) from exc
        except APIConnectionError as exc:
            msg = "Nelze se připojit k OpenAI API. Zkontrolujte připojení k internetu."
            raise OpenAIClientError(msg) from exc
