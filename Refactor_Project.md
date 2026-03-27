# Refactor Project – PBIX Model Extractor → Web App

## Přehled

Rozšíření stávajícího CLI nástroje na webovou aplikaci s:

- webovým UI pro práci s Power Query dotazy,
- napojením na OpenAI API (GPT-5.4 Mini),
- systémem markdown instrukcí pro model,
- zobrazením diffu mezi původním a novým kódem.

---

## Technologický stack

| Vrstva | Technologie | Poznámka |
|--------|------------|----------|
| Backend | **FastAPI** | async, rychlé API, WebSocket podpora |
| Frontend | **Jinja2 šablony + HTMX + Vanilla JS** | bez heavy SPA frameworku, rychlý vývoj |
| Diff rendering | **diff-match-patch** (Python) + **diff2html** (JS) | side-by-side i unified diff |
| OpenAI | **openai** Python SDK | GPT-5.4 Mini |
| Konfigurace | **python-dotenv** | API klíč z `.env` |
| CSS | **Pico CSS** nebo **Simple.css** | lightweight, minimální effort |
| Stávající logika | **src/extractor.py, dependency.py, generator.py** | beze změn, pouze import do nového backendu |

---

## Struktura složek (cílový stav)

```
35_pbix_model_extractor/
├── .env                          # API klíče (OPENAI_API_KEY)
├── .env.example                  # šablona .env pro nové vývojáře
├── .gitignore                    # doplnit .env
├── pyproject.toml                # aktualizovat závislosti
├── requirements.txt              # aktualizovat závislosti
├── Refactor_Project.md           # tento soubor
├── 0_INPUT/                      # PBIX soubory (vstup)
├── 1_OUTPUT/                     # CLI výstup (stávající)
├── 2_INSTRUCTIONS/               # markdown instrukce pro OpenAI model
│   └── example_optimize.md       # příklad instrukčního souboru
├── src/
│   ├── __init__.py
│   ├── cli.py                    # stávající CLI (zachovat)
│   ├── extractor.py              # stávající extrakce (zachovat)
│   ├── dependency.py             # stávající detekce závislostí (zachovat)
│   ├── generator.py              # stávající generátor výstupů (zachovat)
│   ├── openai_client.py          # NEW: konektor na OpenAI API
│   ├── diff_engine.py            # NEW: generování diffu (unified + side-by-side)
│   └── web/
│       ├── __init__.py
│       ├── app.py                # NEW: FastAPI aplikace, routy
│       ├── models.py             # NEW: Pydantic modely (request/response)
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css     # custom styly + diff highlighting
│       │   └── js/
│       │       └── app.js        # HTMX konfigurace, diff toggle, interakce
│       └── templates/
│           ├── base.html         # layout (head, nav, footer)
│           ├── index.html        # upload PBIX + zobrazení dotazů
│           ├── queries.html      # seznam dotazů, výběr, odeslání na API
│           ├── diff_view.html    # zobrazení diffu (side-by-side / unified)
│           └── partials/
│               ├── query_card.html    # HTMX partial – karta jednoho dotazu
│               ├── query_list.html    # HTMX partial – seznam dotazů
│               └── diff_result.html   # HTMX partial – výsledek diffu
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py         # stávající (zachovat)
│   ├── test_generator.py         # stávající (zachovat)
│   ├── test_openai_client.py     # NEW: testy OpenAI klientu
│   ├── test_diff_engine.py       # NEW: testy diff enginu
│   └── test_web_app.py           # NEW: testy API endpointů
```

---

## Milníky

### Milník 0: Příprava prostředí

**Cíl:** Připravit prostředí, závislosti a konfiguraci.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 0.1 | Aktualizovat `requirements.txt` | Přidat: `fastapi`, `uvicorn[standard]`, `python-multipart`, `jinja2`, `openai`, `python-dotenv`, `diff-match-patch`, `httpx` (test client) | `pip install -r requirements.txt` proběhne bez chyb |
| 0.2 | Aktualizovat `pyproject.toml` | Přidat nové závislosti do `[project.dependencies]` | `pip install -e .` proběhne bez chyb |
| 0.3 | Vytvořit `.env` a `.env.example` | Soubor s `OPENAI_API_KEY=` | `.env` existuje, je v `.gitignore` |
| 0.4 | Aktualizovat `.gitignore` | Přidat `.env`, `__pycache__/`, `*.egg-info/` | Ověřit `git status` nezobrazuje `.env` |
| 0.5 | Vytvořit složku `2_INSTRUCTIONS/` | Přidat příklad `example_optimize.md` s ukázkovou instrukcí | Složka a soubor existují |
| 0.6 | Vytvořit adresářovou strukturu `src/web/` | Vytvořit `src/web/__init__.py`, `static/`, `templates/` | Adresáře existují |

