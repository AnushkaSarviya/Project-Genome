"""Reusable Presentation-Ready Knowledge Graph Visualizer for ProjectGenome.

Renders software repository knowledge graphs into publication-quality diagrams
with hierarchical containment layouts, distinct entity/relationship styling,
and automated legend generation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for CLI and scripting
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx

from src.knowledge_graph import KnowledgeGraph, import_json
from src.knowledge_graph.schema import NodeType, RelationshipType

# Node styling palette: (facecolor, edgecolor, marker_shape, base_size, linestyle)
NODE_STYLE_CONFIG: dict[str, dict[str, Any]] = {
    "Repository": {
        "color": "#3949AB",  # Indigo
        "edgecolor": "#1A237E",
        "shape": "o",
        "size": 1700,
        "linestyle": "-",
        "label": "Repository",
    },
    "Directory": {
        "color": "#00897B",  # Teal
        "edgecolor": "#004D40",
        "shape": "o",
        "size": 1350,
        "linestyle": "-",
        "label": "Directory",
    },
    "File": {
        "color": "#0288D1",  # Light Blue
        "edgecolor": "#01579B",
        "shape": "s",  # Square
        "size": 1150,
        "linestyle": "-",
        "label": "File",
    },
    "Class": {
        "color": "#F57C00",  # Orange
        "edgecolor": "#E65100",
        "shape": "^",  # Triangle
        "size": 1200,
        "linestyle": "-",
        "label": "Class",
    },
    "Function": {
        "color": "#2E7D32",  # Green
        "edgecolor": "#1B5E20",
        "shape": "o",
        "size": 1050,
        "linestyle": "-",
        "label": "Function",
    },
    "Method": {
        "color": "#7CB342",  # Light Green
        "edgecolor": "#33691E",
        "shape": "o",
        "size": 900,
        "linestyle": "-",
        "label": "Method",
    },
    "UnresolvedReference": {
        "color": "#EF5350",  # Coral / Red
        "edgecolor": "#B71C1C",
        "shape": "d",  # Diamond
        "size": 950,
        "linestyle": "--",
        "label": "Unresolved Reference (Synthetic)",
    },
}

# Relationship styling palette: (color, linestyle, width, alpha, arc_radius)
REL_STYLE_CONFIG: dict[str, dict[str, Any]] = {
    "CONTAINS": {
        "color": "#78909C",  # Blue-gray
        "linestyle": "-",
        "width": 1.4,
        "alpha": 0.65,
        "rad": 0.0,
        "label": "CONTAINS (Hierarchy)",
    },
    "IMPORTS": {
        "color": "#1976D2",  # Vivid Blue
        "linestyle": "--",
        "width": 1.8,
        "alpha": 0.85,
        "rad": 0.14,
        "label": "IMPORTS (Module Dependency)",
    },
    "CALLS": {
        "color": "#D32F2F",  # Crimson Red
        "linestyle": "-",
        "width": 2.0,
        "alpha": 0.90,
        "rad": 0.20,
        "label": "CALLS (Invocation)",
    },
    "INHERITS": {
        "color": "#8E24AA",  # Purple
        "linestyle": "-.",
        "width": 2.2,
        "alpha": 0.90,
        "rad": -0.16,
        "label": "INHERITS (Subclassing)",
    },
    "DEPENDS_ON": {
        "color": "#FB8C00",  # Dark Orange
        "linestyle": ":",
        "width": 2.4,
        "alpha": 0.95,
        "rad": -0.22,
        "label": "DEPENDS_ON (Derived)",
    },
}

TYPE_LAYER_FALLBACK = {
    "Repository": 0,
    "Directory": 1,
    "File": 2,
    "Class": 3,
    "Function": 3,
    "Method": 4,
    "UnresolvedReference": 5,
}


def compute_hierarchical_layout(
    graph: nx.MultiDiGraph,
    horizontal_spacing: float = 3.0,
    vertical_spacing: float = 2.4,
) -> dict[str, tuple[float, float]]:
    """Compute a top-down layered hierarchical layout for a software knowledge graph.

    Aligns entities vertically by architectural level (Repository -> Directory -> File ->
    Class/Function -> Method -> Unresolved References) and orders siblings horizontally
    by their parent container to minimize edge crossings.

    Args:
        graph: NetworkX MultiDiGraph instance.
        horizontal_spacing: Horizontal distance between sibling nodes.
        vertical_spacing: Vertical distance between architectural layers.

    Returns:
        Mapping of node IDs to (x, y) coordinates.
    """
    if not graph.nodes():
        return {}

    # Extract the CONTAINS hierarchy DAG
    h_contains = nx.DiGraph()
    for u, v, d in graph.edges(data=True):
        if d.get("type") == RelationshipType.CONTAINS.value:
            h_contains.add_edge(u, v)

    # Identify hierarchy roots
    roots = [n for n in h_contains.nodes() if h_contains.in_degree(n) == 0]
    if not roots:
        # Fallback: any node with in-degree 0 in the main graph
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            roots = [next(iter(graph.nodes()))]

    # Assign vertical layers (depths)
    depths: dict[str, int] = {}
    for n, data in graph.nodes(data=True):
        candidates = []
        if n in h_contains:
            for r in roots:
                if nx.has_path(h_contains, r, n):
                    candidates.append(nx.shortest_path_length(h_contains, r, n))
        if candidates:
            depths[n] = min(candidates)
        elif data.get("is_synthetic", False) or data.get("type") == NodeType.UNRESOLVED_REFERENCE.value:
            # Place unresolved synthetic nodes at the bottom level
            depths[n] = 5
        else:
            node_type = data.get("type", "File")
            depths[n] = TYPE_LAYER_FALLBACK.get(node_type, 2)

    # Normalize depths so they form contiguous 0..max_d
    max_d = max(depths.values()) if depths else 0
    pos: dict[str, tuple[float, float]] = {}

    for d in range(max_d + 1):
        level_nodes = [n for n, dep in depths.items() if dep == d]
        if not level_nodes:
            continue

        # Sort siblings horizontally by parent's x position to cluster children under parents
        def get_parent_sort_key(node_id: str) -> tuple[float, str]:
            if node_id in h_contains:
                parents = [p for p in h_contains.predecessors(node_id) if p in pos]
                if parents:
                    return (sum(pos[p][0] for p in parents) / len(parents), node_id)
            # Fallback for synthetic/unresolved nodes: cluster under callers
            callers = [u for u, _, _ in graph.in_edges(node_id, data=True) if u in pos]
            if callers:
                return (sum(pos[c][0] for c in callers) / len(callers), node_id)
            return (0.0, node_id)

        level_nodes.sort(key=get_parent_sort_key)

        n_count = len(level_nodes)
        total_width = (n_count - 1) * horizontal_spacing
        start_x = -total_width / 2.0

        for i, node_id in enumerate(level_nodes):
            x_coord = start_x + (i * horizontal_spacing) if n_count > 1 else 0.0
            y_coord = -d * vertical_spacing
            pos[node_id] = (x_coord, y_coord)

    return pos


def format_node_label(node_id: str, data: dict[str, Any], max_length: int = 18) -> str:
    """Format a clean, readable label for a node, truncating if necessary."""
    raw_name = data.get("name") or node_id.split(":")[-1]
    node_type = data.get("type", "")

    if data.get("is_synthetic", False) or node_type == "UnresolvedReference":
        raw_call = data.get("raw_call") or raw_name
        if len(raw_call) > max_length:
            raw_call = raw_call[: max_length - 3] + "..."
        return f"? {raw_call}"

    if node_type == "Method":
        if "(" not in raw_name:
            raw_name = f"{raw_name}()"
    elif node_type == "Function":
        if "(" not in raw_name:
            raw_name = f"{raw_name}()"

    if len(raw_name) > max_length:
        return raw_name[: max_length - 3] + "..."
    return raw_name


class RepositoryGraphVisualizer:
    """Configurable visualizer for Software Knowledge Graphs."""

    def __init__(self, graph_or_source: KnowledgeGraph | nx.MultiDiGraph | str | Path | dict[str, Any]) -> None:
        """Initialize with a KnowledgeGraph, MultiDiGraph, file path, or dictionary.

        Args:
            graph_or_source: KnowledgeGraph instance or source JSON path/dict.
        """
        if isinstance(graph_or_source, KnowledgeGraph):
            self.kg = graph_or_source
        elif isinstance(graph_or_source, nx.MultiDiGraph):
            self.kg = KnowledgeGraph()
            self.kg._graph = graph_or_source
        elif isinstance(graph_or_source, (str, Path, dict)):
            self.kg = import_json(graph_or_source)
        else:
            raise TypeError(f"Unsupported graph source type: {type(graph_or_source)}")

    def render(
        self,
        output_path: str | Path | None = "data/generated/repository_graph.png",
        hide_unresolved: bool = False,
        hide_derived: bool = False,
        relationship_types: list[str] | None = None,
        layout: str = "hierarchical",
        dpi: int = 300,
        title: str | None = None,
        show: bool = False,
    ) -> Path | None:
        """Render and save the visualization diagram.

        Args:
            output_path: Destination image path (.png).
            hide_unresolved: If True, omit synthetic unresolved reference nodes.
            hide_derived: If True, omit derived relationships (e.g. DEPENDS_ON).
            relationship_types: Optional list of relationship types to include.
            layout: "hierarchical" (default), "spring", or "multipartite".
            dpi: Image resolution.
            title: Custom plot title.
            show: If True, invoke plt.show() interactively.

        Returns:
            Resolved Path of the saved image file, or None if output_path is None.
        """
        # Build filtered copy of the graph
        g_raw = self.kg.underlying_graph
        g: nx.MultiDiGraph = nx.MultiDiGraph()

        # Filter nodes
        for node_id, data in g_raw.nodes(data=True):
            if hide_unresolved and (
                data.get("is_synthetic", False)
                or data.get("type") == NodeType.UNRESOLVED_REFERENCE.value
            ):
                continue
            g.add_node(node_id, **data)

        # Filter edges
        allowed_rel_types = set(relationship_types) if relationship_types else None
        for u, v, key, data in g_raw.edges(keys=True, data=True):
            if u not in g or v not in g:
                continue
            rel_type = data.get("type", "")
            if hide_derived and (data.get("is_derived", False) or rel_type == "DEPENDS_ON"):
                continue
            if allowed_rel_types and rel_type not in allowed_rel_types:
                continue
            g.add_edge(u, v, key=key, **data)

        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()

        # Handle empty graph edge case
        if num_nodes == 0:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(
                0.5, 0.5, "Empty Knowledge Graph\n(No nodes to display)",
                ha="center", va="center", fontsize=14, color="#78909C"
            )
            ax.axis("off")
            if output_path:
                out = Path(output_path)
                out.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(out, dpi=dpi, bbox_inches="tight")
                plt.close(fig)
                return out
            plt.close(fig)
            return None

        # Compute layout coordinates
        if layout == "hierarchical":
            pos = compute_hierarchical_layout(g)
        elif layout == "spring":
            pos = nx.spring_layout(g, seed=42, k=1.5 / max(1, num_nodes ** 0.5))
        elif layout == "multipartite":
            for n, d in g.nodes(data=True):
                g.nodes[n]["subset"] = TYPE_LAYER_FALLBACK.get(d.get("type", "File"), 2)
            pos = nx.multipartite_layout(g, subset_key="subset", align="horizontal")
        else:
            raise ValueError(f"Unknown layout algorithm: '{layout}'. Choose 'hierarchical', 'spring', or 'multipartite'.")

        # Dynamically determine canvas dimensions
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        x_range = max(xs) - min(xs) if xs else 10.0
        y_range = max(ys) - min(ys) if ys else 8.0

        fig_width = max(16.0, min(36.0, x_range * 1.0 + 6.0))
        fig_height = max(11.0, min(28.0, y_range * 1.3 + 5.0))

        fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor="#FAFAFA")
        ax.set_facecolor("#FAFAFA")

        # 1. Draw Edges grouped by relationship type
        for rel_type, rel_cfg in REL_STYLE_CONFIG.items():
            edge_list = [
                (u, v) for u, v, d in g.edges(data=True)
                if d.get("type") == rel_type
            ]
            if not edge_list:
                continue

            rad = rel_cfg["rad"]
            conn_style = f"arc3,rad={rad}" if rad != 0.0 else "arc3,rad=0.0"

            nx.draw_networkx_edges(
                g,
                pos,
                edgelist=edge_list,
                ax=ax,
                edge_color=rel_cfg["color"],
                style=rel_cfg["linestyle"],
                width=rel_cfg["width"],
                alpha=rel_cfg["alpha"],
                arrows=True,
                arrowsize=14,
                arrowstyle="-|>",
                connectionstyle=conn_style,
                node_size=1000,
            )

        # 2. Draw Nodes grouped by node type
        for type_key, type_cfg in NODE_STYLE_CONFIG.items():
            node_list = []
            for n, d in g.nodes(data=True):
                n_type = d.get("type", "")
                if type_key == "UnresolvedReference":
                    if d.get("is_synthetic", False) or n_type == "UnresolvedReference":
                        node_list.append(n)
                else:
                    if n_type == type_key and not d.get("is_synthetic", False):
                        node_list.append(n)

            if not node_list:
                continue

            nx.draw_networkx_nodes(
                g,
                pos,
                nodelist=node_list,
                ax=ax,
                node_color=type_cfg["color"],
                edgecolors=type_cfg["edgecolor"],
                node_shape=type_cfg["shape"],
                node_size=type_cfg["size"],
                linewidths=2.0,
            )

        # 3. Draw Node Labels with legible halo bboxes
        labels = {n: format_node_label(n, d) for n, d in g.nodes(data=True)}
        for node_id, (lx, ly) in pos.items():
            label_text = labels.get(node_id, "")
            node_data = g.nodes[node_id]
            is_unresolved = node_data.get("is_synthetic", False) or node_data.get("type") == "UnresolvedReference"

            font_weight = "bold" if not is_unresolved else "normal"
            font_size = 7.5 if is_unresolved else 8.5
            box_edge = "#B71C1C" if is_unresolved else "#CFD8DC"

            ax.text(
                lx,
                ly,
                label_text,
                fontsize=font_size,
                fontweight=font_weight,
                color="#212121",
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="white",
                    edgecolor=box_edge,
                    alpha=0.88,
                    linewidth=0.6,
                ),
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
                zorder=10,
            )

        # 4. Construct Dual Legends (Entity Types + Relationship Types)
        entity_handles = []
        for type_key, type_cfg in NODE_STYLE_CONFIG.items():
            # Check if this type appears in the current graph
            has_instances = any(
                (d.get("is_synthetic", False) or d.get("type") == "UnresolvedReference")
                if type_key == "UnresolvedReference"
                else (d.get("type") == type_key and not d.get("is_synthetic", False))
                for _, d in g.nodes(data=True)
            )
            if has_instances:
                entity_handles.append(
                    mlines.Line2D(
                        [], [],
                        color="white",
                        marker=type_cfg["shape"],
                        markerfacecolor=type_cfg["color"],
                        markeredgecolor=type_cfg["edgecolor"],
                        markeredgewidth=1.5,
                        markersize=10,
                        label=type_cfg["label"],
                    )
                )

        rel_handles = []
        for rel_type, rel_cfg in REL_STYLE_CONFIG.items():
            has_edges = any(d.get("type") == rel_type for _, _, d in g.edges(data=True))
            if has_edges:
                rel_handles.append(
                    mlines.Line2D(
                        [], [],
                        color=rel_cfg["color"],
                        linestyle=rel_cfg["linestyle"],
                        linewidth=2.2,
                        label=rel_cfg["label"],
                    )
                )

        # Place Entity Legend
        legend_entity = ax.legend(
            handles=entity_handles,
            title="Repository Entities",
            title_fontsize=10.5,
            fontsize=9.0,
            loc="upper left",
            frameon=True,
            facecolor="white",
            edgecolor="#B0BEC5",
            framealpha=0.95,
        )
        ax.add_artist(legend_entity)

        # Place Relationship Legend
        if rel_handles:
            ax.legend(
                handles=rel_handles,
                title="Relationship Types",
                title_fontsize=10.5,
                fontsize=9.0,
                loc="upper right",
                frameon=True,
                facecolor="white",
                edgecolor="#B0BEC5",
                framealpha=0.95,
            )

        # 5. Header Title & Subtitle Statistics
        resolved_count = sum(1 for _, d in g.nodes(data=True) if not d.get("is_synthetic", False))
        unresolved_count = sum(1 for _, d in g.nodes(data=True) if d.get("is_synthetic", False))

        default_title = title or "ProjectGenome — Software Knowledge Graph"
        stats_subtitle = (
            f"{num_nodes} Nodes ({resolved_count} Repository Entities, {unresolved_count} Synthetic Call Placeholders) | "
            f"{num_edges} Relationships"
        )

        ax.set_title(
            f"{default_title}\n{stats_subtitle}",
            fontsize=13,
            fontweight="bold",
            color="#263238",
            pad=18,
        )

        ax.axis("off")
        fig.tight_layout()

        # Save output
        resolved_path = None
        if output_path is not None:
            resolved_path = Path(output_path)
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(resolved_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())

        if show:
            plt.show()

        plt.close(fig)
        return resolved_path


def visualize_graph(
    json_path: str | Path,
    output_path: str | Path | None = "data/generated/repository_graph.png",
    hide_unresolved: bool = False,
    hide_derived: bool = False,
    relationship_types: list[str] | None = None,
    layout: str = "hierarchical",
    dpi: int = 300,
    title: str | None = None,
    show: bool = False,
) -> Path | None:
    """Convenience functional wrapper to load and visualize a graph JSON file."""
    visualizer = RepositoryGraphVisualizer(json_path)
    return visualizer.render(
        output_path=output_path,
        hide_unresolved=hide_unresolved,
        hide_derived=hide_derived,
        relationship_types=relationship_types,
        layout=layout,
        dpi=dpi,
        title=title,
        show=show,
    )


def main() -> None:
    """Command-line interface entry point for the ProjectGenome graph visualizer."""
    parser = argparse.ArgumentParser(
        description="ProjectGenome Software Knowledge Graph Visualizer"
    )
    parser.add_argument(
        "json_path",
        type=str,
        help="Path to the graph JSON file (e.g. data/generated/repository_graph.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/generated/repository_graph.png",
        help="Destination path for generated PNG (default: data/generated/repository_graph.png)",
    )
    parser.add_argument(
        "--hide-unresolved",
        action="store_true",
        help="Omit synthetic unresolved reference nodes and their calling edges",
    )
    parser.add_argument(
        "--hide-derived",
        action="store_true",
        help="Omit derived relationships (e.g. DEPENDS_ON)",
    )
    parser.add_argument(
        "--relationships",
        type=str,
        default=None,
        help="Comma-separated relationship types to include (e.g. 'CALLS,IMPORTS')",
    )
    parser.add_argument(
        "--layout",
        type=str,
        choices=["hierarchical", "spring", "multipartite"],
        default="hierarchical",
        help="Graph layout algorithm (default: hierarchical)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution of output diagram in DPI (default: 300)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional custom title for the visualization",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open an interactive GUI window via plt.show()",
    )

    args = parser.parse_args()

    rel_types = (
        [r.strip().upper() for r in args.relationships.split(",")]
        if args.relationships
        else None
    )

    saved_path = visualize_graph(
        json_path=args.json_path,
        output_path=args.output,
        hide_unresolved=args.hide_unresolved,
        hide_derived=args.hide_derived,
        relationship_types=rel_types,
        layout=args.layout,
        dpi=args.dpi,
        title=args.title,
        show=args.show,
    )

    if saved_path:
        print(f"Visualization successfully generated at: {saved_path}")


if __name__ == "__main__":
    main()
