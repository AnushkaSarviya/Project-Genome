"""End-to-End integration test for ProjectGenome Software Knowledge Graph (Milestone 9).

Validates complete workflow:
Analyzer JSON -> KnowledgeGraph -> Traversal -> Queries -> Validation -> JSON/GraphML Export & Reload.
"""

from pathlib import Path
import pytest

from src.knowledge_graph import (
    KnowledgeGraphBuilder,
    NodeType,
    RelationshipType,
    expand_context,
    export_graphml,
    export_json,
    find_nodes_by_type,
    find_path,
    get_callees,
    get_callers,
    get_dependencies,
    get_statistics,
    import_graphml,
    import_json,
    validate_or_raise,
)


def test_full_pipeline_end_to_end(tmp_path):
    """Execute complete end-to-end integration pipeline using Nyasa's sample fixture."""
    fixture_path = Path("data/sample/sample_analysis.json")
    assert fixture_path.exists(), "Sample analyzer fixture must exist"

    # Step 1 & 2: Ingest analyzer JSON into KnowledgeGraph
    builder = KnowledgeGraphBuilder()
    kg = builder.build(fixture_path)

    # Step 3: Verify analyzer entities
    all_nodes = kg.get_all_nodes()
    analyzer_entities = [n for n, d in all_nodes.items() if not d.get("is_synthetic", False)]
    synthetic_entities = [n for n, d in all_nodes.items() if d.get("is_synthetic", False)]

    assert len(analyzer_entities) == 19
    assert len(synthetic_entities) == 7
    assert kg.number_of_nodes() == 26

    # Step 4: Verify relationships
    assert kg.number_of_edges() == 35

    # Step 5: Verify DEPENDS_ON derived relationship metadata
    dep_edges = [
        r for r in kg.get_all_relationships()
        if r.get("type") == RelationshipType.DEPENDS_ON.value
    ]
    assert len(dep_edges) == 3
    for dep in dep_edges:
        assert dep["properties"]["derived"] is True
        assert isinstance(dep["properties"]["reasons"], list)
        assert dep["properties"]["weight"] >= 1

    # Step 6: Verify unresolved CALLS are preserved with synthetic placeholder targets
    unresolved_calls = [
        r for r in kg.get_all_relationships()
        if r.get("type") == RelationshipType.CALLS.value
        and r.get("target", "").startswith("unresolved:")
    ]
    assert len(unresolved_calls) == 7
    for uc in unresolved_calls:
        target_node = kg.get_node(uc["target"])
        assert target_node is not None
        assert target_node["type"] == NodeType.UNRESOLVED_REFERENCE.value
        assert target_node["is_synthetic"] is True
        assert target_node["resolved"] is False

    # Step 7: Verify NO Module entities were created
    module_nodes = [n for n, d in all_nodes.items() if d.get("type") == "Module"]
    assert len(module_nodes) == 0

    # Step 8: Verify NO DEFINED_IN relationships were required
    defined_in_edges = [r for r in kg.get_all_relationships() if r.get("type") == "DEFINED_IN"]
    assert len(defined_in_edges) == 0

    # Step 9: Run Traversal operations
    # Caller/Callee
    main_callees = get_callees(kg, "func:main.py:main", include_unresolved=False)
    assert "class:services/user_service.py:UserService" in main_callees

    # Path finding
    path = find_path(
        kg,
        source_id="repo:sample_repo",
        target_id="method:services/user_service.py:UserService.create_user",
        relationship_types=[RelationshipType.CONTAINS],
    )
    assert path is not None
    assert path[0] == "repo:sample_repo"
    assert path[-1] == "method:services/user_service.py:UserService.create_user"

    # Context Expansion for Retrieval teammate
    context = expand_context(
        kg,
        seed_ids="method:services/user_service.py:UserService.create_user",
        max_hops=2,
        relationship_types=[RelationshipType.CALLS, RelationshipType.CONTAINS],
    )
    assert len(context["nodes"]) > 1
    assert len(context["edges"]) > 0

    # Step 10: Run Queries & Statistics
    classes = find_nodes_by_type(kg, NodeType.CLASS)
    assert len(classes) == 3

    stats = get_statistics(kg)
    assert stats["analyzer_entity_count"] == 19
    assert stats["synthetic_node_count"] == 7
    assert stats["primitive_relationship_count"] == 32
    assert stats["derived_relationship_count"] == 3
    assert stats["unresolved_calls_count"] == 7

    # Step 11: Run Validation
    validate_or_raise(kg)

    # Step 12: Export JSON & verify reload
    json_path = tmp_path / "test_out.json"
    export_json(kg, file_path=json_path)
    assert json_path.exists()
    reloaded_json_kg = import_json(json_path)
    assert reloaded_json_kg.number_of_nodes() == 26
    assert reloaded_json_kg.number_of_edges() == 35

    # Step 13: Export GraphML & verify reload
    graphml_path = tmp_path / "test_out.graphml"
    export_graphml(kg, file_path=graphml_path)
    assert graphml_path.exists()
    reloaded_graphml_kg = import_graphml(graphml_path)
    assert reloaded_graphml_kg.number_of_nodes() == 26
    assert reloaded_graphml_kg.number_of_edges() == 35
