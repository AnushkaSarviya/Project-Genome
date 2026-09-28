"""Graph traversal operations for graph-aware context expansion and structural retrieval.

Provides BFS-based multi-hop traversal, neighborhood exploration, dependency and call
graph tracing, and path finding across the ProjectGenome Knowledge Graph.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from .graph import KnowledgeGraph, NodeNotFoundError, validate_relationship_type
from .schema import RelationshipType


def _normalize_rel_types(
    relationship_types: list[RelationshipType | str] | None,
) -> set[str] | None:
    """Normalize a list of relationship types into a set of uppercase string values."""
    if relationship_types is None:
        return None
    return {validate_relationship_type(rt).value for rt in relationship_types}


def get_neighbors(
    graph: KnowledgeGraph,
    node_id: str,
    direction: str = "both",
    relationship_types: list[RelationshipType | str] | None = None,
) -> list[str]:
    """Retrieve unique neighboring node IDs connected by specified relationship types.

    Args:
        graph: The KnowledgeGraph instance.
        node_id: Target node identifier.
        direction: "out" (outgoing edges), "in" (incoming edges), or "both".
        relationship_types: Optional filter for relationship types. If None, all types match.

    Returns:
        Deterministic sorted list of neighbor node IDs.

    Raises:
        NodeNotFoundError: If node_id does not exist in graph.
        ValueError: If direction is not 'out', 'in', or 'both'.
    """
    if not graph.has_node(node_id):
        raise NodeNotFoundError(f"Node '{node_id}' does not exist in graph.")

    allowed_types = _normalize_rel_types(relationship_types)
    g = graph.underlying_graph
    neighbors: set[str] = set()

    if direction in ("out", "both"):
        for _, target, data in g.out_edges(node_id, data=True):
            if allowed_types is None or data.get("type") in allowed_types:
                neighbors.add(target)

    if direction in ("in", "both"):
        for source, _, data in g.in_edges(node_id, data=True):
            if allowed_types is None or data.get("type") in allowed_types:
                neighbors.add(source)

    if direction not in ("out", "in", "both"):
        raise ValueError(f"Invalid direction '{direction}'. Must be 'out', 'in', or 'both'.")

    return sorted(neighbors)


def get_callers(graph: KnowledgeGraph, node_id: str) -> list[str]:
    """Retrieve all entity IDs that have an outgoing CALLS edge to node_id."""
    return get_neighbors(
        graph,
        node_id,
        direction="in",
        relationship_types=[RelationshipType.CALLS],
    )


def get_callees(
    graph: KnowledgeGraph,
    node_id: str,
    include_unresolved: bool = True,
) -> list[str]:
    """Retrieve all entity IDs called by node_id via outgoing CALLS edges.

    Args:
        graph: The KnowledgeGraph instance.
        node_id: Calling entity ID.
        include_unresolved: Whether to include synthetic unresolved reference nodes.
    """
    callees = get_neighbors(
        graph,
        node_id,
        direction="out",
        relationship_types=[RelationshipType.CALLS],
    )
    if not include_unresolved:
        return [
            cid for cid in callees
            if not (graph.get_node(cid) or {}).get("is_synthetic", False)
        ]
    return callees


def get_dependencies(
    graph: KnowledgeGraph,
    node_id: str,
    relationship_types: list[RelationshipType | str] | None = None,
) -> list[str]:
    """Retrieve entities that node_id depends on (outgoing dependencies).

    Defaults to DEPENDS_ON and IMPORTS relationships unless custom types are provided.
    """
    rel_types = relationship_types or [
        RelationshipType.DEPENDS_ON,
        RelationshipType.IMPORTS,
    ]
    return get_neighbors(graph, node_id, direction="out", relationship_types=rel_types)


def get_dependents(
    graph: KnowledgeGraph,
    node_id: str,
    relationship_types: list[RelationshipType | str] | None = None,
) -> list[str]:
    """Retrieve entities that depend on node_id (incoming dependencies).

    Defaults to DEPENDS_ON and IMPORTS relationships unless custom types are provided.
    """
    rel_types = relationship_types or [
        RelationshipType.DEPENDS_ON,
        RelationshipType.IMPORTS,
    ]
    return get_neighbors(graph, node_id, direction="in", relationship_types=rel_types)


def find_path(
    graph: KnowledgeGraph,
    source_id: str,
    target_id: str,
    relationship_types: list[RelationshipType | str] | None = None,
    max_depth: int | None = None,
) -> list[str] | None:
    """Find the shortest directed path from source_id to target_id.

    Traverses edges matching relationship_types up to max_depth.

    Returns:
        List of node IDs from source to target, or None if no path exists.
    """
    if not graph.has_node(source_id):
        raise NodeNotFoundError(f"Source node '{source_id}' does not exist in graph.")
    if not graph.has_node(target_id):
        raise NodeNotFoundError(f"Target node '{target_id}' does not exist in graph.")

    if source_id == target_id:
        return [source_id]

    allowed_types = _normalize_rel_types(relationship_types)
    g = graph.underlying_graph

    queue: deque[tuple[str, list[str]]] = deque([(source_id, [source_id])])
    visited: set[str] = {source_id}

    while queue:
        current, path = queue.popleft()
        if max_depth is not None and len(path) - 1 >= max_depth:
            continue

        for _, neighbor, data in g.out_edges(current, data=True):
            if allowed_types is not None and data.get("type") not in allowed_types:
                continue

            if neighbor == target_id:
                return path + [neighbor]

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def multi_hop_traversal(
    graph: KnowledgeGraph,
    seed_ids: list[str] | set[str] | str,
    max_hops: int = 2,
    relationship_types: list[RelationshipType | str] | None = None,
    direction: str = "both",
    include_unresolved: bool = True,
) -> dict[int, set[str]]:
    """Perform breadth-first multi-hop graph expansion from one or more seed nodes.

    Args:
        graph: The KnowledgeGraph instance.
        seed_ids: Starting node ID or collection of node IDs.
        max_hops: Maximum traversal depth (hops >= 0).
        relationship_types: Optional filter for edge relationship types.
        direction: "out", "in", or "both".
        include_unresolved: Whether to include synthetic unresolved reference nodes.

    Returns:
        Dict mapping hop distance (int) to set of node IDs discovered at that hop.
    """
    if isinstance(seed_ids, str):
        seeds = [seed_ids]
    else:
        seeds = list(seed_ids)

    for sid in seeds:
        if not graph.has_node(sid):
            raise NodeNotFoundError(f"Seed node '{sid}' does not exist in graph.")

    allowed_types = _normalize_rel_types(relationship_types)
    g = graph.underlying_graph

    hops_map: dict[int, set[str]] = {0: set(seeds)}
    visited: set[str] = set(seeds)
    current_level = set(seeds)

    for hop in range(1, max_hops + 1):
        next_level: set[str] = set()
        for node in current_level:
            candidates: set[str] = set()

            if direction in ("out", "both"):
                for _, target, data in g.out_edges(node, data=True):
                    if allowed_types is None or data.get("type") in allowed_types:
                        candidates.add(target)

            if direction in ("in", "both"):
                for source, _, data in g.in_edges(node, data=True):
                    if allowed_types is None or data.get("type") in allowed_types:
                        candidates.add(source)

            for cand in candidates:
                if cand not in visited:
                    if not include_unresolved:
                        node_data = graph.get_node(cand)
                        if node_data and node_data.get("is_synthetic", False):
                            continue
                    visited.add(cand)
                    next_level.add(cand)

        hops_map[hop] = next_level
        current_level = next_level
        if not current_level:
            break

    return hops_map


def expand_context(
    graph: KnowledgeGraph,
    seed_ids: list[str] | set[str] | str,
    max_hops: int = 2,
    relationship_types: list[RelationshipType | str] | None = None,
    direction: str = "both",
    include_unresolved: bool = False,
) -> dict[str, Any]:
    """Expand structural context around starting seeds for graph-aware retrieval.

    Collects the induced subgraph around seeds up to max_hops, returning all traversed
    nodes, interconnecting edges, and minimum hop distance.

    Args:
        graph: The KnowledgeGraph instance.
        seed_ids: Starting entity IDs.
        max_hops: Maximum expansion distance.
        relationship_types: Allowed relationship types (e.g. CALLS, IMPORTS, DEPENDS_ON).
        direction: "out", "in", or "both".
        include_unresolved: Whether to include synthetic unresolved reference nodes.

    Returns:
        Dict with keys:
        - "seed_ids": list of starting IDs
        - "max_hops": requested maximum depth
        - "nodes": list of node data dicts for all traversed entities
        - "edges": list of edge data dicts between traversed entities
        - "hop_distances": dict mapping entity ID to shortest hop distance from seeds
    """
    hops = multi_hop_traversal(
        graph=graph,
        seed_ids=seed_ids,
        max_hops=max_hops,
        relationship_types=relationship_types,
        direction=direction,
        include_unresolved=include_unresolved,
    )

    all_node_ids: set[str] = set()
    hop_distances: dict[str, int] = {}
    for distance, nodes in hops.items():
        for nid in nodes:
            all_node_ids.add(nid)
            if nid not in hop_distances:
                hop_distances[nid] = distance

    nodes_list = [graph.get_node(nid) for nid in sorted(all_node_ids)]

    allowed_types = _normalize_rel_types(relationship_types)
    g = graph.underlying_graph
    subgraph_edges: list[dict[str, Any]] = []

    for u, v, data in g.edges(all_node_ids, data=True):
        if v in all_node_ids:
            if allowed_types is None or data.get("type") in allowed_types:
                subgraph_edges.append(dict(data))

    seed_list = [seed_ids] if isinstance(seed_ids, str) else list(seed_ids)
    return {
        "seed_ids": seed_list,
        "max_hops": max_hops,
        "nodes": nodes_list,
        "edges": subgraph_edges,
        "hop_distances": hop_distances,
    }
