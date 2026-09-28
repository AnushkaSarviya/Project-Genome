# ProjectGenome — Software Knowledge Graph Schema Specification

This document defines the schema, node types, relationship types, and metadata contracts for the **ProjectGenome Software Knowledge Graph (KG)**, aligned with Nyasa's Repository Intelligence frozen v2.0 contract.

---

## 1. Graph Representation

The Knowledge Graph is backed by `networkx.MultiDiGraph`:
- **Directed**: Relationships express direction of interaction (e.g. caller $\to$ callee, container $\to$ member).
- **Multi-Edge**: Multiple distinct relationship types can coexist between the same pair of nodes (e.g., `IMPORTS` and `DEPENDS_ON`, or multiple call sites).
- **Deterministic**: Stable identifiers and idempotent ingestion guarantees.

---

## 2. Entity Types (`NodeType`)

The analyzer emits **6 canonical entity types**. An additional **1 synthetic type** is managed internally by the KG for unresolved targets.

| Entity Type | Category | Description | Identifier Example |
| :--- | :--- | :--- | :--- |
| `Repository` | Analyzer | Root repository identity and global config | `repo:sample_repo` |
| `Directory` | Analyzer | File system directory | `dir:models` |
| `File` | Analyzer | Source code file (stores `module_name` in properties) | `file:models/user.py` |
| `Class` | Analyzer | Class definition | `class:models/user.py:User` |
| `Function` | Analyzer | Standalone module-level function | `func:main.py:main` |
| `Method` | Analyzer | Method defined within a class | `method:models/user.py:User.__init__` |
| `UnresolvedReference` | Synthetic KG | Placeholder node for unresolved call targets (e.g. external/dynamic calls) | `unresolved:print` |

### Reconciliation with Analyzer v2.0
1. **No Separate `Module` Nodes**: Python module identity is preserved via the `module_name` property on `File` entities (e.g., `properties.module_name = "models.user"`). The KG builder never instantiates standalone `Module` nodes.
2. **`UnresolvedReference`**: Created only by the KG builder when an unresolved `CALLS` edge target is encountered, preventing dangling edges without polluting repository entity counts.

---

## 3. Relationship Types (`RelationshipType`)

### A. Primitive Structural Relationships (Extracted Facts)
Extracted directly from abstract syntax trees without heuristic inference:

- **`CONTAINS`**: Canonical containment hierarchy:
  $$\text{Repository} \xrightarrow{\text{CONTAINS}} \text{Directory} \xrightarrow{\text{CONTAINS}} \text{File} \xrightarrow{\text{CONTAINS}} \text{Class} \xrightarrow{\text{CONTAINS}} \text{Method}$$
  $$\text{File} \xrightarrow{\text{CONTAINS}} \text{Function}$$
  *(Note: `DEFINED_IN` is deprecated; `CONTAINS` is canonical).*
- **`IMPORTS`**: Inter-file import declarations (e.g. `file:main.py` $\xrightarrow{\text{IMPORTS}}$ `file:services/user_service.py`).
- **`CALLS`**: Direct function or method invocations, including resolved and unresolved call targets.
- **`INHERITS`**: Class inheritance hierarchies (e.g. `User` $\xrightarrow{\text{INHERITS}}$ `BaseModel`).

### B. Derived Relationships (Analyzer Synthesis)
- **`DEPENDS_ON`**: Synthesized by the analyzer across files/modules combining multiple evidence factors (`CALLS`, `IMPORTS`, `INHERITS`).
  - Contains explicit metadata:
    ```json
    {
      "derived": true,
      "reasons": ["CALLS", "IMPORTS"],
      "weight": 2
    }
    ```

---

## 4. Unresolved Call Target Semantics

Unresolved calls occur when external libraries, builtins, or dynamic references are called (e.g. `print`, `service.create_user`).
- **Target Node**: A synthetic node of type `UnresolvedReference` is created.
- **Properties**:
  - `is_synthetic: true`
  - `resolved: false`
  - `raw_call: "<expression>"`
- **Separation**: Queries such as `get_repository_entities()` automatically exclude these placeholders unless `include_synthetic=True` is explicitly passed.

---

## 5. Provenance & Location

Every entity and relationship preserves complete analyzer provenance:
- **`path`**: Normalized relative file path.
- **`location`**: Span coordinates:
  ```json
  {
    "file": "models/user.py",
    "start_line": 4,
    "end_line": 12,
    "start_column": 0,
    "end_column": 35
  }
  ```
- **`properties`**: Preserves all language-specific attributes (`docstring`, `decorators`, `bases`, `parameters`, `return_type`, `is_async`, `size_bytes`, `line_count`).

---

## 6. Serialization Specifications

### JSON Format (`data/generated/repository_graph.json`)
Lossless JSON serialization capturing graph metadata, nodes, properties, and relationships.

### GraphML Format (`data/generated/repository_graph.graphml`)
Deterministic GraphML format suitable for Gephi, NetworkX, and graph analysis tools. Complex nested dicts/lists are deterministically serialized to JSON strings within XML string attributes and parsed back during import.
