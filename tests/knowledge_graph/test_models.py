"""Unit tests for knowledge_graph.models (Milestone 2)."""

import json
from pathlib import Path

from src.knowledge_graph.models import (
    AnalyzerOutput,
    Entity,
    Location,
    Relationship,
)
from src.knowledge_graph.schema import NodeType, RelationshipType


def test_entity_model_creation():
    """Verify Entity Pydantic model parses canonical entity attributes."""
    entity = Entity(
        id="class:models/user.py:User",
        type=NodeType.CLASS,
        name="User",
        path="models/user.py",
        location=Location(file="models/user.py", start_line=4, end_line=12),
        properties={"bases": ["BaseModel"], "docstring": "User model"},
    )
    assert entity.id == "class:models/user.py:User"
    assert entity.is_analyzer_entity is True
    assert entity.is_synthetic is False
    assert entity.properties["bases"] == ["BaseModel"]


def test_relationship_model_classification():
    """Verify Relationship model classifies primitive, derived, and unresolved edges."""
    primitive_rel = Relationship(
        id="rel:calls:1",
        source="fn_a",
        type=RelationshipType.CALLS,
        target="fn_b",
    )
    assert primitive_rel.is_primitive is True
    assert primitive_rel.is_derived is False
    assert primitive_rel.is_unresolved is False

    derived_rel = Relationship(
        id="rel:dep:1",
        source="file_a",
        type=RelationshipType.DEPENDS_ON,
        target="file_b",
        properties={"derived": True, "reasons": ["CALLS", "IMPORTS"], "weight": 2},
    )
    assert derived_rel.is_primitive is False
    assert derived_rel.is_derived is True
    assert derived_rel.is_unresolved is False

    unresolved_rel = Relationship(
        id="rel:calls:unresolved",
        source="fn_main",
        type=RelationshipType.CALLS,
        target="unresolved:print",
        properties={"raw_call": "print", "resolved": False},
    )
    assert unresolved_rel.is_unresolved is True


def test_parse_sample_analysis_json_fixture():
    """Verify AnalyzerOutput parses the complete Nyasa v2.0 sample fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    assert fixture_path.exists(), "Sample fixture data/sample/sample_analysis.json must exist"

    with open(fixture_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    analyzer_output = AnalyzerOutput.model_validate(raw_data)
    assert len(analyzer_output.entities) == 19
    assert len(analyzer_output.relationships) == 35

    # Count primitive, derived, unresolved
    primitive_count = sum(1 for r in analyzer_output.relationships if r.is_primitive)
    derived_count = sum(1 for r in analyzer_output.relationships if r.is_derived)
    unresolved_count = sum(1 for r in analyzer_output.relationships if r.is_unresolved)

    assert primitive_count == 32
    assert derived_count == 3
    assert unresolved_count == 7
