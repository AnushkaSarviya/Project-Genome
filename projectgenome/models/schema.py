"""Repository Analysis Output Envelope and Canonical Hashing logic."""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List

from projectgenome.models.entities import Entity
from projectgenome.models.relationships import Relationship


@dataclass
class RepositoryAnalysisOutput:
    repository_identity: str
    root_path: str
    extracted_at: str
    analyzer_version: str = "0.1.0"
    version: str = "1.0.0"
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    extra_stats: Dict[str, Any] = field(default_factory=dict)

    def get_canonical_dict(self) -> Dict[str, Any]:
        """Returns the canonical dictionary representation with sorted entities and relationships.
        
        Metadata fields like 'extracted_at' are omitted or neutralized to ensure canonical hashing stability.
        """
        sorted_entities = sorted([e.to_dict() for e in self.entities], key=lambda x: x["id"])
        sorted_relationships = sorted([r.to_dict() for r in self.relationships], key=lambda x: x["id"])

        return {
            "version": self.version,
            "metadata": {
                "repository_identity": self.repository_identity,
                "analyzer_version": self.analyzer_version,
            },
            "entities": sorted_entities,
            "relationships": sorted_relationships,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Returns the full serialization dictionary including run metadata."""
        sorted_entities = sorted([e.to_dict() for e in self.entities], key=lambda x: x["id"])
        sorted_relationships = sorted([r.to_dict() for r in self.relationships], key=lambda x: x["id"])

        primitive_count = sum(1 for r in self.relationships if not r.properties.get("derived", False))
        derived_count = sum(1 for r in self.relationships if r.properties.get("derived", False))
        unresolved_count = sum(1 for r in self.relationships if not r.properties.get("resolved", True))

        stats = {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "primitive_relationships": primitive_count,
            "derived_relationships": derived_count,
            "unresolved_calls_count": unresolved_count,
        }
        stats.update(self.extra_stats)

        return {
            "version": self.version,
            "metadata": {
                "repository_identity": self.repository_identity,
                "root_path": self.root_path,
                "extracted_at": self.extracted_at,
                "analyzer_version": self.analyzer_version,
                "stats": stats,
            },
            "entities": sorted_entities,
            "relationships": sorted_relationships,
        }

    def compute_canonical_hash(self) -> str:
        """Computes a SHA-256 hash of the canonical dictionary (excluding timestamp)."""
        canonical_json = json.dumps(self.get_canonical_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
