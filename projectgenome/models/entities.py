"""Entity definitions for ProjectGenome IR."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EntityType(str, Enum):
    REPOSITORY = "Repository"
    DIRECTORY = "Directory"
    FILE = "File"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"


@dataclass
class SourceLocation:
    file: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
        }

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["SourceLocation"]:
        if not d:
            return None
        return cls(**d)


@dataclass
class Entity:
    id: str
    type: EntityType
    name: str
    path: str
    location: Optional[SourceLocation] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, EntityType) else str(self.type),
            "name": self.name,
            "path": self.path,
            "location": self.location.to_dict() if self.location else None,
            "properties": self.properties,
        }
