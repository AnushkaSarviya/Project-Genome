"""Unit tests for knowledge_graph.validation (Milestone 6)."""

from pathlib import Path
import pytest

from src.knowledge_graph.builder import build_from_analysis
from src.knowledge_graph.graph import KnowledgeGraph, KnowledgeGraphError
from src.knowledge_graph.schema import NodeType, RelationshipType
from src.knowledge_graph.validation import validate_graph, validate_or_raise


@pytest.fixture
def sample_kg():
    """Load sample KnowledgeGraph fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    return build_from_analysis(fixture_path)


def test_validate_sample_fixture_graph(sample_kg):
    """Verify sample analyzer KnowledgeGraph passes validation cleanly."""
    report = validate_graph(sample_kg)
    assert report.is_valid is True
    assert len(report.errors) == 0
    validate_or_raise(sample_kg)  # Should not raise


def test_validate_detects_module_entity():
    """Verify validation flags deprecated Module entities as errors."""
    kg = KnowledgeGraph()
    # Force insert a Module node (e.g. bypassing builder)
    kg.add_node("mod_1", NodeType.MODULE, "mymodule")
    report = validate_graph(kg)
    assert report.is_valid is False
    assert any(e.category == "module_entity" for e in report.errors)

    with pytest.raises(KnowledgeGraphError, match="validation failed"):
        validate_or_raise(kg)


def test_validate_unresolved_call_target_synthetic_flag():
    """Verify unresolved call targets must be marked as synthetic."""
    kg = KnowledgeGraph()
    kg.add_node("fn_main", NodeType.FUNCTION, "main")
    # Add unresolved target without is_synthetic=True
    kg.add_node("unresolved:foo", NodeType.UNRESOLVED_REFERENCE, "foo", is_synthetic=False)
    kg.add_relationship("fn_main", "unresolved:foo", RelationshipType.CALLS)

    report = validate_graph(kg)
    assert report.is_valid is False
    assert any(e.category == "unresolved_reference" for e in report.errors)
