"""Unit tests for knowledge_graph.traversal (Milestone 4)."""

from pathlib import Path
import pytest

from src.knowledge_graph.builder import build_from_analysis
from src.knowledge_graph.graph import NodeNotFoundError
from src.knowledge_graph.schema import RelationshipType
from src.knowledge_graph.traversal import (
    expand_context,
    find_path,
    get_callees,
    get_callers,
    get_dependencies,
    get_dependents,
    get_neighbors,
    multi_hop_traversal,
)


@pytest.fixture
def sample_kg():
    """Load sample KnowledgeGraph fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    return build_from_analysis(fixture_path)


def test_get_neighbors(sample_kg):
    """Verify neighbor extraction with direction and type filtering."""
    # file:main.py contains func:main.py:main
    out_neighbors = get_neighbors(
        sample_kg,
        "file:main.py",
        direction="out",
        relationship_types=[RelationshipType.CONTAINS],
    )
    assert "func:main.py:main" in out_neighbors

    # dir:models contains files
    contained_files = get_neighbors(
        sample_kg,
        "dir:models",
        direction="out",
        relationship_types=[RelationshipType.CONTAINS],
    )
    assert "file:models/user.py" in contained_files
    assert "file:models/base.py" in contained_files


def test_get_callers_and_callees(sample_kg):
    """Verify call graph queries with and without synthetic unresolved references."""
    main_func = "func:main.py:main"

    # Callees with unresolved references included
    all_callees = get_callees(sample_kg, main_func, include_unresolved=True)
    assert "class:services/user_service.py:UserService" in all_callees
    assert "unresolved:print" in all_callees

    # Callees excluding unresolved references
    resolved_callees = get_callees(sample_kg, main_func, include_unresolved=False)
    assert "class:services/user_service.py:UserService" in resolved_callees
    assert "unresolved:print" not in resolved_callees

    # Callers of main function
    callers = get_callers(sample_kg, main_func)
    assert "file:main.py" in callers


def test_get_dependencies_and_dependents(sample_kg):
    """Verify dependency tracing along DEPENDS_ON and IMPORTS."""
    main_file = "file:main.py"
    deps = get_dependencies(sample_kg, main_file)
    assert "file:services/user_service.py" in deps

    service_file = "file:services/user_service.py"
    dependents = get_dependents(sample_kg, service_file)
    assert main_file in dependents


def test_find_path(sample_kg):
    """Verify shortest directed path detection."""
    # Path from repo to method via containment
    path = find_path(
        sample_kg,
        source_id="repo:sample_repo",
        target_id="method:models/user.py:User.__init__",
        relationship_types=[RelationshipType.CONTAINS],
    )
    assert path is not None
    assert path == [
        "repo:sample_repo",
        "dir:models",
        "file:models/user.py",
        "class:models/user.py:User",
        "method:models/user.py:User.__init__",
    ]

    # Nonexistent path returns None
    no_path = find_path(
        sample_kg,
        source_id="method:models/user.py:User.__init__",
        target_id="repo:sample_repo",
        relationship_types=[RelationshipType.CONTAINS],
    )
    assert no_path is None


def test_multi_hop_traversal(sample_kg):
    """Verify breadth-first expansion across specified hop depths."""
    seed = "class:models/user.py:User"
    hops = multi_hop_traversal(sample_kg, seed, max_hops=2, include_unresolved=False)

    assert 0 in hops
    assert seed in hops[0]
    assert 1 in hops
    # Hop 1 should include inherited base class and containing file
    assert "class:models/base.py:BaseModel" in hops[1] or "file:models/user.py" in hops[1]


def test_expand_context(sample_kg):
    """Verify structural context expansion returns sub-graph nodes, edges, and distances."""
    seed = "method:services/user_service.py:UserService.create_user"
    context = expand_context(
        sample_kg,
        seed_ids=seed,
        max_hops=2,
        relationship_types=[
            RelationshipType.CALLS,
            RelationshipType.CONTAINS,
            RelationshipType.DEPENDS_ON,
        ],
        direction="both",
        include_unresolved=False,
    )

    assert context["seed_ids"] == [seed]
    assert context["max_hops"] == 2
    node_ids = {n["id"] for n in context["nodes"]}
    assert seed in node_ids
    # create_user calls User class, which should be in the expanded context
    assert "class:models/user.py:User" in node_ids

    # Hop distances
    assert context["hop_distances"][seed] == 0
    assert context["hop_distances"]["class:models/user.py:User"] == 1

    # Edges in subgraph
    edge_types = {e["type"] for e in context["edges"]}
    assert "CALLS" in edge_types or "CONTAINS" in edge_types
