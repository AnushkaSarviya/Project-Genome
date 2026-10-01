"""Schema definitions for ProjectGenome Software Knowledge Graph.

Compatible with Nyasa's Repository Intelligence frozen v2.0 contract.
"""

from enum import Enum


class NodeType(str, Enum):
    """Entity types in the Software Knowledge Graph.

    Canonical repository entities emitted by the analyzer:
    - REPOSITORY, DIRECTORY, FILE, CLASS, FUNCTION, METHOD.

    Backward compatibility:
    - MODULE: Kept for backward compatibility; in v2.0, module_name is stored
      as a property on File entities rather than as a separate node.

    Synthetic KG-internal types:
    - UNRESOLVED_REFERENCE: Dedicated type for KG-generated placeholder nodes
      representing unresolved call targets (e.g. unresolved:print).
    """

    REPOSITORY = "Repository"
    DIRECTORY = "Directory"
    FILE = "File"
    MODULE = "Module"  # Backward compatibility; analyzer stores module_name on File
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    UNRESOLVED_REFERENCE = "UnresolvedReference"  # KG-internal synthetic placeholder


class RelationshipType(str, Enum):
    """Relationship types in the Software Knowledge Graph.

    Primitive extracted relationships:
    - CONTAINS: Canonical hierarchical containment (Repo -> Dir -> File -> Class -> Method).
    - IMPORTS: Inter-file dependency imports.
    - CALLS: Function/method invocation (including unresolved calls).
    - INHERITS: Class inheritance hierarchy.

    Derived relationships:
    - DEPENDS_ON: Multi-factor repository dependencies derived by analyzer.

    Backward compatibility:
    - DEFINED_IN: Kept for backward compatibility; CONTAINS is canonical.
    """

    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    DEFINED_IN = "DEFINED_IN"  # Backward compatibility; CONTAINS is canonical
    DEPENDS_ON = "DEPENDS_ON"


# Canonical entity types produced by Nyasa's v2.0 analyzer
ANALYZER_ENTITY_TYPES: frozenset[NodeType] = frozenset({
    NodeType.REPOSITORY,
    NodeType.DIRECTORY,
    NodeType.FILE,
    NodeType.CLASS,
    NodeType.FUNCTION,
    NodeType.METHOD,
})

# Primitive structural relationships extracted directly from code
PRIMITIVE_RELATIONSHIP_TYPES: frozenset[RelationshipType] = frozenset({
    RelationshipType.CONTAINS,
    RelationshipType.IMPORTS,
    RelationshipType.CALLS,
    RelationshipType.INHERITS,
})

# Derived relationships synthesized by the analyzer
DERIVED_RELATIONSHIP_TYPES: frozenset[RelationshipType] = frozenset({
    RelationshipType.DEPENDS_ON,
})
