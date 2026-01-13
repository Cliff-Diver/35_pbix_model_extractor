# PBIX Model Extractor

Krátký a výstižný popis projektu, jeho účelu a jak se s ním začít pracovat. Tento soubor je určený pro čtenáře (vývojáře i uživatele), kteří potřebují rychle pochopit co projekt dělá a jak ho spustit. 🙂

## Co to dělá

- Extrahuje Power Query (M) obsah z PBIX souborů.
- Generuje dva výstupy: `queries.md` (přehled) a `dependency_graph.json` (statická závislostní mapa).

## Rychlý start

1. Umístěte `.pbix` soubory do složky `0_INPUTS/`.
2. Spusťte extrakci (příklad):

```bash
pbix-model-extractor extract 0_INPUTS/report.pbix --out 1_OUTPUTS --overwrite --parser regex
```

## Kde jsou výstupy

- Výstupy se vytváří do `1_OUTPUTS/<nazev_pbix>/`.
- Hlavní soubory: `queries.md`, `dependency_graph.json`.

## Pro vývojáře

- Požadavky: Python 3.11+
- Lint: `ruff`

## Instalace

1. Vytvořte virtuální prostředí a aktivujte ho:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Nainstalujte závislosti:

```bash
pip install -r requirements.txt
# nebo (pokud projekt podporuje instalaci jako balíček)
pip install .
```

## Testy

- Spusťte testy pomocí `pytest`:

```bash
pytest
```

## Krátký příklad výstupu

- Ukázka malé části souboru `dependency_graph.json`:

```json
{
  "nodes": [ { "id": "query__Sales__abc123", "name": "Sales", "kind": "query" } ],
  "edges": [ { "from": "query__Sales__abc123", "to": "parameter__StartDate__def456", "type": "uses_parameter", "confidence": "medium", "evidence": { "match": "StartDate" } } ]
}
```

## Jak napsat dobrý README

# PBIX Model Extractor

Krátký popis: nástroj pro extrakci Power Query (M) obsahu z PBIX souborů a generování výstupů pro další analýzu.

## Co to dělá

- Extrahuje Power Query (M) definice (queries, functions, parameters) z PBIX.
- Generuje dva hlavní výstupy pro každý PBIX:
  - `queries.md` — přehled dotazů s jejich M kódem,
  - `dependency_graph.json` — statický graf závislostí mezi entitami.

## Rychlý start

1. Umístěte `.pbix` soubory do složky `0_INPUTS/`.
2. Spusťte extrakci (příklad):

```bash
pbix-model-extractor extract 0_INPUTS/report.pbix --out 1_OUTPUTS --overwrite --parser regex
```

Výstupy najdete v `1_OUTPUTS/<nazev_pbix>/`.

## Vstupy a výstupy

- Vstupy: složka `0_INPUTS/` s PBIX soubory.
- Výstupy: adresáře `1_OUTPUTS/<pbix_name>/` obsahující `queries.md` a `dependency_graph.json`.

## Pro vývojáře

- Požadavky: Python 3.11+
- Lint: `ruff`

## Instalace

- Vytvořte a aktivujte virtuální prostředí:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

- Vytvořte a aktivujte virtuální prostředí:

```bash
pip install -r requirements.txt
# nebo (lokálně jako balíček)
pip install .
```

## Testy

Spusťte testy pomocí `pytest`:

```bash
pytest
```

## Příklad části `dependency_graph.json`

```json
{
  "nodes": [
    { "id": "query__Sales__abc123", "name": "Sales", "kind": "query" }
  ],
  "edges": [
    {
      "from": "query__Sales__abc123",
      "to": "parameter__StartDate__def456",
      "type": "uses_parameter",
      "confidence": "medium",
      "evidence": { "match": "StartDate" }
    }
  ]
}
```

## Doporučení pro README

- Začněte stručným popisem projektu.
- Přidejte `Rychlý start` s konkrétním příkladem.
- Popište vstupy a výstupy.
- Uveďte kroky pro vývoj: instalace, testy, lint.

## Licence

Tento projekt je licencován pod MIT — viz soubor `LICENSE`.

---

Detaily a rozsáhlá specifikace najdete v [readme_scope.md](readme_scope.md).
