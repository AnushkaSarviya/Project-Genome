# ProjectGenome — Master Research & Implementation Plan
## Repository-Level Software Understanding with Knowledge Graph-Aware Retrieval

**Document status:** Master source-of-truth for implementation, research, experimentation, and paper writing  
**Last updated:** 26 September 2026  
**Project name:** ProjectGenome  
**Primary research theme:** Beyond Semantic Retrieval: Knowledge Graph-Aware Retrieval for Repository-Level Software Understanding

---

# 0. READ THIS FIRST — INSTRUCTIONS FOR ANTIGRAVITY

This document is the **current master plan** for ProjectGenome.

Antigravity must treat this document as the operational source of truth for the project unless a later explicit decision is made by the team.

## Non-negotiable principles

1. **Do not redesign the whole project casually.**
   The repository-analysis subsystem is already implemented and tested. Do not replace it with a different architecture unless explicitly instructed.

2. **Do not invent research results.**
   No accuracy, recall, faithfulness, latency, or other numerical result may be written as a result until the corresponding experiment has actually been executed.

3. **Do not claim novelty merely because a Knowledge Graph is used.**
   Existing work already uses code graphs, graph databases, and KG-based repository retrieval. The research contribution must be framed around the controlled evaluation of retrieval strategies for repository-level QA and the specific typed/provenance-aware representation used by ProjectGenome.

4. **Separate implementation from research.**
   A component can be useful for the system without itself being the research contribution.

5. **Keep the experimental comparison fair.**
   When comparing retrieval strategies, use the same repositories, questions, generator model, context/token budget where possible, and evaluation protocol.

6. **Preserve provenance.**
   Retrieved evidence must be traceable to concrete repository entities and source locations.

7. **Do not use an LLM to hallucinate repository structure.**
   Static repository analysis should be deterministic wherever possible. Unresolved calls must remain unresolved rather than being guessed.

8. **Do not silently change the data contract.**
   The JSON emitted by Repository Intelligence is the interface between repository analysis and Knowledge Graph construction.

9. **Do not over-engineer before the first experiment.**
   The priority is to establish an end-to-end experimental pipeline quickly, then improve components based on evidence.

10. **The ultimate goal is a research result, not merely a software demo.**

---

# 1. PROJECT IN ONE PARAGRAPH

ProjectGenome investigates whether a structured Software Knowledge Graph can help an LLM answer questions about an entire software repository more accurately, completely, and faithfully than conventional retrieval approaches.

A repository is first statically analysed to identify files, classes, functions, methods, imports, inheritance relations, and function/method calls. These entities and relationships are converted into a deterministic JSON representation and ingested into a graph database. Retrieval systems then use different combinations of lexical, semantic, structural, and graph-aware signals to select repository context. The selected context is passed to an LLM such as Qwen2.5-Coder, which produces a repository-level answer. The systems are evaluated on repository QA tasks, with retrieval quality and answer quality measured separately.

The central research question is:

> **Does graph-aware retrieval over a Software Knowledge Graph improve repository-level question answering compared with conventional lexical, semantic, and structural retrieval?**

The project is therefore not simply:
"Build a Knowledge Graph of a repository."

It is:
**Build a reliable repository representation and experimentally determine when and how graph-aware retrieval helps an LLM understand software repositories.**

---

# 2. CURRENT PROJECT STATUS

## 2.1 Repository Intelligence — COMPLETE

The Repository Intelligence subsystem has already been implemented.

Current implementation location:

```text
d:\Project Genome\projectgenome\
```

Implemented components:

```text
projectgenome/
├── models/
│   ├── entities.py
│   ├── relationships.py
│   └── schema.py
│
├── scanner/
│   └── repository_scanner.py
│
├── parsers/
│   └── python_parser.py
│
├── extractors/
│   ├── entity_extractor.py
│   └── relationship_extractor.py
│
├── exporters/
│   └── json_exporter.py
│
└── main.py
```

Tests:
11 tests (11 passed)

The implementation includes:
- repository scanning
- directory/file extraction
- Python AST parsing
- class extraction
- function extraction
- method extraction
- lexical scoping
- import extraction
- inheritance extraction
- function/method call extraction
- static call resolution
- unresolved-call representation
- deterministic IDs
- source provenance
- canonical JSON ordering
- SHA-256 canonical hashing
- optional derived dependency relationships
- CLI execution
- end-to-end output generation

## 2.2 End-to-end Repository Analysis — VERIFIED

The sample repository was successfully analysed.

Current observed output:
- Entities: 19
- Relationships: 35
  - CONTAINS: 18
  - IMPORTS: 3
  - INHERITS: 1
  - CALLS: 10
  - DEPENDS_ON: 3
- Resolved CALLS: 3
- Unresolved CALLS: 7

Canonical SHA-256 observed for the sample output:
`1c02c304e2d9f75d5f66d87e83c7e4311919b04def89c6210373202b48176ef8`

This is an implementation checkpoint, not a research result.

## 2.3 Current responsibility boundary

Repository Intelligence is responsible for:
`Repository -> Repository Analysis -> Structured Repository JSON`

The Repository Intelligence module is NOT responsible for:
- Neo4j graph construction
- graph retrieval
- vector retrieval
- LLM generation
- answer evaluation
- final research conclusions

