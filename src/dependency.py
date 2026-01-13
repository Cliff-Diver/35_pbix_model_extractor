from typing import List, Dict, Any
import re


def detect_dependencies_regex(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect dependencies between nodes using regex heuristics."""
    edges = []
    # Map name -> list of nodes sharing that name (handles duplicates)
    name_map: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        name_map.setdefault(n["name"], []).append(n)

    for node in nodes:
        m_code = node["m_code"]
        # Get local names from let ... in
        local_names = extract_local_names(m_code)

        for name, targets in name_map.items():
            if name == node["name"]:
                continue  # Skip self
            if name in local_names:
                continue  # Skip local variables

            # Check for references
            quoted_pattern = r'#"\s*' + re.escape(name) + r"\s*\""
            word_pattern = r"\b" + re.escape(name) + r"\b"

            quoted_match = re.search(quoted_pattern, m_code, re.IGNORECASE)
            word_match = re.search(word_pattern, m_code, re.IGNORECASE)

            match_obj = quoted_match or word_match
            if not match_obj:
                continue

            # For each possible target with the same name, create an edge.
            for target_node in targets:
                # Determine type
                if re.search(r"\b" + re.escape(name) + r"\s*\(", m_code, re.IGNORECASE):
                    dep_type = "calls"
                elif target_node.get("kind") == "parameter":
                    dep_type = "uses_parameter"
                else:
                    dep_type = "references"

                # Confidence: quoted identifiers -> high; if multiple targets, lower confidence
                if quoted_match:
                    confidence = "high"
                else:
                    confidence = "low" if len(targets) > 1 else "medium"

                evidence = {
                    "match": name,
                    "line": get_line_number(m_code, match_obj.start()),
                    "col_start": match_obj.start() - m_code.rfind("\n", 0, match_obj.start()) - 1,
                }

                edge = {
                    "from": node["id"],
                    "to": target_node["id"],
                    "type": dep_type,
                    "confidence": confidence,
                    "evidence": evidence,
                }
                edges.append(edge)

    return edges


def extract_local_names(m_code: str) -> set:
    """Extract local variable names from let ... in expression."""
    local_names = set()
    # Simple regex to find let ... in
    match = re.search(r"let\s+(.*?)\s+in\s+", m_code, re.DOTALL | re.IGNORECASE)
    if match:
        let_part = match.group(1)
        # Split by commas
        for line in let_part.split(","):
            line = line.strip()
            if "=" in line:
                var_name = line.split("=")[0].strip()
                # Handle quoted names
                if var_name.startswith('#"') and var_name.endswith('"'):
                    var_name = var_name[2:-1]
                local_names.add(var_name)
    return local_names


def get_line_number(text: str, pos: int) -> int:
    """Get line number for a position in text."""
    return text[:pos].count("\n") + 1
