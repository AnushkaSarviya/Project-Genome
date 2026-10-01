# ProjectGenome — Knowledge Graph API Contract & Integration Guide

This guide documents the public programming interface of the Software Knowledge Graph module for consumption by the downstream **Semantic Retrieval**, **Context Builder**, and **LLM** evaluation teammates.

---

## 1. Installation & Imports

Import the Knowledge Graph module directly from `src.knowledge_graph`:

```python
from src.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    build_from_analysis,
    expand_context,
    find_nodes_by_name,
    find_nodes_by_type,
    find_path,
    get_callees,
    get_callers,
    get_dependencies,
    get_dependents,
    get_statistics,
    validate_or_raise,
    export_json,
    import_json,
    export_graphml,
    import_graphml,
    NodeType,
    RelationshipType,
)
```

---

## 2. Ingesting Repository Analysis

Ingest analyzer output directly from a file path, dictionary, or `AnalyzerOutput` object:

```python
# Option A: Convenience function
kg = build_from_analysis("data/sample/sample_analysis.json")

# Option B: Builder class
builder = KnowledgeGraphBuilder(strict_duplicates=False)
kg = builder.build(analyzer_dict_or_path)
```

The builder:
1. Validates all inputs against Nyasa's v2.0 contract.
2. Ingests all 6 canonical entity types without creating separate `Module` nodes.
3. Automatically synthesizes clearly marked `UnresolvedReference` placeholder nodes for unresolved calls.
4. Preserves derived `DEPENDS_ON` edges with weights and reasoning tags.

---

## 3. Retrieval & Graph-Aware Context Expansion

This is the primary interface for the **Semantic Retrieval** and **Context Builder** teammates.

When semantic retrieval finds one or more relevant seed entities, use `expand_context` to collect the structural neighborhood:

```python
seed = "method:services/user_service.py:UserService.create_user"

context = expand_context(
    graph=kg,
    seed_ids=seed,
    max_hops=2,
    relationship_types=[
        RelationshipType.CALLS,
        RelationshipType.CONTAINS,
        RelationshipType.DEPENDS_ON,
    ],
    direction="both",
    include_unresolved=False,  # Set to True if unresolved calls are desired
)
```

### Return Payload Structure
```python
{
    "seed_ids": ["method:services/user_service.py:UserService.create_user"],
    "max_hops": 2,
    "nodes": [
        {
            "id": "method:services/user_service.py:UserService.create_user",
            "type": "Method",
            "name": "create_user",
            "path": "services/user_service.py",
            "location": {...},
            "properties": {...}
        },
        {
            "id": "class:models/user.py:User",
            "type": "Class",
            "name": "User",
            ...
        }
    ],
    "edges": [
        {
            "id": "rel:calls:...",
            "source": "method:services/user_service.py:UserService.create_user",
            "target": "class:models/user.py:User",
            "type": "CALLS",
            "properties": {"raw_call": "User", "resolved": True}
        }
    ],
    "hop_distances": {
        "method:services/user_service.py:UserService.create_user": 0,
        "class:models/user.py:User": 1
    }
}
```

---

## 4. Traversal Operations

### Call Graph Exploration
```python
# Callees (functions called by this entity)
callees = get_callees(kg, "func:main.py:main", include_unresolved=False)

# Callers (entities that invoke this entity)
callers = get_callers(kg, "class:services/user_service.py:UserService")
```

### Dependency Tracing
```python
# Direct outgoing dependencies (DEPENDS_ON and IMPORTS)
dependencies = get_dependencies(kg, "file:main.py")

# Direct incoming dependents
dependents = get_dependents(kg, "file:services/user_service.py")
```

### Path Finding
Find shortest structural paths between repository entities:
```python
path = find_path(
    kg,
    source_id="repo:sample_repo",
    target_id="method:models/user.py:User.__init__",
    relationship_types=[RelationshipType.CONTAINS],
)
# Returns: ['repo:sample_repo', 'dir:models', 'file:models/user.py', 'class:models/user.py:User', 'method:models/user.py:User.__init__']
```

---

## 5. High-Level Queries & Statistics

### Searching Entities
```python
# By exact or partial name
users = find_nodes_by_name(kg, "User", node_type=NodeType.CLASS, exact=True)

# By entity type
all_methods = find_nodes_by_type(kg, NodeType.METHOD)
```

### Evaluation Statistics
```python
stats = get_statistics(kg)
print(stats)
# {
#   "total_nodes": 26,
#   "total_edges": 35,
#   "analyzer_entity_count": 19,
#   "synthetic_node_count": 7,
#   "primitive_relationship_count": 32,
#   "derived_relationship_count": 3,
#   "unresolved_calls_count": 7,
#   "entities_by_type": {"Class": 3, "Directory": 2, "File": 6, ...},
#   "relationships_by_type": {"CALLS": 10, "CONTAINS": 16, "DEPENDS_ON": 3, ...}
# }
```

---

## 6. Graph Validation

Verify the integrity of any KnowledgeGraph:
```python
# Raises KnowledgeGraphError if invalid
validate_or_raise(kg)

# Or inspect the report
report = validate_graph(kg)
if not report.is_valid:
    print(report.errors)
```

---

## 7. Serialization

```python
# Export to default or custom paths
export_json(kg, file_path="data/generated/repository_graph.json")
export_graphml(kg, file_path="data/generated/repository_graph.graphml")

# Reload from file
reloaded_kg = import_json("data/generated/repository_graph.json")
```