The next major step is therefore integration with the Knowledge Graph and retrieval pipeline.

---

# 3. FINAL RESEARCH DIRECTION

Final working research topic:
**Knowledge Graph-Aware Retrieval for Repository-Level Software Understanding**

Alternative paper-style title:
**Beyond Semantic Retrieval: Knowledge Graph-Aware Retrieval for Repository-Level Software Understanding**

---

# 4. WHAT THE PROJECT IS ACTUALLY TESTING

The project is testing a retrieval hypothesis.

Suppose a user asks:
"Which function ultimately handles the database lookup used by UserService.get_user()?"

A semantic retriever may retrieve code that is semantically similar to "database lookup."

A graph-aware system can reason through explicit relationships:
```text
UserService.get_user()
        |
      CALLS
        ↓
repository.get_user()
        |
      CALLS
        ↓
database.fetch_user()
```

The research question is whether explicit structural information of this type improves repository-level QA.

---

# 5. RESEARCH QUESTIONS

- **RQ1 — Retrieval effectiveness**: Does graph-aware retrieval retrieve more relevant repository context than lexical, semantic, or purely structural retrieval? (Metrics: Recall@K, Precision@K, MRR, nDCG)
- **RQ2 — Answer quality**: Does graph-aware retrieval improve the quality of LLM-generated answers to repository-level questions? (Metrics: correctness/accuracy, completeness, faithfulness)
- **RQ3 — Question-type dependence**: For which categories of repository-level questions does graph-aware retrieval provide the greatest benefit?
- **RQ4 — Hybrid retrieval**: Does combining semantic retrieval with graph-aware retrieval provide complementary benefits compared with either approach alone?
- **RQ5 — Cost / efficiency**: What is the retrieval-quality and answer-quality trade-off of graph-aware retrieval in terms of context size and latency?

---

# 6. HYPOTHESES

- **H1**: Graph-aware retrieval will improve retrieval recall for questions requiring cross-file and multi-hop structural reasoning compared with semantic-only retrieval.
- **H2**: Graph-aware retrieval will improve answer correctness and completeness for structural, dependency, and multi-hop repository questions.
- **H3**: Hybrid semantic + graph retrieval will retrieve complementary evidence and may outperform either retrieval mode alone on broad repository QA.
- **H4**: Provenance-aware graph context will make generated answers more directly traceable to repository evidence and may improve faithfulness.

---

# 7. SYSTEM ARCHITECTURE

```text
                    ┌─────────────────────┐
                    │   Source Repository │
                    │       Git/Python    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Repository          │
                    │ Intelligence        │
                    │                     │
                    │ AST                 │
                    │ Imports             │
                    │ Calls               │
                    │ Classes             │
                    │ Functions           │
                    │ Inheritance         │
                    │ Files/Directories   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Canonical JSON      │
                    │ Repository IR       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Software Knowledge  │
                    │ Graph               │
                    │                     │
                    │ Neo4j               │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
             BM25         Semantic       Structural
             Search       Retrieval      Retrieval
                 │             │             │
                 └─────────────┼─────────────┘
                               │
                         Hybrid Retrieval
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Graph-Aware         │
                    │ Retrieval           │
                    │                     │
                    │ Semantic seed       │
                    │       +             │
                    │ KG traversal        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Context Builder     │
                    │                     │
                    │ Evidence +          │
                    │ provenance +        │
                    │ relationships       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Generation LLM      │
                    │ Qwen2.5-Coder       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Repository-Level    │
                    │ Answer              │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Evaluation          │
                    │                     │
                    │ Retrieval metrics  │
                    │ Answer metrics     │
                    │ Faithfulness       │
                    │ Completeness       │
                    │ Latency            │
                    └─────────────────────┘
```

---

# 8. DATA CONTRACT & SCHEMA RECAP

- **Entities**: Repository, Directory, File (with `module_name`), Class, Function, Method.
- **Relationships**: `CONTAINS` (canonical top-down), `IMPORTS`, `INHERITS`, `CALLS` (resolved + unresolved fallback), and derived `DEPENDS_ON`.
- **IDs**: `type:path:name` (e.g., `class:src/user.py:UserService`, `func:src/a.py:outer.helper`).
- **Provenance**: Line and column range stored for all entities and relationship occurrences.
- **Reproducibility**: Entity and relationship arrays sorted by `id`, metadata timestamp excluded from canonical hash.

---

# 9. EXECUTION ROADMAP & NEXT PHASES

- **Phase 1 — Integration**: JSON validation & Neo4j Knowledge Graph Ingestion.
- **Phase 2 — Code Index**: Code entity chunks & embedding index (CodeBERT / GraphCodeBERT).
- **Phase 3-6 — Retrieval Baselines**: BM25, Semantic, Structural, Hybrid retrieval implementations.
- **Phase 7 — Graph-Aware Retrieval**: Semantic seed + KG traversal + source expansion + filtering.
- **Phase 8-9 — LLM Generation & Evaluation**: Qwen2.5-Coder-7B-Instruct integration + SWE-QA benchmark evaluation (Recall@K, Precision@K, MRR, nDCG, Accuracy, Completeness, Faithfulness).
- **Phase 10 — Paper Writing**: Synthesizing results into empirical paper based strictly on experimental findings.
