"""Unit tests for the core KnowledgeGraph module (Milestone 1)."""

import pytest

from src.knowledge_graph.graph import (
    InvalidNodeTypeError,
    InvalidRelationshipTypeError,
    KnowledgeGraph,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    RelationshipAlreadyExistsError,
)
from src.knowledge_graph.schema import NodeType, RelationshipType


def test_graph_initialization():
    """Verify that a newly initialized KnowledgeGraph is empty and uses MultiDiGraph."""
    kg = KnowledgeGraph()
    assert kg.number_of_nodes() == 0
    assert kg.number_of_edges() == 0
    assert kg.underlying_graph.is_directed()
    assert kg.underlying_graph.is_multigraph()


def test_add_and_get_node_with_metadata():
    """Verify adding nodes preserves schema type, name, and arbitrary source metadata."""
    kg = KnowledgeGraph()
    kg.add_node(
        node_id="class_auth_service",
        node_type=NodeType.CLASS,
        name="AuthService",
        file_path="src/auth.py",
        line_start=10,
        line_end=50,
        docstring="Handles user authentication.",
    )

    assert kg.has_node("class_auth_service")
    node_data = kg.get_node("class_auth_service")
    assert node_data is not None
    assert node_data["id"] == "class_auth_service"
    assert node_data["type"] == "Class"
    assert node_data["name"] == "AuthService"
    assert node_data["file_path"] == "src/auth.py"
    assert node_data["line_start"] == 10
    assert node_data["line_end"] == 50
    assert node_data["docstring"] == "Handles user authentication."


def test_add_node_string_type_normalization():
    """Verify that string representations of NodeType are normalized properly."""
    kg = KnowledgeGraph()
    kg.add_node("fn_login", "Function", "login")
    node = kg.get_node("fn_login")
    assert node is not None
    assert node["type"] == NodeType.FUNCTION.value


def test_add_node_invalid_type():
    """Verify that unsupported node types raise InvalidNodeTypeError."""
    kg = KnowledgeGraph()
    with pytest.raises(InvalidNodeTypeError):
        kg.add_node("var_x", "Variable", "x")


def test_add_node_invalid_id_or_name():
    """Verify that blank or non-string node_id and name raise ValueError."""
    kg = KnowledgeGraph()
    with pytest.raises(ValueError):
        kg.add_node("", NodeType.FILE, "file.py")

    with pytest.raises(ValueError):
        kg.add_node("node_1", NodeType.FILE, "")


def test_add_duplicate_node_handling():
    """Verify duplicate node addition raises NodeAlreadyExistsError on conflict or by default."""
    kg = KnowledgeGraph()
    kg.add_node("mod_core", NodeType.MODULE, "core", file_path="core.py")

    # Re-adding exact node raises when raise_if_exists is True (default)
    with pytest.raises(NodeAlreadyExistsError):
        kg.add_node("mod_core", NodeType.MODULE, "core", file_path="core.py")

    # Re-adding conflicting node always raises even if raise_if_exists=False
    with pytest.raises(NodeAlreadyExistsError):
        kg.add_node(
            "mod_core",
            NodeType.CLASS,  # Conflicting type
            "core",
            raise_if_exists=False,
        )

    # Re-adding non-conflicting node with raise_if_exists=False succeeds idempotently
    kg.add_node("mod_core", NodeType.MODULE, "core", raise_if_exists=False, file_path="core.py")
    assert kg.number_of_nodes() == 1


def test_get_nonexistent_node():
    """Verify getting a nonexistent node returns None."""
    kg = KnowledgeGraph()
    assert kg.get_node("nonexistent") is None
    assert not kg.has_node("nonexistent")


