"""JSON Exporter module for serializing RepositoryAnalysisOutput to standardized, deterministic JSON files."""

import json
from pathlib import Path
from typing import Union

from projectgenome.models.schema import RepositoryAnalysisOutput


class JSONExporter:
    """Handles deterministic serialization of repository analysis outputs."""

    def __init__(self, output: RepositoryAnalysisOutput):
        self.output = output

    def to_json_string(self, canonical_only: bool = False) -> str:
        """Serializes output to a formatted, sorted JSON string.
        
        If canonical_only is True, non-canonical run metadata (such as timestamps) is excluded.
        """
        data = self.output.get_canonical_dict() if canonical_only else self.output.to_dict()
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    def export(self, target_path: Union[str, Path], canonical_only: bool = False) -> Path:
        """Writes the JSON representation to target_path."""
        dest = Path(target_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        json_content = self.to_json_string(canonical_only=canonical_only)
        
        with open(dest, "w", encoding="utf-8") as f:
            f.write(json_content)
            
        return dest
