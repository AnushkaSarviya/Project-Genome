"""ProjectGenome Visualization Package.

Reusable, presentation-ready graph visualizer for software repository knowledge graphs.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph_visualizer import (
        RepositoryGraphVisualizer,
        compute_hierarchical_layout,
        visualize_graph,
    )

__all__ = [
    "RepositoryGraphVisualizer",
    "compute_hierarchical_layout",
    "visualize_graph",
]


def __getattr__(name: str):
    if name in __all__:
        from . import graph_visualizer
        return getattr(graph_visualizer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
