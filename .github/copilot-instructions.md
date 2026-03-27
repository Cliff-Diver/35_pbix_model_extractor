# Copilot Instructions

Při generování kódu dodržuj následující zásady:

1. **Komentáře**  
   - Každý důležitý blok kódu doplň srozumitelným komentářem v českém jazyce.  
   - Komentáře mají vysvětlovat *proč* se něco dělá, ne jen *co* se dělá.

2. **Pojmenování a texty**
   - Názvy proměnných, funkcí a uživatelské výstupy piš v angličtině.
   - Pojmenování má být výstižné a konzistentní.

3. **Kvalita a struktura**
   - Preferuj jednoduché, přehledné řešení před zbytečnou složitostí.
   - Preferuj malé, znovupoužitelné funkce.
   - Kód děl na logické celky, vyhýbej se dlouhým a zanořeným funkcím.
   - Logiku odděluj od vstupů/výstupů tak, aby byla snadno testovatelná.

4. **Robustnost**
   - Navrhuj řešení tak, aby rozumně zvládalo běžné chyby a neočekávané vstupy.

## Závislosti a prostředí
- U jazyků, kde to dává smysl, používej izolované prostředí pro závislosti.

## Informace o projektu
- Struktura složek a souborů je popsána v `folder_structure.md`. Soubory vytvářej v souladu s touto strukturou.
- Pro práci s cestami využij modul `path_config.py`.
- Pro logování používej `log_config_manager.py` a dodržuj jeho konvenci pro získávání loggeru.

## Jazykově specifická pravidla
- Pro Python soubory platí detailní pravidla v `python.instructions.md`.
---

Tyto pokyny jsou závazné pro veškerý kód generovaný Copilotem v tomto projektu.
