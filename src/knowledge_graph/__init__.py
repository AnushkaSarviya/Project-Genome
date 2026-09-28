"""ProjectGenome Software Knowledge Graph Package.

Comprehensive, research-oriented Knowledge Graph for repository-level code understanding.
"""

from .builder import KnowledgeGraphBuilder, build_from_analysis
from .graph import (
    InvalidNodeTypeError,
    InvalidRelationshipTypeError,
    KnowledgeGraph,
    KnowledgeGraphError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    RelationshipAlreadyExistsError,
    validate_node_type,
    validate_relationship_type,
)
from .models import (
    AnalyzerMetadata,
    AnalyzerOutput,
    AnalyzerStats,
    Entity,
    Location,
    Relationship,
)
from .queries import (
    find_nodes_by_name,
    find_nodes_by_type,
    get_node,
    get_relationships,
    get_relationships_by_type,
    get_repository_entities,
    get_statistics,
    get_structural_context,
    get_synthetic_nodes,
)
from .schema import (
    ANALYZER_ENTITY_TYPES,
    DERIVED_RELATIONSHIP_TYPES,
    PRIMITIVE_RELATIONSHIP_TYPES,
    NodeType,
    RelationshipType,
)
from .serialization import (
    DEFAULT_GRAPHML_PATH,
    DEFAULT_JSON_PATH,
    export_graphml,
    export_json,
    import_graphml,
    import_json,
)
from .traversal import (
    expand_context,
    find_path,
    get_callees,
    get_callers,
    get_dependencies,
    get_dependents,
    get_neighbors,
    multi_hop_traversal,
)
from .validation import (
    ValidationIssue,
    ValidationReport,
    validate_graph,
    validate_or_raise,
)

__all__ = [
    # Schema
    "NodeType",
    "RelationshipType",
    "ANALYZER_ENTITY_TYPES",
    "PRIMITIVE_RELATIONSHIP_TYPES",
    "DERIVED_RELATIONSHIP_TYPES",
    # Core Graph
    "KnowledgeGraph",
    "KnowledgeGraphError",
    "NodeNotFoundError",
    "NodeAlreadyExistsError",
    "RelationshipAlreadyExistsError",
    "InvalidNodeTypeError",
    "InvalidRelationshipTypeError",
    "validate_node_type",
    "validate_relationship_type",
    # Models
    "Entity",
    "Relationship",
    "Location",
    "AnalyzerMetadata",
    "AnalyzerStats",
    "AnalyzerOutput",
    # Builder
    "KnowledgeGraphBuilder",
    "build_from_analysis",
    # Traversal
    "get_neighbors",
    "get_callers",
    "get_callees",
    "get_dependencies",
    "get_dependents",
    "find_path",
    "multi_hop_traversal",
    "expand_context",
    # Queries & Statistics
    "get_node",
    "find_nodes_by_name",
    "find_nodes_by_type",
    "get_repository_entities",
    "get_synthetic_nodes",
    "get_relationships",
    "get_relationships_by_type",
    "get_structural_context",
    "get_statistics",
    # Validation
    "ValidationIssue",
    "ValidationReport",
    "validate_graph",
    "validate_or_raise",
    # Serialization
    "export_json",
    "import_json",
    "export_graphml",
    "import_graphml",
    "DEFAULT_JSON_PATH",
    "DEFAULT_GRAPHML_PATH",
]