**Kontrolní bod M0:** Existující testy (`pytest`) stále procházejí. Nové závislosti nainstalované.

---

### Milník 1: OpenAI konektor (`src/openai_client.py`)

**Cíl:** Funkční volání OpenAI API s M kódem a markdown instrukcemi.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 1.1 | Vytvořit `src/openai_client.py` | Třída `OpenAIClient` s metodami: `analyze_query(m_code, instructions)` → `str`, `analyze_queries_batch(queries, instructions)` → `list[str]` | Unit test s mocknutým API |
| 1.2 | Načítání API klíče z `.env` | Použít `python-dotenv`, fallback na env proměnnou | Test: chybějící klíč vyhodí srozumitelnou chybu |
| 1.3 | Načítání markdown instrukcí | Funkce `load_instructions(paths: list[Path]) -> str` – načte a spojí obsah MD souborů | Test: načte 1+ souborů, spojí je, ošetří chybějící soubor |
| 1.4 | Sestavení promptu | System prompt = instrukce z MD, user prompt = M kód. Model: `gpt-5.4-mini` | Test: správná struktura messages |
| 1.5 | Error handling | Timeout, rate limit, neplatný klíč – srozumitelné chybové zprávy | Test: mock výjimek z openai SDK |
| 1.6 | Napsat `tests/test_openai_client.py` | Testy s mocknutým openai klientem (bez reálného API volání) | `pytest tests/test_openai_client.py` projde |

**Kontrolní bod M1:** `OpenAIClient` funguje s mock testy. Reálné API volání ověřeno manuálně.

---

### Milník 2: Diff engine (`src/diff_engine.py`)

**Cíl:** Generování strukturovanému diffu mezi původním a novým M kódem.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 2.1 | Vytvořit `src/diff_engine.py` | Funkce `generate_diff(original: str, modified: str) -> DiffResult` | Unit test |
| 2.2 | Unified diff | Výstup ve formátu unified diff (jako `difflib.unified_diff`) | Test: správné `+`/`-` řádky |
| 2.3 | Side-by-side diff | Výstup jako dvojice řádků `(left, right, change_type)` pro side-by-side zobrazení | Test: párování řádků |
| 2.4 | HTML rendering | Funkce `diff_to_html(diff_result, mode="unified"|"side-by-side") -> str` | Test: validní HTML výstup |
| 2.5 | Napsat `tests/test_diff_engine.py` | Testy pro oba formáty diffu, edge cases (prázdný vstup, identický kód, velký diff) | `pytest tests/test_diff_engine.py` projde |

**Kontrolní bod M2:** Diff engine generuje korektní unified i side-by-side diff pro Power Query kód.

---

### Milník 3: FastAPI backend (`src/web/app.py`)

**Cíl:** API endpointy pro upload, extrakci, OpenAI volání a diff.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 3.1 | Vytvořit `src/web/app.py` | FastAPI app se základním routingem | `uvicorn src.web.app:app` startuje |
| 3.2 | `POST /upload` | Upload PBIX → uložit do temp, extrahovat uzly, vrátit JSON | Test: upload testovacího PBIX |
| 3.3 | `GET /queries/{session_id}` | Vrátit seznam extrahovaných dotazů pro session | Test: vrací správný počet dotazů |
| 3.4 | `POST /analyze` | Přijmout query ID(s) + instruction file(s) → zavolat OpenAI → vrátit výsledek | Test: mock OpenAI, ověřit flow |
| 3.5 | `POST /analyze-all` | Odeslat všechny dotazy najednou | Test: mock OpenAI, ověřit batch flow |
| 3.6 | `GET /diff/{session_id}/{query_name}` | Vrátit diff HTML pro daný dotaz | Test: ověřit HTML odpověď |
| 3.7 | Vytvořit `src/web/models.py` | Pydantic modely: `UploadResponse`, `QueryNode`, `AnalyzeRequest`, `AnalyzeResponse`, `DiffResponse` | Importy fungují |
| 3.8 | Session management | In-memory dict pro ukládání extrahovaných dat per session (UUID) | Test: session se vytvoří a načte |
| 3.9 | Napsat `tests/test_web_app.py` | Testy endpointů pomocí `httpx.AsyncClient` / `TestClient` | `pytest tests/test_web_app.py` projde |

