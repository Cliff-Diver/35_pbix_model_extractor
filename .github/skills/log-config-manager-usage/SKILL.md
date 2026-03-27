---
name: log-config-manager-usage
description: Konfigurace logování přes Loguru pomocí src.modules.log_config.log_config_manager (configure_logger, get_logger). Použij pro nastavení logování v orchestrátoru, logování v submodulech.
---

# Použití Log Config Manager (skill pro GitHub Copilot)

## Účel
Tento modul zajišťuje jednotné logování napříč orchestrátorem a všemi podskripty/moduly pomocí Loguru:
- Orchestrátor nastaví logování **jednou** na startu běhu (`configure_logger()`).
- Všechny ostatní moduly už jen získávají logger přes `get_logger()` a logují.

## Kde to v repozitáři je
Modul pro logování včetně dokumentace je v:
- `src/modules/log_config/`
- související: `email_config.py`, `teams_notification.py`, `log_config_manager.md`

## Rozsah (repo logging stack)
Hlavní veřejné API pro použití v kódu:
- `src/modules/log_config/log_config_manager.py`: `configure_logger(...)` + `get_logger(...)`

## Základní pravidla používání

### 1. `configure_logger()` volej jen 1×
- Volej **pouze v orchestrátoru** (entrypoint, `main`, task runner) hned na začátku.
- `configure_logger()` provádí interně `logger.remove()` a kompletně přenastaví sinky.
  - Opakované volání uprostřed běhu může způsobit nečekaný „reset“ logování.

### 2. V podmodulech používej jen `get_logger()`
- V podmodulech nikdy znovu nekonfiguruj sinky.
- Vždy loguj přes objekt vrácený `get_logger(...)`.

### 3. `orchestrator_name` musí být bezpečný pro Windows cestu
`orchestrator_name` se používá jako název složky. Nepoužívej znaky:
`< > : " / \ | ? *`

### 4. ERRORS/ a atexit – důležité chování
- Modul vždy udržuje složku `ERRORS/` pro logy z běhů, ve kterých se vyskytla chyba.
- Kopírování chybových logů do `ERRORS/` probíhá při ukončení programu (přes `atexit`).
- `retention` promazává pouze staré `*.log` v kořenové složce orchestrátoru, **ne v `ERRORS/`**.

## Šablona pro orchestrátor (explicitní výchozí nastavení)
Kvůli jednoznačnosti a auditovatelnosti předávej všechny parametry explicitně.

```python
from src.modules.log_config.log_config_manager import configure_logger, get_logger
from src.modules.path_config.path_config import LOGS_DIR

def main():
    result = configure_logger(
        orchestrator_name="my_orchestrator",
        log_file_name="run",
        log_dir=LOGS_DIR,
        retention=10,
        level="DEBUG",

        send_email_on_error=False,
        recipient_email="dan.stoszek@ceskatelevize.cz",
        email_log_level="ERROR",

        send_teams_on_error=False,
        teams_log_level="ERROR",
        production_mode=True,
    )

    log = get_logger(module_name="orchestrator", user="service")
    log.info("Orchestrator started")
# Pozn.: user může být klidně název funkce (např. "main") nebo identifikátor služby. Smyslem je mít v logu snadno dohledatelné, odkud z kódu zpráva pochází – zvol si tedy hodnotu, která ti nejvíc pomůže při čtení logů.
    
   
if __name__ == "__main__":
    main()
```
