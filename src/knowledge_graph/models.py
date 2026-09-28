"""Typed data models representing normalized Repository Intelligence analyzer output.

Adheres strictly to Nyasa's Repository Intelligence frozen v2.0 contract.
Accommodates variable entity metadata and preserves full analyzer provenance.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .schema import (
    ANALYZER_ENTITY_TYPES,
    DERIVED_RELATIONSHIP_TYPES,
    PRIMITIVE_RELATIONSHIP_TYPES,
    NodeType,
    RelationshipType,
)


class Location(BaseModel):
    """Source code span location metadata."""

    file: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None

    model_config = ConfigDict(extra="allow")


class Entity(BaseModel):
    """Normalized repository entity emitted by repository intelligence."""

    id: str
    type: NodeType | str
    name: str
    path: str | None = None
    location: Location | None = None
    properties: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @property
    def is_analyzer_entity(self) -> bool:
        """Return True if this entity type is one of the 6 canonical analyzer entity types."""
        try:
            enum_type = NodeType(self.type) if isinstance(self.type, str) else self.type
            return enum_type in ANALYZER_ENTITY_TYPES
        except ValueError:
            return False

    @property
    def is_synthetic(self) -> bool:
        """Return True if this is a synthetic placeholder (e.g. UnresolvedReference)."""
        return (
            self.type == NodeType.UNRESOLVED_REFERENCE
            or self.type == NodeType.UNRESOLVED_REFERENCE.value
            or self.properties.get("is_synthetic", False)
        )


class Relationship(BaseModel):
    """Directed interaction or dependency between two entities."""

    id: str | None = None
    source: str
    type: RelationshipType | str
    target: str
    location: Location | None = None
    properties: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @property
    def is_derived(self) -> bool:
        """Return True if this relationship is derived by the analyzer (e.g. DEPENDS_ON)."""
        if self.properties.get("derived", False):
            return True
        try:
            enum_type = RelationshipType(self.type) if isinstance(self.type, str) else self.type
            return enum_type in DERIVED_RELATIONSHIP_TYPES
        except ValueError:
            return False

    @property
    def is_primitive(self) -> bool:
        """Return True if this relationship is primitive/extracted (CONTAINS, IMPORTS, CALLS, INHERITS)."""
        if self.is_derived:
            return False
        try:
            enum_type = RelationshipType(self.type) if isinstance(self.type, str) else self.type
            return enum_type in PRIMITIVE_RELATIONSHIP_TYPES
        except ValueError:
            return False

    @property
    def is_unresolved(self) -> bool:
        """Return True if this relationship points to an unresolved target reference."""
        return (
            self.target.startswith("unresolved:")
            or self.properties.get("resolved") is False
        )


class AnalyzerStats(BaseModel):
    """Extraction statistics emitted by the analyzer."""

    total_entities: int | None = None
    total_relationships: int | None = None
    primitive_relationships: int | None = None
    derived_relationships: int | None = None
    unresolved_calls_count: int | None = None

    model_config = ConfigDict(extra="allow")


class AnalyzerMetadata(BaseModel):
    """Metadata describing the repository analysis run."""

    repository_identity: str | None = None
    root_path: str | None = None
    extracted_at: str | None = None
    analyzer_version: str | None = None
    stats: AnalyzerStats | dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class AnalyzerOutput(BaseModel):
    """Top-level normalized payload produced by Nyasa's Repository Intelligence module."""

    version: str = "1.0.0"
    metadata: AnalyzerMetadata | dict[str, Any] = Field(default_factory=dict)
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
