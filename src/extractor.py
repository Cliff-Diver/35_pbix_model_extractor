from pathlib import Path
from typing import List, Dict, Any
from pbixray import PBIXRay
import uuid


class PBIXExtractor:
    def __init__(self, pbix_path: Path):
        self.pbix_path = pbix_path
        self.model = PBIXRay(str(pbix_path))
        # Namespace for deterministic UUIDs per PBIX file
        try:
            pbix_resolved = str(pbix_path.resolve())
        except Exception:
            pbix_resolved = str(pbix_path)
        self._pbix_ns = uuid.uuid5(uuid.NAMESPACE_URL, pbix_resolved)

    def extract_nodes(self) -> List[Dict[str, Any]]:
        nodes = []

        # Get list of loaded tables (Load = enabled)
        # model.tables contains only tables that are loaded into the data model
        loaded_tables = set(self.model.tables) if hasattr(self.model, 'tables') else set()

        # Extract queries and functions from power_query
        power_query_df = self.model.power_query
        for _, row in power_query_df.iterrows():
            name = row["TableName"]
            expression = row["Expression"]
            # Heuristic: if expression starts with (params) => it's a function, else query
            if expression.strip().startswith("(") and "=>" in expression:
                kind = "function"
                # Functions don't have a Load property
                load_enabled = None
            else:
                kind = "query"
                # Check if this query is loaded into the model
                load_enabled = name in loaded_tables
            # Deterministic id based on PBIX namespace, kind and name
            sanitized = name.replace(' ', '_').lower()
            uid = uuid.uuid5(self._pbix_ns, f"{kind}:{name}")
            node = {
                "id": f"{kind}__{sanitized}__{uid.hex}",
                "name": name,
                "kind": kind,
                "m_code": expression,
                "group": None,  # TODO: extract from TOM metadata (requires Microsoft.AnalysisServices.Tabular)
                "load_enabled": load_enabled,
            }
            nodes.append(node)

        # Extract parameters
        parameters_df = self.model.m_parameters
        for _, row in parameters_df.iterrows():
            name = row["ParameterName"]
            sanitized = name.replace(' ', '_').lower()
            uid = uuid.uuid5(self._pbix_ns, f"parameter:{name}")
            node = {
                "id": f"parameter__{sanitized}__{uid.hex}",
                "name": name,
                "kind": "parameter",
                "m_code": row["Expression"],
                "group": None,  # TODO: extract from TOM metadata
                "load_enabled": None,  # Parameters don't have a Load property
            }
            nodes.append(node)

        return nodes


def extract_from_pbix(pbix_path: Path) -> List[Dict[str, Any]]:
    extractor = PBIXExtractor(pbix_path)
    return extractor.extract_nodes()
