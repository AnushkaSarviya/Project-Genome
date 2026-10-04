export type NodeType =
  | 'Repository'
  | 'Directory'
  | 'File'
  | 'Class'
  | 'Function'
  | 'Method'
  | 'UnresolvedReference';

export type RelationshipType =
  | 'CONTAINS'
  | 'IMPORTS'
  | 'CALLS'
  | 'INHERITS'
  | 'DEPENDS_ON';

export interface LocationSpan {
  file: string;
  start_line: number;
  end_line: number;
  start_column: number;
  end_column: number;
}

export interface EntityProperties {
  qualified_name?: string;
  docstring?: string | null;
  decorators?: string[];
  bases?: string[];
  parameters?: string[];
  return_type?: string | null;
  is_async?: boolean;
  size_bytes?: number;
  line_count?: number;
  module_name?: string;
  language?: string;
  abs_path?: string;
  [key: string]: unknown;
}

export interface EntityNode {
  id: string;
  type: NodeType;
  name: string;
  path: string;
  location: LocationSpan | null;
  properties: EntityProperties;
  is_synthetic?: boolean;
  resolved?: boolean;
}

export interface RelationshipProperties {
  raw_call?: string;
  resolved?: boolean;
  confidence?: string;
  derived?: boolean;
  reasons?: string[];
  weight?: number;
  [key: string]: unknown;
}

export interface RelationshipEdge {
  id: string;
  source: string;
  target: string;
  type: RelationshipType;
  location?: LocationSpan | null;
  properties?: RelationshipProperties;
}

export interface RepositoryMetadata {
  repository_identity: string;
  root_path: string;
  extracted_at: string;
  analyzer_version: string;
  stats: {
    total_entities: number;
    total_relationships: number;
    primitive_relationships: number;
    derived_relationships: number;
    unresolved_calls_count: number;
  };
}

export interface GraphData {
  version: string;
  metadata: RepositoryMetadata;
  nodes: EntityNode[];
  edges: RelationshipEdge[];
}

export interface AnalyzerOutput {
  version: string;
  metadata: RepositoryMetadata;
  entities: EntityNode[];
  relationships: RelationshipEdge[];
}

export type RetrievalStrategy =
  | 'bm25'
  | 'semantic'
  | 'structural'
  | 'hybrid'
  | 'graph_aware';

export interface RetrievalEvidence {
  id: string;
  entity_id: string;
  type: NodeType;
  name: string;
  file_path: string;
  location?: LocationSpan | null;
  score: number;
  source_snippet: string;
  explanation: string;
  provenance: string;
  hops_from_seed?: number;
}

export interface QAResult {
  id: string;
  query: string;
  strategy: RetrievalStrategy;
  answer: string;
  confidence: number;
  generator_model: string;
  encoder_model?: string;
  latency_ms: number;
  context_tokens: number;
  evidence: RetrievalEvidence[];
  graph_path?: string[];
  is_verified_checkpoint?: boolean;
}

export interface RetrievalComparisonMetric {
  strategy: RetrievalStrategy;
  strategy_name: string;
  description: string;
  primary_mechanism: string;
  strengths: string[];
  failure_modes: string[];
  token_budget_avg: number;
  latency_avg_ms: number;
  recall_at_5: number | null;
  mrr: number | null;
  faithfulness_score: number | null;
  tested_status: 'completed' | 'in_progress' | 'planned';
}

export interface ResearchQuestionStatus {
  id: string;
  title: string;
  description: string;
  metrics: string[];
  status: 'Ready for Benchmark' | 'Baseline Verified' | 'Awaiting Model Run';
  target_model: string;
}
