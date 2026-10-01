"""Unit tests for knowledge_graph.queries (Milestone 5)."""

from pathlib import Path
import pytest

from src.knowledge_graph.builder import build_from_analysis
from src.knowledge_graph.queries import (
    find_nodes_by_name,
    find_nodes_by_type,
    get_node,
    get_relationships,
    get_relationships_by_type,
    get_repository_entities,
    get_statistics,
    get_structural_context,
    get_synthetic_nodes,
)
from src.knowledge_graph.schema import NodeType, RelationshipType


@pytest.fixture
def sample_kg():
    """Load sample KnowledgeGraph fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    return build_from_analysis(fixture_path)


def test_get_node_and_find_by_name(sample_kg):
    """Verify node retrieval and name-based search."""
    node = get_node(sample_kg, "class:models/user.py:User")
    assert node is not None
    assert node["name"] == "User"

    # Exact match
    users = find_nodes_by_name(sample_kg, "User", node_type=NodeType.CLASS)
    assert len(users) == 1
    assert users[0]["id"] == "class:models/user.py:User"

    # Substring match
    matches = find_nodes_by_name(sample_kg, "init", exact=False)
    assert len(matches) >= 3  # __init__ methods in base, user, user_service


def test_find_nodes_by_type(sample_kg):
    """Verify retrieving nodes by NodeType."""
    classes = find_nodes_by_type(sample_kg, NodeType.CLASS)
    assert len(classes) == 3
    class_names = {c["name"] for c in classes}
    assert class_names == {"BaseModel", "User", "UserService"}

    files = find_nodes_by_type(sample_kg, NodeType.FILE)
    assert len(files) == 6


def test_repository_vs_synthetic_entities(sample_kg):
    """Verify clean separation between analyzer entities and synthetic placeholders."""
    repo_entities = get_repository_entities(sample_kg)
    assert len(repo_entities) == 19
    assert all(not e.get("is_synthetic", False) for e in repo_entities)

    synthetic_entities = get_synthetic_nodes(sample_kg)
    assert len(synthetic_entities) == 7
    assert all(e.get("is_synthetic", False) for e in synthetic_entities)
    assert all(e.get("type") == "UnresolvedReference" for e in synthetic_entities)


def test_relationships_queries(sample_kg):
    """Verify relationship querying by type, source, and target."""
    inherits_rels = get_relationships_by_type(sample_kg, RelationshipType.INHERITS)
    assert len(inherits_rels) == 1
    assert inherits_rels[0]["source"] == "class:models/user.py:User"
    assert inherits_rels[0]["target"] == "class:models/base.py:BaseModel"

    filtered = get_relationships(
        sample_kg,
        source_id="file:main.py",
        target_id="file:services/user_service.py",
    )
    assert len(filtered) == 2  # IMPORTS and DEPENDS_ON


def test_get_structural_context(sample_kg):
    """Verify higher-level structural context query."""
    ctx = get_structural_context(sample_kg, "func:main.py:main", depth=1)
    assert ctx["seed_ids"] == ["func:main.py:main"]
    assert any(n["id"] == "func:main.py:main" for n in ctx["nodes"])


def test_get_statistics(sample_kg):
    """Verify accurate calculation of graph statistics matching analyzer report."""
    stats = get_statistics(sample_kg)
    assert stats["total_nodes"] == 26
    assert stats["total_edges"] == 35
    assert stats["analyzer_entity_count"] == 19
    assert stats["synthetic_node_count"] == 7
    assert stats["primitive_relationship_count"] == 32
    assert stats["derived_relationship_count"] == 3
    assert stats["unresolved_calls_count"] == 7

    assert stats["entities_by_type"]["Class"] == 3
    assert stats["entities_by_type"]["Directory"] == 2
    assert stats["entities_by_type"]["File"] == 6
    assert stats["entities_by_type"]["Function"] == 1
    assert stats["entities_by_type"]["Method"] == 6
    assert stats["entities_by_type"]["Repository"] == 1
    assert stats["entities_by_type"]["UnresolvedReference"] == 7
