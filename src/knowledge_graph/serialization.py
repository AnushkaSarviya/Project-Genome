"""Serialization and deserialization for ProjectGenome Software Knowledge Graph.

Supports JSON and GraphML formats, preserving all node, relationship, and provenance metadata.
Converts complex nested structures deterministically for GraphML compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from .graph import KnowledgeGraph
from .schema import NodeType, RelationshipType

DEFAULT_JSON_PATH = Path("data/generated/repository_graph.json")
DEFAULT_GRAPHML_PATH = Path("data/generated/repository_graph.graphml")


def export_json(
    graph: KnowledgeGraph,
    file_path: str | Path | None = None,
    indent: int = 2,
) -> str:
    """Export the KnowledgeGraph to a structured JSON string and optionally to a file.

    Preserves node attributes, relationship attributes, synthetic markers, and graph metadata.

    Args:
        graph: The KnowledgeGraph instance.
        file_path: Optional destination file path. If None, only returns JSON string.
        indent: JSON indentation formatting.

    Returns:
        Formatted JSON string representation of the graph.
    """
    nodes_list = []
    for node_id, data in sorted(graph.get_all_nodes().items(), key=lambda x: x[0]):
        node_payload = dict(data)
        node_payload["id"] = node_id
        nodes_list.append(node_payload)

    relationships_list = []
    for rel in graph.get_all_relationships():
        relationships_list.append(dict(rel))

    payload = {
        "version": "1.0.0",
        "metadata": graph.metadata,
        "nodes": nodes_list,
        "relationships": relationships_list,
    }

    json_str = json.dumps(payload, indent=indent, default=str)

    if file_path is not None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str, encoding="utf-8")

    return json_str


def import_json(file_path_or_str: str | Path) -> KnowledgeGraph:
    """Import and reconstruct a KnowledgeGraph from a JSON file or JSON string.

    Args:
        file_path_or_str: Path to a JSON file or raw JSON string.

    Returns:
        Reconstructed KnowledgeGraph.
    """
    path = Path(file_path_or_str)
    if path.is_file():
        raw_text = path.read_text(encoding="utf-8")
    else:
        raw_text = str(file_path_or_str)

    data = json.loads(raw_text)
    kg = KnowledgeGraph(metadata=data.get("metadata", {}))

    for node in data.get("nodes", []):
        node_id = node.get("id")
        node_type = node.get("type")
        name = node.get("name", node_id)
        metadata = {k: v for k, v in node.items() if k not in ("id", "type", "name")}
        kg.add_node(
            node_id=node_id,
            node_type=node_type,
            name=name,
            raise_if_exists=False,
            **metadata,
        )

    for rel in data.get("relationships", []):
        source_id = rel.get("source")
        target_id = rel.get("target")
        rel_type = rel.get("type")
        key = rel.get("id") or rel_type
        metadata = {k: v for k, v in rel.items() if k not in ("source", "target", "type")}
        kg.add_relationship(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            key=key,
            raise_if_exists=False,
            **metadata,
        )

    return kg


def export_graphml(graph: KnowledgeGraph, file_path: str | Path) -> None:
    """Export the KnowledgeGraph to GraphML format.

    Serializes nested dictionaries and lists (such as locations and properties) into
    deterministic JSON strings to maintain GraphML specification compliance without
    discarding metadata.

    Args:
        graph: The KnowledgeGraph instance.
        file_path: Output file path (.graphml).
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    g_export = nx.MultiDiGraph()

    for node_id, data in graph.get_all_nodes().items():
        attr_dict: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                attr_dict[k] = json.dumps(v, sort_keys=True)
            elif v is None:
                attr_dict[k] = ""
            elif isinstance(v, (int, float, str, bool)):
                attr_dict[k] = v
            else:
                attr_dict[k] = str(v)
        g_export.add_node(node_id, **attr_dict)

    for u, v, key, data in graph.underlying_graph.edges(keys=True, data=True):
        attr_dict = {}
        for k, val in data.items():
            if isinstance(val, (dict, list)):
                attr_dict[k] = json.dumps(val, sort_keys=True)
            elif val is None:
                attr_dict[k] = ""
            elif isinstance(val, (int, float, str, bool)):
                attr_dict[k] = val
            else:
                attr_dict[k] = str(val)
        g_export.add_edge(u, v, key=str(key), **attr_dict)

    nx.write_graphml(g_export, str(path))


def import_graphml(file_path: str | Path) -> KnowledgeGraph:
    """Import and reconstruct a KnowledgeGraph from a GraphML file.

    Parses serialized JSON string attributes back into their original Python structures.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"GraphML file not found: {file_path}")

    g_imported = nx.read_graphml(str(path))
    kg = KnowledgeGraph()

    for node_id, data in g_imported.nodes(data=True):
        unpacked_data: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    unpacked_data[k] = json.loads(v)
                    continue
                except json.JSONDecodeError:
                    pass
            unpacked_data[k] = v

        node_type = unpacked_data.pop("type", "Repository")
        name = unpacked_data.pop("name", str(node_id))
        unpacked_data.pop("id", None)

        kg.add_node(
            node_id=str(node_id),
            node_type=node_type,
            name=name,
            raise_if_exists=False,
            **unpacked_data,
        )

    for u, v, key, data in g_imported.edges(keys=True, data=True):
        unpacked_data = {}
        for k, val in data.items():
            if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
                try:
                    unpacked_data[k] = json.loads(val)
                    continue
                except json.JSONDecodeError:
                    pass
            unpacked_data[k] = val

        rel_type = unpacked_data.pop("type", "CONTAINS")
        unpacked_data.pop("source", None)
        unpacked_data.pop("target", None)

        kg.add_relationship(
            source_id=str(u),
            target_id=str(v),
            rel_type=rel_type,
            key=str(key),
            raise_if_exists=False,
            **unpacked_data,
        )

    return kg
