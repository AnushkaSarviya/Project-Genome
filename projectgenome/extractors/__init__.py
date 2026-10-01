"""Extractors package for IR entity and relationship generation."""

from projectgenome.extractors.entity_extractor import EntityExtractor
from projectgenome.extractors.relationship_extractor import (
    RelationshipExtractor,
    SymbolTable,
    derive_depends_on_relationships,
)

__all__ = [
    "EntityExtractor",
    "RelationshipExtractor",
    "SymbolTable",
    "derive_depends_on_relationships",
]
