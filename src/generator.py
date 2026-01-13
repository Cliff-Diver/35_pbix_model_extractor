from typing import List, Dict, Any
import re
from pathlib import Path
from src.dependency import detect_dependencies_regex


def parse_m_steps(m_code: str) -> List[str]:
    """Extract top-level variable names from let ... in ... expression."""
    # Find the let ... in block
    match = re.search(r"let\s+(.*?)\s+in\s+", m_code, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    let_part = match.group(1)

    # Use regex to find all variable assignments: variable_name = expression,
    # But avoid nested lets and comments
    variables = []
    # Pattern to match variable = (but not in comments or nested)
    # This is simplified - real M parser would be better
    lines = let_part.split('\n')
    for line in lines:
        line = line.strip()
        # Skip comments and empty lines
        if line.startswith('//') or line.startswith('/*') or not line:
            continue
        # Look for variable = pattern at start of line
        var_match = re.match(r'^([^=\n]+)\s*=', line)
        if var_match:
            var_name = var_match.group(1).strip()
            # Handle quoted names
            if var_name.startswith('#"') and var_name.endswith('"'):
                var_name = var_name[2:-1]
            variables.append(var_name)

    return variables


def generate_queries_md(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], output_path: Path, source_name: str = None
):
    """Generate queries.md file.

    - `source_name` will be used as the single H1 for the file (name of analyzed source PBIX).
    - For each node: `## <node name>` followed by `### Metadata "<node name>"`,
      `### Steps "<node name>"`, `### Dependencies (detected) "<node name>"`, and
      `### M code "<node name>"` sections.
    """
    # Create node id to name mapping
    node_map = {node["id"]: node["name"] for node in nodes}

    with open(output_path, "w", encoding="utf-8") as f:
        # Single H1: source name (fallback to output filename if not provided)
        title = source_name or output_path.stem
        f.write(f"# {title}\n\n")

        # Intro comment (HTML comment so it doesn't affect rendered structure)
        f.write("<!--\n")
        f.write("Poznámka k formátu:\n")
        f.write("- # : název analyzovaného PBIX (jediné H1).\n")
        f.write("- ## : název dotazu (query).\n")
        f.write("- ### Metadata \"Název dotazu\": základní informace o dotazu.\n")
        f.write("  - Kind: typ položky (query/function/parameter).\n")
        f.write("  - Load: zda je dotaz načítán do modelu (true/false/null).\n")
        f.write("  - Group: volitelná skupina (pokud je k dispozici).\n")
        f.write("- ### Steps \"Název dotazu\": pořadí kroků z M kódu (top-level proměnné v let...in).\n")
        f.write("- ### Dependencies (detected) \"Název dotazu\": detekované závislosti na jiných dotazech/parametrech.\n")
        f.write("- ### M code \"Název dotazu\": původní M (Power Query) kód.\n")
        f.write("-->\n\n")

        for node in nodes:
            node_name = node["name"]
            f.write(f"## {node_name}\n\n")

            # Metadata section as H3 including the query name
            f.write(f"### Metadata \"{node_name}\"\n\n")
            f.write(f"- Kind: {node['kind']}\n")
            load = node.get("load_enabled")
            f.write(f"- Load: {load if load is not None else 'null'}\n")
            group = node.get("group")
            if group:
                f.write(f"- Group: {group}\n")
            f.write("\n")

            # Steps section
            f.write(f"### Steps \"{node_name}\"\n\n")
            steps = parse_m_steps(node["m_code"])
            if steps:
                for i, step in enumerate(steps, 1):
                    f.write(f"{i}. {step}\n")
            else:
                f.write("- (no steps detected)\n")
            f.write("\n")

            # Dependencies
            f.write(f"### Dependencies (detected) \"{node_name}\"\n\n")
            deps = [edge for edge in edges if edge.get("from") == node.get("id")]
            if deps:
                for dep in deps:
                    target_name = node_map.get(dep.get("to"), dep.get("to"))
                    f.write(
                        f"- {target_name} (type: {dep.get('type')}, confidence: {dep.get('confidence')})\n"
                    )
            else:
                f.write("- None detected\n")
            f.write("\n")

            # M code
            f.write(f"### M code \"{node_name}\"\n\n")
            f.write("```powerquery\n")
            f.write(node["m_code"])
            f.write("\n```\n\n")


def generate_dependency_graph_json(
    nodes: List[Dict[str, Any]],
    output_path: Path,
    pbix_name: str,
    parser_mode: str = "regex",
):
    """Generate dependency_graph.json file."""
    import json
    from datetime import datetime

    # Detect dependencies
    if parser_mode == "regex":
        edges = detect_dependencies_regex(nodes)
    else:
        edges = []  # TODO: AST parser

    graph = {
        "_comment": "Tento soubor obsahuje výstup nástroje pbix_model_extractor: 'metadata' s informacemi o generování, 'nodes' seznam uzlů (queries/functions/parameters) a 'edges' seznam detekovaných závislostí.",
        "metadata": {
            "tool": "pbix_model_extractor",
            "tool_version": "0.1.0",
            "source_pbix": f"{pbix_name}.pbix",
            "generated_at": datetime.now().isoformat(),
            "parser_mode": parser_mode,
        },
        "nodes": [
            {
                "id": node["id"],
                "name": node["name"],
                "kind": node["kind"],
                "group": node.get("group"),
                "load_enabled": node.get("load_enabled"),
            }
            for node in nodes
        ],
        "edges": edges,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