**Kontrolní bod M3:** Všechny API endpointy fungují a jsou otestovány. Backend se spustí bez chyb.

---

### Milník 4: Frontend – šablony a interakce

**Cíl:** Funkční webové UI pro celý workflow.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 4.1 | Vytvořit `base.html` | HTML layout: head s CSS/JS, navigace, footer | Stránka se renderuje |
| 4.2 | Vytvořit `index.html` | Upload formulář pro PBIX (drag & drop + file input) | Upload funguje, přesměruje na queries |
| 4.3 | Vytvořit `queries.html` | Seznam dotazů: jméno, kind, load_enabled, rozbalitelný M kód | Zobrazí extrahované dotazy |
| 4.4 | Select dotazů | Checkboxy: vybrat jednotlivé dotazy, "Select All" / "Deselect All" | Výběr funguje |
| 4.5 | Upload markdown instrukcí | File input pro 1+ markdown souborů, zobrazit názvy nahraných souborů | MD soubory se nahrají |
| 4.6 | Tlačítko "Analyze Selected" | Odeslat vybrané dotazy + instrukce přes HTMX na `/analyze` | Požadavek odejde, spinner se zobrazí |
| 4.7 | Tlačítko "Analyze All" | Odeslat všechny dotazy + instrukce přes HTMX na `/analyze-all` | Požadavek odejde |
| 4.8 | Zobrazení výsledků | Pro každý analyzovaný dotaz: původní kód + výsledek z API | Výsledky se zobrazí |
| 4.9 | Vytvořit `diff_view.html` | Diff zobrazení s přepínačem unified ↔ side-by-side | Diff se renderuje |
| 4.10 | CSS styling | Styly pro diff (zelená = přidáno, červená = odebráno), karty dotazů, layout | Vizuálně funkční |
| 4.11 | `app.js` | HTMX config, toggle diff mode, loading stavy, error handling | Interakce fungují |

**Kontrolní bod M4:** Celý workflow funguje end-to-end přes UI: upload → zobrazení → výběr → analýza → diff.

---

### Milník 5: Integrace, polish a dokumentace

**Cíl:** Finální propojení, ošetření edge cases, dokumentace.

| # | Task | Popis | Test / Kontrolní bod |
|---|------|-------|---------------------|
| 5.1 | Error handling v UI | Zobrazení chyb: nevalidní PBIX, chybějící API klíč, timeout OpenAI | Chyby se zobrazí uživateli srozumitelně |
| 5.2 | Loading stavy | Spinner/progress při upload i analýze | Uživatel vidí, že se něco děje |
| 5.3 | Validace vstupů | Max velikost PBIX, povolené přípony, sanitizace | Nevalidní vstup → srozumitelná chyba |
| 5.4 | Aktualizovat `README.md` | Přidat sekce: web UI spuštění, konfigurace `.env`, markdown instrukce | README je aktuální |
| 5.5 | Aktualizovat `README_USAGE.md` | Nový workflow: CLI + Web UI | Dokumentace odpovídá realitě |
| 5.6 | End-to-end test | Manuální test: upload reálného PBIX → analýza → diff | Celý flow funguje |
| 5.7 | Cleanup | Smazat nepoužívaný kód, ověřit `.gitignore` | Repo je čisté |

**Kontrolní bod M5:** Aplikace je připravena k používání. Dokumentace je aktuální.

---

## Pořadí implementace

```
M0 (Příprava) → M1 (OpenAI) → M2 (Diff) → M3 (Backend API) → M4 (Frontend) → M5 (Polish)
```

Každý milník je samostatně testovatelný. Žádný milník nezávisí na pozdějším.

---

## Závislosti (nové)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
jinja2>=3.1.0
openai>=1.50.0
python-dotenv>=1.0.0
diff-match-patch>=20230501
httpx>=0.27.0
```

---

## Rizika a poznámky

| Riziko | Mitigace |
|--------|----------|
| OpenAI rate limits | Implementovat retry s exponential backoff |
| Velké PBIX soubory | Omezit max upload size (např. 100 MB), async zpracování |
| Dlouhé odpovědi z API | Timeout + uživatelsky přívětivé chybové hlášení |
| Změna OpenAI API modelu | Model name jako konfigurace v `.env` |
| Bezpečnost API klíče | Klíč pouze v `.env`, nikdy v kódu ani v git |
