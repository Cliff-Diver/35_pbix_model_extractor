# PBIX Model Extractor - Usage

Nástroj pro extrakci Power Query (M) obsahu z PBIX souborů.

## Instalace

```bash
pip install -e .
```

## Použití

```bash
pbix-model-extractor extract <path> [--out OUTPUT_DIR] [--overwrite] [--parser regex|ast] [--log-level INFO|DEBUG]
```

Příklady:

```bash
# Extrakce jednoho PBIX souboru
pbix-model-extractor extract 0_INPUT/report.pbix

# Extrakce všech PBIX v složce
pbix-model-extractor extract 0_INPUT/

# S přepsáním existujících výstupů
pbix-model-extractor extract 0_INPUT/ --overwrite
```

## Výstupy

Pro každý PBIX soubor vytvoří složku `<pbix_name>/` s:

- `queries.md` - Markdown s přehledem všech dotazů/funkcí/parametrů
- `dependency_graph.json` - JSON graf závislostí

## Testy

```bash
python -m pytest tests/
```

## Linting a formátování

```bash
ruff check src/
ruff format src/
```