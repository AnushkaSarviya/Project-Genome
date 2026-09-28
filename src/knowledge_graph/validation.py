"""Integrity validation for ProjectGenome Software Knowledge Graph.

Validates node and relationship schemas, reference consistency, and distinguishes
canonical analyzer entities from synthetic unresolved reference placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import KnowledgeGraph, KnowledgeGraphError
from .schema import (
    ANALYZER_ENTITY_TYPES,
    DERIVED_RELATIONSHIP_TYPES,
    PRIMITIVE_RELATIONSHIP_TYPES,
    NodeType,
    RelationshipType,
)


@dataclass(frozen=True)
class ValidationIssue:
    """Representation of an integrity or schema issue discovered in the KnowledgeGraph."""

    level: str  # "ERROR" or "WARNING"
    category: str
    message: str
    element_id: str | None = None


@dataclass
class ValidationReport:
    """Consolidated report of graph validation."""

    is_valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Return a human-readable summary of validation results."""
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Validation {status}: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)."
        )


def validate_graph(graph: KnowledgeGraph) -> ValidationReport:
    """Validate graph integrity, schema conformance, and reference consistency.

    Distinguishes canonical repository entities from synthetic unresolved placeholders.

    Args:
        graph: The KnowledgeGraph instance to validate.

    Returns:
        ValidationReport indicating validity, errors, warnings, and summary stats.
    """
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    nodes = graph.get_all_nodes()
    relationships = graph.get_all_relationships()

    # 1. Node Integrity & Schema Conformance
    for node_id, data in nodes.items():
        if not node_id or not isinstance(node_id, str):
            errors.append(
                ValidationIssue("ERROR", "node_id", "Node ID must be a non-empty string.", node_id)
            )

        name = data.get("name")
        if not name or not isinstance(name, str):
            errors.append(
                ValidationIssue("ERROR", "node_name", f"Node '{node_id}' is missing a valid name.", node_id)
            )

        raw_type = data.get("type")
        try:
            node_type = NodeType(raw_type)
        except ValueError:
            errors.append(
                ValidationIssue(
                    "ERROR", "node_type", f"Node '{node_id}' has invalid NodeType '{raw_type}'.", node_id
                )
            )
            continue

        is_synthetic = data.get("is_synthetic", False)

        if is_synthetic:
            # Synthetic placeholder validation
            if node_type != NodeType.UNRESOLVED_REFERENCE:
                errors.append(
                    ValidationIssue(
                        "ERROR",
                        "synthetic_node",
                        f"Synthetic node '{node_id}' must have type 'UnresolvedReference', got '{node_type}'.",
                        node_id,
                    )
                )
            if data.get("resolved") is not False:
                warnings.append(
                    ValidationIssue(
                        "WARNING",
                        "synthetic_node",
                        f"Synthetic node '{node_id}' should have resolved=False.",
                        node_id,
                    )
                )
        else:
            # Canonical analyzer entity validation
            if node_type not in ANALYZER_ENTITY_TYPES:
                errors.append(
                    ValidationIssue(
                        "ERROR",
                        "entity_type",
                        f"Repository entity '{node_id}' has non-canonical entity type '{node_type}'.",
                        node_id,
                    )
                )
            if node_type == NodeType.MODULE:
                errors.append(
                    ValidationIssue(
                        "ERROR",
                        "module_entity",
                        f"Entity '{node_id}' is of deprecated type Module; module_name must be on File.",
                        node_id,
                    )
                )

    # 2. Relationship Integrity & Reference Consistency
    for rel in relationships:
        source_id = rel.get("source")
        target_id = rel.get("target")
        rel_type_str = rel.get("type")
        rel_id = rel.get("id")

        if not source_id or not graph.has_node(source_id):
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "missing_source",
                    f"Relationship '{rel_id or rel_type_str}' references nonexistent source '{source_id}'.",
                    rel_id,
                )
            )

        if not target_id or not graph.has_node(target_id):
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "missing_target",
                    f"Relationship '{rel_id or rel_type_str}' references nonexistent target '{target_id}'.",
                    rel_id,
                )
            )

        try:
            rel_type = RelationshipType(rel_type_str)
        except ValueError:
            errors.append(
                ValidationIssue(
                    "ERROR",
                    "relationship_type",
                    f"Relationship '{rel_id}' has invalid RelationshipType '{rel_type_str}'.",
                    rel_id,
                )
            )
            continue

        if rel_type == RelationshipType.DEFINED_IN:
            warnings.append(
                ValidationIssue(
                    "WARNING",
                    "deprecated_relationship",
                    f"Relationship '{rel_id}' uses DEFINED_IN; CONTAINS is the canonical containment relationship.",
                    rel_id,
                )
            )

        # Unresolved CALLS validation
        if rel_type == RelationshipType.CALLS and (
            (target_id and target_id.startswith("unresolved:"))
            or rel.get("is_unresolved", False)
        ):
            target_node = graph.get_node(target_id)
            if target_node and not target_node.get("is_synthetic", False):
                errors.append(
                    ValidationIssue(
                        "ERROR",
                        "unresolved_reference",
                        f"Unresolved call target '{target_id}' is not marked as a synthetic node.",
                        rel_id,
                    )
                )

    is_valid = len(errors) == 0
    return ValidationReport(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        statistics={
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    )


def validate_or_raise(graph: KnowledgeGraph) -> None:
    """Validate the graph and raise KnowledgeGraphError if any errors are found."""
    report = validate_graph(graph)
    if not report.is_valid:
        error_msgs = "\n".join(f"- [{e.category}] {e.message}" for e in report.errors)
        raise KnowledgeGraphError(
            f"Knowledge Graph validation failed with {len(report.errors)} error(s):\n{error_msgs}"
        )
