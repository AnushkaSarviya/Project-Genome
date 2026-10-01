"""Higher-level graph queries and statistics for ProjectGenome Knowledge Graph.

Provides high-level search, filtering, contextual retrieval, and graph statistics
for downstream semantic retrieval and evaluation pipelines.
"""

from __future__ import annotations

from typing import Any

from .graph import KnowledgeGraph, validate_node_type, validate_relationship_type
from .schema import (
    ANALYZER_ENTITY_TYPES,
    DERIVED_RELATIONSHIP_TYPES,
    PRIMITIVE_RELATIONSHIP_TYPES,
    NodeType,
    RelationshipType,
)
from .traversal import expand_context


def get_node(graph: KnowledgeGraph, node_id: str) -> dict[str, Any] | None:
    """Retrieve attributes for a node by its ID."""
    return graph.get_node(node_id)


def find_nodes_by_name(
    graph: KnowledgeGraph,
    name: str,
    node_type: NodeType | str | None = None,
    exact: bool = True,
) -> list[dict[str, Any]]:
    """Search for nodes by entity name.

    Args:
        graph: The KnowledgeGraph instance.
        name: Name to search for.
        node_type: Optional NodeType filter.
        exact: If True, requires exact match; if False, case-insensitive substring match.

    Returns:
        List of matching node attribute dictionaries.
    """
    target_type = validate_node_type(node_type).value if node_type is not None else None
    results: list[dict[str, Any]] = []

    for _, data in graph.get_all_nodes().items():
        if target_type is not None and data.get("type") != target_type:
            continue

        node_name = data.get("name", "")
        if exact:
            if node_name == name:
                results.append(data)
        else:
            if name.lower() in node_name.lower():
                results.append(data)

    return sorted(results, key=lambda n: n.get("id", ""))


def find_nodes_by_type(
    graph: KnowledgeGraph,
    node_type: NodeType | str,
) -> list[dict[str, Any]]:
    """Retrieve all nodes of a specific NodeType."""
    validated = validate_node_type(node_type).value
    return sorted(
        [data for data in graph.get_all_nodes().values() if data.get("type") == validated],
        key=lambda n: n.get("id", ""),
    )


def get_repository_entities(
    graph: KnowledgeGraph,
    include_synthetic: bool = False,
) -> list[dict[str, Any]]:
    """Retrieve all analyzer-emitted repository entities (excluding synthetic placeholders)."""
    return sorted(
        [
            data for data in graph.get_all_nodes().values()
            if include_synthetic or not data.get("is_synthetic", False)
        ],
        key=lambda n: n.get("id", ""),
    )


def get_synthetic_nodes(graph: KnowledgeGraph) -> list[dict[str, Any]]:
    """Retrieve all synthetic KG-generated placeholder nodes (e.g. UnresolvedReference)."""
    return sorted(
        [data for data in graph.get_all_nodes().values() if data.get("is_synthetic", False)],
        key=lambda n: n.get("id", ""),
    )


def get_relationships_by_type(
    graph: KnowledgeGraph,
    rel_type: RelationshipType | str,
) -> list[dict[str, Any]]:
    """Retrieve all relationships matching the specified relationship type."""
    validated = validate_relationship_type(rel_type).value
    return [
        rel for rel in graph.get_all_relationships()
        if rel.get("type") == validated
    ]


def get_relationships(
    graph: KnowledgeGraph,
    source_id: str | None = None,
    target_id: str | None = None,
    rel_type: RelationshipType | str | None = None,
) -> list[dict[str, Any]]:
    """Filter relationships by source, target, and/or relationship type."""
    validated_type = validate_relationship_type(rel_type).value if rel_type is not None else None
    results: list[dict[str, Any]] = []

    for rel in graph.get_all_relationships():
        if source_id is not None and rel.get("source") != source_id:
            continue
        if target_id is not None and rel.get("target") != target_id:
            continue
        if validated_type is not None and rel.get("type") != validated_type:
            continue
        results.append(rel)

    return results


def get_structural_context(
    graph: KnowledgeGraph,
    entity_id: str,
    depth: int = 1,
    relationship_types: list[RelationshipType | str] | None = None,
    include_unresolved: bool = False,
) -> dict[str, Any]:
    """Retrieve the structural context subgraph around an entity up to depth hops."""
    return expand_context(
        graph=graph,
        seed_ids=entity_id,
        max_hops=depth,
        relationship_types=relationship_types,
        direction="both",
        include_unresolved=include_unresolved,
    )


def get_statistics(graph: KnowledgeGraph) -> dict[str, Any]:
    """Compute comprehensive, deterministic statistics of the KnowledgeGraph.

    Returns:
        Dict containing node counts, edge counts, categorical distributions,
        primitive vs derived relationships, and unresolved call counts.
    """
    all_nodes = graph.get_all_nodes()
    all_edges = graph.get_all_relationships()

    analyzer_entity_count = sum(1 for d in all_nodes.values() if not d.get("is_synthetic", False))
    synthetic_node_count = sum(1 for d in all_nodes.values() if d.get("is_synthetic", False))

    entities_by_type: dict[str, int] = {}
    for d in all_nodes.values():
        t = d.get("type", "Unknown")
        entities_by_type[t] = entities_by_type.get(t, 0) + 1

    relationships_by_type: dict[str, int] = {}
    for r in all_edges:
        t = r.get("type", "Unknown")
        relationships_by_type[t] = relationships_by_type.get(t, 0) + 1

    primitive_count = sum(
        1 for r in all_edges
        if r.get("type") in [pt.value for pt in PRIMITIVE_RELATIONSHIP_TYPES]
        and not r.get("is_derived", False)
    )
    derived_count = sum(
        1 for r in all_edges
        if r.get("type") in [dt.value for dt in DERIVED_RELATIONSHIP_TYPES]
        or r.get("is_derived", False)
    )
    unresolved_calls_count = sum(
        1 for r in all_edges
        if r.get("type") == RelationshipType.CALLS.value
        and (r.get("target", "").startswith("unresolved:") or r.get("is_unresolved", False))
    )

    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "analyzer_entity_count": analyzer_entity_count,
        "synthetic_node_count": synthetic_node_count,
        "entities_by_type": dict(sorted(entities_by_type.items())),
        "relationships_by_type": dict(sorted(relationships_by_type.items())),
        "primitive_relationship_count": primitive_count,
        "derived_relationship_count": derived_count,
        "unresolved_calls_count": unresolved_calls_count,
    }
