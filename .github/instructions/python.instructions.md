---
name: 'Python Standards'
description: 'Coding conventions for Python files'
applyTo: '**/*.py'
---

# Python Programming Instructions

Tento soubor obsahuje specifická pravidla pro programování v Pythonu. Obecné zásady pro komentáře, modularitu a bezpečnost jsou definovány v `copilot-instructions.md`.

## 1. Standardy kódu

### 1.1 PEP 8
- Dodržuj standard [PEP 8](https://peps.python.org/pep-0008/) pro formátování kódu
- Maximální délka řádku: **120 znaků**
- Odsazení: **4 mezery** (nikdy tabulátory)
- Cílová verze Pythonu: **3.13**

### 1.2 Docstringy (PEP 257)
- Každá funkce, třída a modul musí obsahovat docstring ve formátu [PEP 257](https://peps.python.org/pep-0257/)
- Docstring musí obsahovat:
  - Popis účelu funkce/třídy
  - Parametry (včetně typů)
  - Návratovou hodnotu (včetně typu)
  - U složitějších funkcí i příklady použití a popis logiky
  
### 1.3 Typové anotace (Type Hints)
- **Povinné**: Používej typové anotace u všech parametrů funkcí a návratových hodnot
- Používej `typing` modul pro složitější typy (Optional, Union, List, Dict, atd.)
- Nedovoluj netypované definice funkcí (`disallow_untyped_defs`)
- Příklad:
  ```python
  from typing import Optional, List
  
  def process_data(items: List[str], threshold: Optional[int] = None) -> dict[str, int]:
      """Process list of items and return counts."""
      pass
  ```

## 2. Ruff - Linter a Formatter

### 2.1 Základní konfigurace
```toml
[tool.ruff]
line-length = 120
indent-width = 4
target-version = "py313"
```

### 2.2 Aktivovaná pravidla
Kód musí splňovat následující sady pravidel:

- **A** (flake8-builtins) - Kontrola stínění vestavěných funkcí
- **ANN** (flake8-annotations) - Kontrola typových anotací
- **ARG** (flake8-unused-arguments) - Nepoužité argumenty
- **B** (flake8-bugbear) - Běžné chyby a anti-patterny
- **C4** (flake8-comprehensions) - Comprehensions optimalizace
- **D** (pydocstyle) - Docstring konvence
- **DTZ** (flake8-datetimez) - Práce s datetime a timezone
- **E** (pycodestyle Error) - Chyby stylu kódu
- **ERA** (eradicate) - Zakomentovaný mrtvý kód
- **F** (pyflakes) - Logické chyby v kódu
- **FLY** (flynt) - Optimalizace string formátování
- **I** (isort) - Třídění importů
- **LOG** (flake8-logging) - Správné použití loggingu
- **N** (pep8-naming) - Pojmenování podle PEP 8
- **PD** (pandas-vet) - Pandas best practices
- **PERF** (perflint) - Výkonnostní optimalizace
- **PL** (pylint) - Obecná kvalita kódu
- **PT** (flake8-pytest-style) - Pytest best practices
- **PTH** (flake8-use-pathlib) - Používej pathlib místo os.path
- **Q** (flake8-quotes) - Konzistentní uvozovky
- **RET** (flake8-return) - Optimalizace return statements
- **RSE** (flake8-raise) - Správné vyhazování výjimek
- **RUF** (ruff-specific) - Ruff-specifická pravidla
- **S** (bandit) - Bezpečnostní kontroly
- **SIM** (flake8-simplify) - Zjednodušení kódu
- **TC** (flake8-type-checking) - Type checking optimalizace
- **TD** (flake8-todos) - TODO/FIXME komentáře
- **TID** (flake8-tidy-imports) - Čisté importy
- **TRY** (tryceratops) - Exception handling best practices
- **UP** (pyupgrade) - Moderní Python syntax
- **W** (pycodestyle Warning) - Varování stylu kódu

### 2.3 Ignorovaná pravidla
```toml
ignore = ["PLR0913", "D203", "D211", "D212", "D213"]
```

## 3. Mypy - Type Checker

### 3.1 Základní konfigurace
```toml
[tool.mypy]
python_version = "3.13"
strict = true
```

### 3.2 Strict Mode pravidla
- `disallow_untyped_defs = true` - Všechny funkce musí mít typové anotace
- `disallow_untyped_calls = true` - Nelze volat netypované funkce
- `disallow_untyped_decorators = true` - Dekorátory musí být typované
- `warn_return_any = true` - Varování při návratu Any typu
- `warn_redundant_casts = true` - Varování při zbytečném přetypování
- `warn_unused_configs = true` - Varování při nepoužité konfiguraci
- `warn_unused_ignores = true` - Varování při zbytečném type: ignore
- `warn_unreachable = true` - Varování při nedosažitelném kódu

### 3.3 Any typ omezení
- `disallow_any_unimported = true` - Any z neimportovaných modulů
- `disallow_any_expr = true` - Any v expresích
- `disallow_any_decorated = true` - Any v dekorátorech
- `disallow_any_generics = true` - Any v generických typech

### 3.4 Další pravidla
- `implicit_optional = true` - Automatické Optional pro default None
- `strict_equality = true` - Striktní kontrola rovnosti
- `disallow_subclassing_any = true` - Zakázat dědění z Any
- `ignore_missing_imports = true` - Ignorovat chybějící importy (pro third-party)

### 3.5 Zobrazení chyb
- `show_error_context = true` - Zobrazit kontext chyby
- `show_column_numbers = true` - Zobrazit čísla sloupců
- `show_error_code_links = true` - Zobrazit odkazy na dokumentaci chyb

## 4. Prostředí a spouštění

### 4.1 Virtuální prostředí
- **Vždy** používej virtuální prostředí (`venv`) pro správu závislostí
- Všechny skripty musí být spouštěny v aktivovaném venv

### 4.2 Závislosti
- Všechny závislosti musí být uvedeny v `requirements.txt` s **přesnými verzemi**
- Formát: `package==1.2.3`

### 4.3 Spouštění skriptů
- Python skripty spouštěj příkazem: `py` nebo `python`
- Příklad: `py script.py` nebo `python -m module`

## 5. Import statements

### 5.1 Třídění importů (isort)
Importy musí být seřazeny v následujícím pořadí:
1. Standardní knihovna
2. Third-party balíčky
3. Lokální moduly

Každá skupina oddělena prázdným řádkem.

### 5.2 Správa cest v projektu
- **Vždy používej modul `path_config.py`** pro práci s cestami v projektu
- Modul definuje konstanty pro všechny klíčové složky projektu:
  - `BASE_DIR` - kořenová složka projektu
  - `LOGS_DIR` - složka pro logy
  - `DATA_DIR`, `CONFIG_DIR`, `SRC_DIR`, `TEST_DIR` atd.
- **Nikdy nekonstruuj cesty ručně** - vždy používej předdefinované konstanty
- Příklad správného použití:
  ```python
  from src.modules.path_config.path_config import LOGS_DIR, DATA_DIR, BASE_DIR
  
  # Správně - použití konstant z path_config
  log_file = LOGS_DIR / "my_app" / "run.log"
  config_file = BASE_DIR / "config" / "settings.json"
  
  # Špatně - ruční konstrukce cest
  # log_file = Path(__file__).parent.parent / "logs" / "run.log"  # NEPOUŽÍVAT!
  ```
- Pro další práce s cestami používej `pathlib.Path` metody (`.exists()`, `.mkdir()`, `.glob()`, atd.)

## 6. Logging

### 6.1 Používej log_config_manager.py
- **Vždy používej modul `log_config_manager.py`** pro logování v projektu
- Modul je založen na knihovně **loguru** a poskytuje:
  - Jednotné formátování logů
  - Automatickou správu logovacích souborů (rotace, retention)
  - Emailové notifikace při chybách (EmailNotifier)
  - Microsoft Teams notifikace při chybách (TeamsNotifier)
  - Automatické kopírování chybových logů do ERRORS složky

### 6.2 Použití v orchestrátoru (hlavní aplikace)
```python
from src.modules.log_config.log_config_manager import configure_logger, get_logger
from src.modules.path_config.path_config import LOGS_DIR

# Konfigurace loggeru na začátku aplikace (pouze jednou)
notifier = configure_logger(
    orchestrator_name="my_app",
    log_file_name="run",
    log_dir=LOGS_DIR,
    retention=5,
    level="INFO",
    send_email_on_error=True,
    recipient_email="admin@example.com",
    email_log_level="ERROR",
    send_teams_on_error=True,
    teams_log_level="ERROR"
)

# Získání loggeru pro orchestrátor
log = get_logger(module_name="orchestrator", user="user_name")
log.info("Application started")

# Na konci: odeslání souhrnu chyb, pokud nastaly
if notifier:
    notifier.send_summary_if_errors()
```

### 6.3 Použití v subscriptech (submodulech)
```python
from src.modules.log_config.log_config_manager import get_logger

# V subskriptu: pouze získání loggeru (konfigurace již proběhla v orchestrátoru)
log = get_logger(module_name="data_processor", user="user_name")
log.info("Processing started")
log.debug("Processing data batch")
log.error("Error occurred")
```

### 6.4 Důležitá pravidla
- **Orchestrátor** volá `configure_logger()` pro nastavení loggingu
- **Subscripte** volají pouze `get_logger()` pro získání loggeru
- **Nikdy nepoužívej `print()`** pro debugging - vždy používej logger
- **Vždy specifikuj `module_name`** pro identifikaci zdroje logů
- **Volitelně specifikuj `user`** pro sledování, kdo akci inicioval
- Používej správné úrovně logování:
  - `TRACE` - velmi detailní debug informace
  - `DEBUG` - detailní informace pro debugging
  - `INFO` - běžné informační zprávy
  - `SUCCESS` - úspěšné dokončení operace
  - `WARNING` - varování, které nevyžaduje okamžitou akci
  - `ERROR` - chyba, která nevyžaduje zastavení aplikace
  - `CRITICAL` - kritická chyba vyžadující zastavení aplikace

## 7. Exception handling

### 7.1 Best practices
- Vždy specifikuj konkrétní výjimky místo obecného `except:`
- Používej `try/except` tam, kde očekáváš možná selhání
- Re-raise výjimky kde je to vhodné pomocí `raise` nebo `raise from`
- Validuj vstupní data

---

**Poznámka**: Tyto pokyny jsou závazné pro veškerý Python kód generovaný Copilotem v tomto projektu.
