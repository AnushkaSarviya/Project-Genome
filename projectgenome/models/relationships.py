"""Relationship definitions for ProjectGenome IR."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from projectgenome.models.entities import SourceLocation


class RelationshipType(str, Enum):
    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    CALLS = "CALLS"
    DEPENDS_ON = "DEPENDS_ON"


@dataclass
class Relationship:
    id: str
    source: str
    type: RelationshipType
    target: str
    location: Optional[SourceLocation] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "type": self.type.value if isinstance(self.type, RelationshipType) else str(self.type),
            "target": self.target,
            "location": self.location.to_dict() if self.location else None,
            "properties": self.properties,
        }