def test_add_and_get_relationship():
    """Verify adding directed, typed edges with metadata between existing nodes."""
    kg = KnowledgeGraph()
    kg.add_node("class_auth", NodeType.CLASS, "Auth")
    kg.add_node("class_base", NodeType.CLASS, "Base")

    kg.add_relationship(
        source_id="class_auth",
        target_id="class_base",
        rel_type=RelationshipType.INHERITS,
        line=12,
    )

    assert kg.number_of_edges() == 1
    assert kg.has_relationship("class_auth", "class_base")
    assert kg.has_relationship("class_auth", "class_base", RelationshipType.INHERITS)
    assert not kg.has_relationship("class_base", "class_auth")  # Directed

    rel = kg.get_relationship("class_auth", "class_base", RelationshipType.INHERITS)
    assert rel is not None
    assert rel["source"] == "class_auth"
    assert rel["target"] == "class_base"
    assert rel["type"] == "INHERITS"
    assert rel["line"] == 12


def test_multidigraph_multiple_relationships_between_same_nodes():
    """Verify that multiple distinct relationship types can exist between the same pair of nodes."""
    kg = KnowledgeGraph()
    kg.add_node("fn_a", NodeType.FUNCTION, "func_a")
    kg.add_node("fn_b", NodeType.FUNCTION, "func_b")

    # Two distinct relationship types between fn_a and fn_b
    kg.add_relationship("fn_a", "fn_b", RelationshipType.CALLS)
    kg.add_relationship("fn_a", "fn_b", RelationshipType.DEPENDS_ON)

    assert kg.number_of_edges() == 2
    assert kg.has_relationship("fn_a", "fn_b", RelationshipType.CALLS)
    assert kg.has_relationship("fn_a", "fn_b", RelationshipType.DEPENDS_ON)

    rels = kg.get_relationships("fn_a", "fn_b")
    assert len(rels) == 2
    types = {r["type"] for r in rels}
    assert types == {"CALLS", "DEPENDS_ON"}


def test_add_relationship_missing_nodes():
    """Verify adding relationship referencing nonexistent source or target raises NodeNotFoundError."""
    kg = KnowledgeGraph()
    kg.add_node("node_a", NodeType.MODULE, "ModuleA")

    # Missing target
    with pytest.raises(NodeNotFoundError):
        kg.add_relationship("node_a", "missing_node", RelationshipType.DEPENDS_ON)

    # Missing source
    with pytest.raises(NodeNotFoundError):
        kg.add_relationship("missing_node", "node_a", RelationshipType.DEPENDS_ON)


def test_add_relationship_invalid_type():
    """Verify adding relationship with invalid relationship type raises InvalidRelationshipTypeError."""
    kg = KnowledgeGraph()
    kg.add_node("node_a", NodeType.MODULE, "ModuleA")
    kg.add_node("node_b", NodeType.MODULE, "ModuleB")

    with pytest.raises(InvalidRelationshipTypeError):
        kg.add_relationship("node_a", "node_b", "BELONGS_TO")


def test_relationship_duplicate_conflict_handling():
    """Verify conflicting relationship attributes raise RelationshipAlreadyExistsError."""
    kg = KnowledgeGraph()
    kg.add_node("node_a", NodeType.FILE, "a.py")
    kg.add_node("node_b", NodeType.FILE, "b.py")

    kg.add_relationship("node_a", "node_b", RelationshipType.IMPORTS, line=10)

    # Conflicting metadata raises
    with pytest.raises(RelationshipAlreadyExistsError):
        kg.add_relationship("node_a", "node_b", RelationshipType.IMPORTS, line=20)


def test_get_all_nodes_and_relationships():
    """Verify bulk retrieval of all nodes and relationships."""
    kg = KnowledgeGraph()
    kg.add_node("repo_1", NodeType.REPOSITORY, "ProjectGenome")
    kg.add_node("dir_1", NodeType.DIRECTORY, "src")
    kg.add_relationship("repo_1", "dir_1", RelationshipType.CONTAINS)

    all_nodes = kg.get_all_nodes()
    assert len(all_nodes) == 2
    assert "repo_1" in all_nodes
    assert "dir_1" in all_nodes

    all_rels = kg.get_all_relationships()
    assert len(all_rels) == 1
    assert all_rels[0]["source"] == "repo_1"
    assert all_rels[0]["target"] == "dir_1"
    assert all_rels[0]["type"] == "CONTAINS"
