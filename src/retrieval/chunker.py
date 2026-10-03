"""Code Entity Chunker for ProjectGenome.

Converts repository entities (File, Class, Function, Method) into normalized CodeChunk
retrieval units for embedding generation and vector search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    """Normalized retrieval chunk representing a single meaningful code entity."""

    repository_id: str = Field(default="repository", description="ID of the repository")
    entity_id: str = Field(..., description="Deterministic entity ID (e.g., func:src/a.py:foo)")
    entity_type: str = Field(..., description="Type of entity: file, class, function, method")
    name: str = Field(..., description="Name of the code entity")
    qualified_name: str | None = Field(default=None, description="Qualified name (e.g., Class.method)")
    file_path: str = Field(..., description="Relative file path")
    start_line: int | None = Field(default=None, description="Starting line number (1-indexed)")
    end_line: int | None = Field(default=None, description="Ending line number (1-indexed)")
    signature: str | None = Field(default=None, description="Function/Method/Class signature")
    docstring: str | None = Field(default=None, description="Docstring or doc comment if available")
    source_code: str = Field(default="", description="Source code snippet")
    text_representation: str = Field(..., description="Formatted text for embedding model input")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional entity properties")

    def to_dict(self) -> dict[str, Any]:
        """Serialize chunk to a dictionary."""
        return self.model_dump()


class CodeEntityChunker:
    """Chunks repository entities into normalized CodeChunk objects."""

    def __init__(self, repo_path: str | Path | None = None) -> None:
        """Initialize chunker.

        Args:
            repo_path: Optional path to the local repository directory for reading source code files.
        """
        self.repo_path = Path(repo_path) if repo_path else None

    def chunk_analysis_file(self, analysis_file_path: str | Path) -> list[CodeChunk]:
        """Load and chunk analyzer JSON file."""
        path = Path(analysis_file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file_path}")

        with open(path, encoding="utf-8") as f:
            raw_data = json.load(f)

        return self.chunk_analysis_dict(raw_data)

    def chunk_analysis_dict(self, data: dict[str, Any]) -> list[CodeChunk]:
        """Chunk raw analyzer JSON dictionary."""
        repo_data = data.get("repository")
        repo_id = (repo_data.get("name") if isinstance(repo_data, dict) else None) or "repository"
        entities = data.get("entities", [])

        chunks: list[CodeChunk] = []
        for entity in entities:
            chunk = self._chunk_entity_dict(entity, repo_id=repo_id)
            if chunk:
                chunks.append(chunk)
        return chunks

    def chunk_knowledge_graph(self, kg: Any) -> list[CodeChunk]:
        """Chunk entities from an in-memory KnowledgeGraph object."""
        repo_id = (kg.metadata.get("name") if hasattr(kg, "metadata") and kg.metadata else None) or "repository"
        chunks: list[CodeChunk] = []

        graph_obj = getattr(kg, "underlying_graph", getattr(kg, "_graph", kg))
        nodes_dict = graph_obj.nodes

        for node_id in nodes_dict:
            node_data = nodes_dict[node_id]
            # Skip synthetic unresolved nodes or non-code nodes
            if node_data.get("is_synthetic"):
                continue

            node_type = str(node_data.get("type", "")).lower()
            if node_type in ("repository", "directory", "unresolved_reference"):
                continue

            chunk = self._chunk_kg_node(node_id, node_data, repo_id=repo_id)
            if chunk:
                chunks.append(chunk)

        return chunks

    def _chunk_entity_dict(self, entity: dict[str, Any], repo_id: str = "repository") -> CodeChunk | None:
        """Process a single entity dict into a CodeChunk."""
        raw_type = str(entity.get("type", "")).lower()

        # Only chunk file, class, function, method entities
        if raw_type not in ("file", "class", "function", "method"):
            return None

        entity_id = entity.get("id", "")
        name = entity.get("name", "")
        file_path = entity.get("path", "")

        location = entity.get("location") or {}
        start_line = location.get("start_line")
        end_line = location.get("end_line")

        props = dict(entity.get("properties") or {})
        docstring = props.get("docstring")
        qualified_name = props.get("qualified_name")
        if not qualified_name and ":" in entity_id:
            parts_id = entity_id.split(":", 2)
            if len(parts_id) == 3:
                qualified_name = parts_id[2]
        if not qualified_name:
            qualified_name = name

        signature = self._derive_signature(name, raw_type, props)

        source_code = self._read_source_code(file_path, start_line, end_line)
        if not source_code and props.get("source_code"):
            source_code = props["source_code"]

        text_rep = self._format_text_representation(
            raw_type=raw_type,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            signature=signature,
            docstring=docstring,
            source_code=source_code,
        )

        return CodeChunk(
            repository_id=repo_id,
            entity_id=entity_id,
            entity_type=raw_type,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            signature=signature,
            docstring=docstring,
            source_code=source_code,
            text_representation=text_rep,
            metadata=props,
        )

    def _chunk_kg_node(self, node_id: str, node_data: dict[str, Any], repo_id: str = "repository") -> CodeChunk | None:
        """Process a KnowledgeGraph node into a CodeChunk."""
        raw_type = str(node_data.get("type", "")).lower()
        if raw_type not in ("file", "class", "function", "method"):
            return None

        name = node_data.get("name", "")
        file_path = node_data.get("path", "")
        location = node_data.get("location") or {}
        start_line = location.get("start_line")
        end_line = location.get("end_line")

        props = dict(node_data.get("properties") or {})
        docstring = props.get("docstring")
        qualified_name = props.get("qualified_name")
        if not qualified_name and ":" in node_id:
            parts_id = node_id.split(":", 2)
            if len(parts_id) == 3:
                qualified_name = parts_id[2]
        if not qualified_name:
            qualified_name = name

        signature = self._derive_signature(name, raw_type, props)

        source_code = self._read_source_code(file_path, start_line, end_line)
        if not source_code and props.get("source_code"):
            source_code = props["source_code"]

        text_rep = self._format_text_representation(
            raw_type=raw_type,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            signature=signature,
            docstring=docstring,
            source_code=source_code,
        )

        return CodeChunk(
            repository_id=repo_id,
            entity_id=node_id,
            entity_type=raw_type,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            signature=signature,
            docstring=docstring,
            source_code=source_code,
            text_representation=text_rep,
            metadata=props,
        )

    def _read_source_code(self, file_path: str, start_line: int | None, end_line: int | None) -> str:
        """Read source code snippet from repo file if available."""
        if not self.repo_path or not file_path:
            return ""

        full_path = self.repo_path / file_path
        if not full_path.is_file():
            return ""

        try:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if start_line is None or end_line is None:
                return "".join(lines)

            # Convert 1-indexed to 0-indexed slice
            s_idx = max(0, start_line - 1)
            e_idx = min(len(lines), end_line)
            return "".join(lines[s_idx:e_idx])
        except Exception:
            return ""

    def _derive_signature(self, name: str, entity_type: str, props: dict[str, Any]) -> str | None:
        """Derive readable signature for functions/methods/classes."""
        if props.get("signature"):
            return str(props["signature"])

        if entity_type in ("function", "method"):
            args = props.get("args") or props.get("parameters") or []
            if isinstance(args, list):
                args_str = ", ".join(str(a) for a in args)
            else:
                args_str = str(args)
            return f"{name}({args_str})"
        elif entity_type == "class":
            bases = props.get("bases") or []
            if bases:
                bases_str = ", ".join(str(b) for b in bases)
                return f"class {name}({bases_str})"
            return f"class {name}"

        return name

    def _format_text_representation(
        self,
        raw_type: str,
        name: str,
        qualified_name: str | None,
        file_path: str,
        signature: str | None,
        docstring: str | None,
        source_code: str,
    ) -> str:
        """Format chunk content for semantic embedding (CodeBERT)."""
        parts = [
            f"Entity Type: {raw_type.capitalize()}",
            f"Name: {name}",
        ]
        if qualified_name and qualified_name != name:
            parts.append(f"Qualified Name: {qualified_name}")
        parts.append(f"File: {file_path}")
        if signature:
            parts.append(f"Signature: {signature}")
        if docstring:
            parts.append(f"Docstring: {docstring}")
        if source_code:
            parts.append(f"Source Code:\n{source_code}")

        return "\n".join(parts)
