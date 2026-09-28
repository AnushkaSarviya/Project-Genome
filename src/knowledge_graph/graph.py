"""Core in-memory NetworkX MultiDiGraph wrapper for ProjectGenome Software Knowledge Graph.

Represents repository entities as nodes and structural interactions as directed, typed edges.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from .schema import NodeType, RelationshipType


class KnowledgeGraphError(Exception):
    """Base exception for Knowledge Graph operations."""


class NodeNotFoundError(KnowledgeGraphError):
    """Raised when an operation references a node that does not exist in the graph."""


class NodeAlreadyExistsError(KnowledgeGraphError):
    """Raised when attempting to add a node that already exists or conflicts."""


class RelationshipAlreadyExistsError(KnowledgeGraphError):
    """Raised when attempting to add a relationship that already exists or conflicts."""


class InvalidNodeTypeError(KnowledgeGraphError, ValueError):
    """Raised when an unsupported or malformed node type is provided."""


class InvalidRelationshipTypeError(KnowledgeGraphError, ValueError):
    """Raised when an unsupported or malformed relationship type is provided."""


def validate_node_type(node_type: NodeType | str) -> NodeType:
    """Validate and normalize a node type to a NodeType enum member.

    Args:
        node_type: NodeType enum member or string representation.

    Returns:
        The matching NodeType enum member.

    Raises:
        InvalidNodeTypeError: If node_type does not correspond to a valid NodeType.
    """
    if isinstance(node_type, NodeType):
        return node_type

    if isinstance(node_type, str):
        try:
            return NodeType(node_type)
        except ValueError:
            for member in NodeType:
                if member.value.lower() == node_type.lower() or member.name.lower() == node_type.lower():
                    return member

    valid_types = [t.value for t in NodeType]
    raise InvalidNodeTypeError(
        f"Invalid node type: '{node_type}'. Supported types: {valid_types}"
    )


def validate_relationship_type(rel_type: RelationshipType | str) -> RelationshipType:
    """Validate and normalize a relationship type to a RelationshipType enum member.

    Args:
        rel_type: RelationshipType enum member or string representation.

    Returns:
        The matching RelationshipType enum member.

    Raises:
        InvalidRelationshipTypeError: If rel_type does not correspond to a valid RelationshipType.
    """
    if isinstance(rel_type, RelationshipType):
        return rel_type

    if isinstance(rel_type, str):
        try:
            return RelationshipType(rel_type)
        except ValueError:
            for member in RelationshipType:
                if member.value.upper() == rel_type.upper() or member.name.upper() == rel_type.upper():
                    return member

    valid_types = [t.value for t in RelationshipType]
    raise InvalidRelationshipTypeError(
        f"Invalid relationship type: '{rel_type}'. Supported types: {valid_types}"
    )


class KnowledgeGraph:
    """NetworkX MultiDiGraph-backed Software Knowledge Graph.

    Maintains repository structural entities and relationships deterministically,
    preserving metadata and relationship types without silent data loss or overwrites.
    """

    def __init__(self, metadata: dict[str, Any] | None = None) -> None:
        """Initialize an empty KnowledgeGraph, optionally with repository metadata."""
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.metadata: dict[str, Any] = dict(metadata or {})

    @property
    def underlying_graph(self) -> nx.MultiDiGraph:
        """Direct access to the underlying NetworkX MultiDiGraph instance."""
        return self._graph

    def number_of_nodes(self) -> int:
        """Return the total number of nodes in the graph."""
        return self._graph.number_of_nodes()

    def number_of_edges(self) -> int:
        """Return the total number of edges (relationships) in the graph."""
        return self._graph.number_of_edges()

    def has_node(self, node_id: str) -> bool:
        """Check whether a node with the given ID exists in the graph."""
        if not isinstance(node_id, str):
            return False
        return self._graph.has_node(node_id)

    def add_node(
        self,
        node_id: str,
        node_type: NodeType | str,
        name: str,
        raise_if_exists: bool = True,
        **metadata: Any,
    ) -> None:
        """Add an entity node to the Knowledge Graph.

        Args:
            node_id: Stable, unique identifier for the node.
            node_type: Category of the entity (NodeType or valid string).
            name: Human-readable entity name.
            raise_if_exists: If True, raise NodeAlreadyExistsError when adding an existing node.
            **metadata: Additional source code metadata (file_path, line_start, etc.).

        Raises:
            ValueError: If node_id or name is empty or invalid.
            InvalidNodeTypeError: If node_type is not a valid NodeType.
            NodeAlreadyExistsError: If the node already exists and raise_if_exists is True,
                                    or if incoming attributes conflict with existing ones.
        """
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be a non-empty string.")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string.")

        validated_type = validate_node_type(node_type)

        incoming_attributes = {
            "id": node_id,
            "type": validated_type.value,
            "name": name,
            **metadata,
        }

        if self._graph.has_node(node_id):
            existing_attributes = self._graph.nodes[node_id]
            conflicts = {
                k: {"existing": existing_attributes[k], "new": incoming_attributes[k]}
                for k in incoming_attributes
                if k in existing_attributes and existing_attributes[k] != incoming_attributes[k]
            }

            if conflicts:
                raise NodeAlreadyExistsError(
                    f"Node '{node_id}' already exists with conflicting attributes: {conflicts}"
                )

            if raise_if_exists:
                raise NodeAlreadyExistsError(
                    f"Node '{node_id}' already exists in the graph."
                )

            # Idempotent re-addition: non-conflicting metadata can be backfilled
            self._graph.nodes[node_id].update(incoming_attributes)
            return

        self._graph.add_node(node_id, **incoming_attributes)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Retrieve attributes for a node by its ID.

        Returns a shallow copy of the node's attributes dict, or None if not found.
        """
        if not self._graph.has_node(node_id):
            return None
        return dict(self._graph.nodes[node_id])

    def get_all_nodes(self) -> dict[str, dict[str, Any]]:
        """Return a mapping of all node IDs to their attributes."""
        return {node_id: dict(data) for node_id, data in self._graph.nodes(data=True)}

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType | str,
        key: str | None = None,
        raise_if_exists: bool = False,
        **metadata: Any,
    ) -> None:
        """Add a directed, typed relationship edge between two existing nodes.

        Supports multiple edges between the same source and target (e.g. CALLS and DEPENDS_ON).

        Args:
            source_id: Node ID of the relationship source.
            target_id: Node ID of the relationship target.
            rel_type: Relationship type (RelationshipType or valid string).
            key: Optional distinct edge key. Defaults to rel_type.value.
            raise_if_exists: If True, raise RelationshipAlreadyExistsError if edge exists.
            **metadata: Additional relationship metadata.

        Raises:
            NodeNotFoundError: If source_id or target_id does not exist in the graph.
            InvalidRelationshipTypeError: If rel_type is not a valid RelationshipType.
            RelationshipAlreadyExistsError: If relationship exists with conflicts or raise_if_exists is True.
        """
        if not self._graph.has_node(source_id):
            raise NodeNotFoundError(
                f"Source node '{source_id}' does not exist in the graph."
            )

        if not self._graph.has_node(target_id):
            raise NodeNotFoundError(
                f"Target node '{target_id}' does not exist in the graph."
            )

        validated_type = validate_relationship_type(rel_type)
        edge_key = key if key is not None else (metadata.get("id") or validated_type.value)

        incoming_attributes = {
            "source": source_id,
            "target": target_id,
            "type": validated_type.value,
            **metadata,
        }

        if self._graph.has_edge(source_id, target_id, key=edge_key):
            existing_attributes = self._graph[source_id][target_id][edge_key]
            conflicts = {
                k: {"existing": existing_attributes[k], "new": incoming_attributes[k]}
                for k in incoming_attributes
                if k in existing_attributes and existing_attributes[k] != incoming_attributes[k]
            }

            if conflicts:
                raise RelationshipAlreadyExistsError(
                    f"Relationship ({source_id} -> {target_id}, key='{edge_key}') "
                    f"already exists with conflicting attributes: {conflicts}"
                )

            if raise_if_exists:
                raise RelationshipAlreadyExistsError(
                    f"Relationship ({source_id} -> {target_id}, key='{edge_key}') "
                    f"already exists in the graph."
                )

            self._graph[source_id][target_id][edge_key].update(incoming_attributes)
            return

        self._graph.add_edge(source_id, target_id, key=edge_key, **incoming_attributes)

    def has_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType | str | None = None,
    ) -> bool:
        """Check whether a relationship exists between source and target, optionally matching rel_type."""
        if not self._graph.has_edge(source_id, target_id):
            return False

        if rel_type is None:
            return True

        validated_type = validate_relationship_type(rel_type)
        edge_dict = self._graph[source_id][target_id]
        return any(data.get("type") == validated_type.value for data in edge_dict.values())

    def get_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType | str,
        key: str | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve relationship attributes for an edge matching rel_type (and optional key)."""
        if not self._graph.has_edge(source_id, target_id):
            return None

        edge_dict = self._graph[source_id][target_id]
        if key is not None:
            if key in edge_dict:
                return dict(edge_dict[key])
            return None

        validated_type = validate_relationship_type(rel_type)
        for data in edge_dict.values():
            if data.get("type") == validated_type.value:
                return dict(data)
        return None

    def get_relationships(self, source_id: str, target_id: str) -> list[dict[str, Any]]:
        """Retrieve all relationships between source and target."""
        if not self._graph.has_edge(source_id, target_id):
            return []
        return [dict(data) for data in self._graph[source_id][target_id].values()]

    def get_all_relationships(self) -> list[dict[str, Any]]:
        """Retrieve a list of all relationships across the entire graph."""
        return [dict(data) for _, _, data in self._graph.edges(data=True)]

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._graph.clear()
