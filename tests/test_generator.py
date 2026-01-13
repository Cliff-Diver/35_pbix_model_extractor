import pytest
from pathlib import Path
import json
import tempfile
from src.generator import generate_queries_md, generate_dependency_graph_json
from src.extractor import extract_from_pbix

def test_generate_queries_md():
    """Test generation of queries.md."""
    pbix_path = Path("0_INPUT/sledovani_zmen.pbix")
    if not pbix_path.exists():
        pytest.skip("Test PBIX file not found")
    
    nodes = extract_from_pbix(pbix_path)
    edges = []  # For simplicity
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
    
    generate_queries_md(nodes, edges, temp_path, pbix_path.stem)

    content = temp_path.read_text(encoding='utf-8')
    assert "# " in content  # Has headers
    # New format uses H3 sections with the query name included
    assert "### Metadata" in content
    assert "### M code" in content
    
    temp_path.unlink()

def test_generate_dependency_graph_json():
    """Test generation of dependency_graph.json."""
    pbix_path = Path("0_INPUT/sledovani_zmen.pbix")
    if not pbix_path.exists():
        pytest.skip("Test PBIX file not found")
    
    nodes = extract_from_pbix(pbix_path)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    generate_dependency_graph_json(nodes, temp_path, "test.pbix")
    
    content = temp_path.read_text(encoding='utf-8')
    data = json.loads(content)

    # Expect a top-level helper comment field describing the file
    assert "_comment" in data
    assert isinstance(data["_comment"], str)

    assert "metadata" in data
    assert "nodes" in data
    assert "edges" in data
    assert data["metadata"]["tool"] == "pbix_model_extractor"
    assert len(data["nodes"]) == len(nodes)
    
    temp_path.unlink()