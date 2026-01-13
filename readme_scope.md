# PBIX_MODEL_EXTRACTOR

Nástroj pro **extrakci Power Query (M) obsahu z PBIX** a vytvoření dvou výstupů:

1) **Markdown** pro následnou analýzu (např. pomocí LLM),
2) **JSON dependency graph** (statická analýza vazeb mezi dotazy / parametry / funkcemi).

> Projekt řeší pouze **Power Query (M)**. **Neřeší DAX, relace, vizuály ani refresh.**

---

## 1) Cíl projektu (MVP)

### In-scope (MVP)

- Načíst jeden nebo více **PBIX** souborů ze složky `0_INPUTS/`.
- Z PBIX získat seznam Power Query „shared expressions“:
  - `query`, `function`, `parameter` (podle metadat / heuristik).
- Pro každý PBIX vytvořit výstupy do `1_OUTPUTS/<nazev_pbix_bez_pripony>/`:
  - `queries.md`
  - `dependency_graph.json`
- Vytvořit **statický dependency graph**: uzly = shared entities, hrany = detekované reference v M kódu.

### Out of scope

- Šifrované/heslem chráněné PBIX.
- DAX, relace, vizuály, měřítka, report layout.
- Spouštění dotazů, připojování ke zdrojům, validace dat.
- Výkonová optimalizace dotazů (to je následná analýza mimo projekt).

---

## 2) Vstupy a výstupy

### Vstupy

- `0_INPUTS/` obsahuje PBIX soubor(y) určené k analýze.

### Výstupy

- `1_OUTPUTS/<pbix_name>/`
  - `queries.md` — přehled všech dotazů/funkcí/parametrů + M kód + kroky
  - `dependency_graph.json` — graf závislostí

část **Přepisování výstupů**

- Pokud cílová složka existuje, při spuštění s `--overwrite` se smaže a vygeneruje znovu.
- Bez `--overwrite` se spuštění ukončí chybou (ochrana proti nechtěnému přepsání).

---

## 3) Formát výstupů

### 3.1 Markdown (`queries.md`)

Jeden soubor pro celý PBIX (MVP). Struktura je opakovaná sekce pro každý objekt:

```md
# <Name>

## Metadata
- Kind: query|function|parameter
- Load: true|false|null
- Group: <optional>
- Description: <optional>

## Steps
1. <step 1>
2. <step 2>
...

## Dependencies (detected)
- <OtherQueryA> (type: references, confidence: high)
- <ParameterX> (type: uses_parameter, confidence: medium)
```

## M code

```powerquery
let
    Source = ...,
    Filtered = ...
in
    Filtered
```

část **Poznámky k „Steps“**

- V MVP extrahujeme **top-level** názvy proměnných v `let ... in ...` jako kroky v pořadí, v jakém jsou uvedené.
- Neřešíme v MVP vnořené `let`, ani „UI steps“ přesně 1:1 – cílem je reprodukovatelný, jednoduchý seznam.

### 3.2 JSON dependency graph (`dependency_graph.json`)

Soubor obsahuje:

- `metadata` (verze nástroje, zdrojový PBIX, timestamp),
- `nodes` (uzly),
- `edges` (hrany).

Minimální kontrakt:

```json
{
  "metadata": {
    "tool": "pbix_model_extractor",
    "tool_version": "0.1.0",
    "source_pbix": "report.pbix",
    "generated_at": "2026-01-12T12:00:00Z",
    "parser_mode": "regex"
  },
  "nodes": [
    {
      "id": "query__sales__a1b2c3d4",
      "name": "Sales",
      "kind": "query",
      "group": "Staging",
      "load_enabled": true
    }
  ],
  "edges": [
    {
      "from": "query__sales__a1b2c3d4",
      "to": "parameter__startdate__e5f6a7b8",
      "type": "uses_parameter",
      "confidence": "medium",
      "evidence": {
        "match": "StartDate",
        "line": 12,
        "col_start": 5
      }
    }
  ]
}
```

#### Node (povinná pole)

- `id` (stabilní): doporučení `"<kind>__<slug(name)>__<hash>"`.
- `name`
- `kind`: `query | function | parameter`
- `group` (nullable)
- `load_enabled` (nullable bool — ne vždy je dostupné)

#### Edge (povinná pole)

- `from`, `to` (node id)
- `type`: `references | calls | uses_parameter`
- `confidence`: `high | medium | low`
- `evidence`: minimálně `match`, volitelně pozice

