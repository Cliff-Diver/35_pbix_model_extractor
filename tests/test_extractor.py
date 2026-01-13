import pytest
from pathlib import Path
from src.extractor import extract_from_pbix

def test_extract_from_pbix():
    """Test extraction from existing PBIX file."""
    pbix_path = Path("0_INPUT/sledovani_zmen.pbix")
    if not pbix_path.exists():
        pytest.skip("Test PBIX file not found")
    
    nodes = extract_from_pbix(pbix_path)
    
    assert len(nodes) > 0
    assert all('id' in node for node in nodes)
    assert all('name' in node for node in nodes)
    assert all('kind' in node for node in nodes)
    assert all('m_code' in node for node in nodes)
    
    # Check kinds
    kinds = {node['kind'] for node in nodes}
    assert kinds.issubset({'query', 'function', 'parameter'})

def test_extract_nodes_structure():
    """Test that extracted nodes have required fields."""
    pbix_path = Path("0_INPUT/sledovani_zmen.pbix")
    if not pbix_path.exists():
        pytest.skip("Test PBIX file not found")
    
    nodes = extract_from_pbix(pbix_path)
    
    for node in nodes:
        assert isinstance(node['id'], str)
        assert isinstance(node['name'], str)
        assert node['kind'] in ['query', 'function', 'parameter']
        assert isinstance(node['m_code'], str)
        assert 'group' in node
        assert 'load_enabled' in node