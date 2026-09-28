"""Unit tests for knowledge_graph.serialization (Milestone 7)."""

import json
from pathlib import Path
import pytest

from src.knowledge_graph.builder import build_from_analysis
from src.knowledge_graph.schema import RelationshipType
from src.knowledge_graph.serialization import (
    DEFAULT_GRAPHML_PATH,
    DEFAULT_JSON_PATH,
    export_graphml,
    export_json,
    import_graphml,
    import_json,
)


@pytest.fixture
def sample_kg():
    """Load sample KnowledgeGraph fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    return build_from_analysis(fixture_path)


def test_json_export_and_import_roundtrip(sample_kg, tmp_path):
    """Verify complete lossless JSON roundtrip of sample repository graph."""
    out_file = tmp_path / "graph.json"
    json_str = export_json(sample_kg, file_path=out_file)

    parsed = json.loads(json_str)
    assert len(parsed["nodes"]) == 26
    assert len(parsed["relationships"]) == 35

    # Re-import from JSON
    reloaded_kg = import_json(out_file)
    assert reloaded_kg.number_of_nodes() == 26
    assert reloaded_kg.number_of_edges() == 35

    # Check that metadata and properties are preserved
    user_node = reloaded_kg.get_node("class:models/user.py:User")
    assert user_node is not None
    assert user_node["name"] == "User"
    assert user_node["properties"]["bases"] == ["BaseModel"]

    # Check unresolved call preserved
    assert reloaded_kg.has_relationship(
        "func:main.py:main",
        "unresolved:print",
        RelationshipType.CALLS,
    )


def test_graphml_export_and_import_roundtrip(sample_kg, tmp_path):
    """Verify GraphML export and import preserving complex nested properties."""
    out_file = tmp_path / "graph.graphml"
    export_graphml(sample_kg, file_path=out_file)
    assert out_file.exists()

    reloaded_kg = import_graphml(out_file)
    assert reloaded_kg.number_of_nodes() == 26
    assert reloaded_kg.number_of_edges() == 35

    # Verify nested JSON unpacks properly
    user_node = reloaded_kg.get_node("class:models/user.py:User")
    assert user_node is not None
    assert user_node["name"] == "User"
    assert isinstance(user_node.get("properties"), dict)
    assert user_node["properties"]["bases"] == ["BaseModel"]


def test_default_output_generation(sample_kg):
    """Verify serialization to standard ProjectGenome generated artifacts."""
    export_json(sample_kg, file_path=DEFAULT_JSON_PATH)
    assert DEFAULT_JSON_PATH.exists()
    assert DEFAULT_JSON_PATH.stat().st_size > 0

    export_graphml(sample_kg, file_path=DEFAULT_GRAPHML_PATH)
    assert DEFAULT_GRAPHML_PATH.exists()
    assert DEFAULT_GRAPHML_PATH.stat().st_size > 0