---

## 4) Pravidla pro dependency graph (MVP – režim `regex`)

Cíl MVP: “dost dobrý” statický graf, který je laditelný a vysvětlitelný (evidence + confidence).

### 4.1 Symboly, se kterými pracujeme

- `shared_names`: názvy všech sdílených objektů (query/function/parameter) z PBIX.
- Pro každý objekt navíc odvodíme `local_names`:
  - top-level proměnné v `let` bloku (např. `Source`, `Filtered Rows`, `#"Filtered Rows"`…).

### 4.2 Detekce referencí (heuristika)

Pro každý objekt `X`:

1. vezmi jeho M kód,
2. ignoruj referenci na sebe sama,
3. ignoruj názvy v `local_names` (minimalizace falešných hran),
4. pro každý `Y` v `shared_names` zkus najít výskyt:
   - identifikátor: `\bY\b` (word boundary),
   - quoted identifikátor: `#"<Y>"` (přesný match).
5. pokud nalezeno:
   - pokud bezprostředně následuje `(` → `calls`,
   - pokud `Y.kind == parameter` → `uses_parameter`,
   - jinak `references`.

### 4.3 Confidence (MVP)

- `high`: quoted match `#"<Y>"` nebo jasné `Y(`.
- `medium`: word-boundary match `\bY\b`.
- `low`: match v řetězci / komentáři nebo podezření na kolizi (např. `Y` je velmi krátké).

### 4.4 AST parser (volitelné vylepšení)

Později lze přidat `--parser ast` pro přesnější rozlišení lokálních proměnných a skutečných referencí.

---

## 5) CLI (cílové rozhraní)

Příkazy (MVP):

- `pbix-model-extractor extract <path>`  
  - `<path>` může být soubor `.pbix` nebo složka (vezme všechny `.pbix` uvnitř).

Parametry (MVP):

- `--out 1_OUTPUTS/` (default)
- `--overwrite`
- `--parser regex|ast` (default `regex`)
- `--log-level INFO|DEBUG`

---

## 6) Chybové stavy a logging

- Pokud PBIX nelze otevřít / neobsahuje očekávaná data → návratový kód != 0 + chybová hláška.
- Pokud zpracováváme více PBIX, jeden vadný soubor nesmí shodit celé batch zpracování (pokračovat na další, na konci shrnutí).
- Logovat:
  - počet nalezených nodes,
  - počet edges,
  - parser mód,
  - varování (duplicitní názvy, nízká confidence).

---

## 7) Testy (minimální sada)

`tests/fixtures/` s malými PBIX:

1) 2 query, jedna referuje druhou,
2) query + parameter,
3) query s názvem s mezerami (`#"Sales Orders"`),
4) query s lokální proměnnou stejného jména jako jiný shared objekt (test filtru `local_names`).

Testy (pytest):

- správné vytvoření výstupních souborů,
- deterministické `nodes`/`edges`,
- základní kontrola “no self loops”.

---

## 8) Akceptační kritéria (Definition of Done pro MVP)

MVP je hotové, když:

- Nástroj zpracuje PBIX ze `0_INPUTS/` a vygeneruje `queries.md` + `dependency_graph.json`.
- `queries.md` obsahuje sekce pro všechny nalezené shared objekty a jejich M kód.
- `dependency_graph.json` obsahuje `nodes` a `edges` dle kontraktu výše a u hran je vyplněné `confidence` + `evidence.match`.
- Příkaz `... --overwrite` funguje opakovaně (deterministické výstupy).
- Projdou základní testy pro fixtures.

---

## 9) Implementační plán (aby se návrh nerozjížděl)

Milníky:

- **M1**: extrakce — načtu PBIX a vylistuju nodes (name, kind, load_enabled, group, m_code).
- **M2**: generování `queries.md` (včetně Steps + Dependencies list).
- **M3**: generování `dependency_graph.json` (parser `regex`).
- **M4 (volitelné)**: `--parser ast`.

---

## 10) Technologická rozhodnutí (MVP)

- Python: **3.11+**
- Nástroje: `ruff` (lint/format), `pytest` (testy)
- Extrakční backend: preferovaně existující knihovna (např. `pbixray`), případně vlastní extraktor (PBIX jako zip + mashup).
- Výstupy: čistý text (MD, JSON), bez závislosti na Power BI runtime.
