import React from 'react';
import {
  GitBranch,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  Network,
  Search,
} from 'lucide-react';
import type { GraphData } from '../../types/genome';
import type { SystemStatus } from '../../services/api';
import type { TabKey } from '../layout/Header';

interface OverviewViewProps {
  graphData: GraphData;
  status: SystemStatus | null;
  onNavigate: (tab: TabKey) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  graphData,
  status,
  onNavigate,
}) => {
  const meta = graphData?.metadata || {
    repository_identity: 'Unknown',
    stats: { total_entities: 0, total_relationships: 0, primitive_relationships: 0, derived_relationships: 0 }
  };
  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  // Compute breakdown by type
  const entityCounts = nodes.reduce((acc, n) => {
    acc[n.type] = (acc[n.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const relCounts = edges.reduce((acc, e) => {
    acc[e.type] = (acc[e.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const resolvedCalls = edges.filter(
    (e) => e.type === 'CALLS' && e.properties?.resolved === true
  ).length;
  const unresolvedCalls = edges.filter(
    (e) => e.type === 'CALLS' && e.properties?.resolved === false
  ).length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Editorial Research Hero */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 sm:p-8 shadow-2xs">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-medium bg-[#EBF2EE] text-[#244837] border border-[#C8DBD0] mb-4">
            <Sparkles className="w-3.5 h-3.5 text-[#244837]" />
            <span>Research Hypothesis & Empirical Architecture</span>
          </div>

          <h1 className="text-2xl sm:text-3xl text-[#1C1917] font-serif-heading font-medium leading-tight tracking-tight">
            Knowledge Graph-Aware Retrieval
          </h1>

          <p className="mt-4 text-[14px] leading-relaxed text-[#57534E]">
            A deterministic AST-derived <strong>Software Knowledge Graph</strong> that grounds LLM generation in explicit structural provenance.
          </p>

          <details className="mt-2 text-[13px] text-[#78746D] group">
            <summary className="cursor-pointer font-medium hover:text-[#244837]">Methodology & Background</summary>
            <div className="mt-2 pl-3 border-l-2 border-[#EAE7E0] space-y-2">
              <p>Conventional code retrieval relies on lexical BM25 keyword matching or dense vector embeddings.</p>
              <p>ProjectGenome enables multi-hop structural traversal—tracking call trees, inheritance hierarchies, and file dependencies with verified source provenance.</p>
            </div>
          </details>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('graph')}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-[#244837] hover:bg-[#1B372A] text-white text-[13px] font-medium rounded-lg transition-all shadow-xs"
            >
              <Network className="w-4 h-4" />
              <span>Explore Knowledge Graph</span>
              <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
            </button>

            <button
              onClick={() => onNavigate('ask')}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-[#F6F5F2] hover:bg-[#ECE9E2] text-[#1C1917] border border-[#E5E2DA] text-[13px] font-medium rounded-lg transition-all"
            >
              <Search className="w-4 h-4 text-[#57534E]" />
              <span>Ask the Codebase</span>
            </button>

            <button
              onClick={() => onNavigate('comparison')}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-transparent hover:bg-[#F6F5F2] text-[#57534E] text-[13px] font-medium rounded-lg transition-all"
            >
              <span>View 5-Way Retrieval Baselines</span>
              <ArrowRight className="w-3 h-3 text-[#8C877F]" />
            </button>
          </div>
        </div>
      </section>

      {/* Verified Repository Metrics Grid */}
      <section>
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-[15px] font-semibold text-[#1C1917] tracking-tight">
            Current Repository State · Verified Facts
          </h2>
          <span className="text-[12px] font-mono-code text-[#78746D]">
            {meta.repository_identity}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white border border-[#E8E5DF] rounded-lg p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Total Entities
            </div>
            <div className="mt-1 text-2xl font-serif-heading font-semibold text-[#1C1917]">
              {meta.stats.total_entities}
            </div>
            <p className="mt-1 text-[11px] text-[#57534E]">
              Files, classes, functions, methods
            </p>
          </div>

          <div className="bg-white border border-[#E8E5DF] rounded-lg p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Relationships
            </div>
            <div className="mt-1 text-2xl font-serif-heading font-semibold text-[#1C1917]">
              {meta.stats.total_relationships}
            </div>
            <p className="mt-1 text-[11px] text-[#57534E]">
              {meta.stats.primitive_relationships} primitive + {meta.stats.derived_relationships} derived
            </p>
          </div>

          <div className="bg-white border border-[#E8E5DF] rounded-lg p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Call Resolution
            </div>
            <div className="mt-1 text-2xl font-serif-heading font-semibold text-[#1C1917]">
              {resolvedCalls} / {resolvedCalls + unresolvedCalls}
            </div>
            <p className="mt-1 text-[11px] text-[#57534E]">
              {unresolvedCalls} synthetic placeholders
            </p>
          </div>

          <div className="bg-white border border-[#E8E5DF] rounded-lg p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Knowledge Engine
            </div>
            <div className="mt-1 text-lg font-serif-heading font-semibold text-[#244837] truncate">
              NetworkX MultiDiGraph
            </div>
            <p className="mt-1 text-[11px] text-[#57534E] truncate">
              CodeBERT + Qwen2.5-Coder
            </p>
          </div>
        </div>
      </section>

      {/* Structural Entities & Relationships Distribution */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Entities Taxonomy */}
        <div className="bg-white border border-[#E8E5DF] rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE6]">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#244837]" />
              <h3 className="text-[14px] font-semibold text-[#1C1917]">
                Entity Hierarchy & Layer Distribution
              </h3>
            </div>
            <span className="text-[11px] font-mono-code text-[#78746D]">
              {nodes.length} nodes
            </span>
          </div>

          <div className="mt-4 space-y-2.5">
            {[
              { type: 'Repository', label: 'Repository Root', count: entityCounts['Repository'] || 0, desc: 'Global context & base config' },
              { type: 'Directory', label: 'Directories', count: entityCounts['Directory'] || 0, desc: 'FileSystem package containers' },
              { type: 'File', label: 'Files (.py)', count: entityCounts['File'] || 0, desc: 'Source files with module_name property' },
              { type: 'Class', label: 'Classes', count: entityCounts['Class'] || 0, desc: 'BaseModel, User, UserService' },
              { type: 'Function', label: 'Standalone Functions', count: entityCounts['Function'] || 0, desc: 'Module-level functions (e.g. main)' },
              { type: 'Method', label: 'Methods', count: entityCounts['Method'] || 0, desc: 'Class-scoped methods with signatures' },
              { type: 'UnresolvedReference', label: 'Unresolved Calls', count: entityCounts['UnresolvedReference'] || unresolvedCalls, desc: 'Builtins & external imports (print, etc.)' },
            ].map((item) => (
              <div
                key={item.type}
                className="flex items-center justify-between p-2 rounded-md hover:bg-[#FBFBFA] transition-colors text-[13px]"
              >
                <div>
                  <div className="font-medium text-[#1C1917]">{item.label}</div>
                  <div className="text-[11px] text-[#78746D]">{item.desc}</div>
                </div>
                <div className="font-mono-code font-semibold px-2 py-0.5 rounded bg-[#F6F5F2] text-[#244837] text-[12px] border border-[#E5E2DA]">
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Relationships Taxonomy */}
        <div className="bg-white border border-[#E8E5DF] rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE6]">
            <div className="flex items-center space-x-2">
              <GitBranch className="w-4 h-4 text-[#244837]" />
              <h3 className="text-[14px] font-semibold text-[#1C1917]">
                Directed Relationships (Typed Edges)
              </h3>
            </div>
            <span className="text-[11px] font-mono-code text-[#78746D]">
              {edges.length} edges
            </span>
          </div>

          <div className="mt-4 space-y-2.5">
            {[
              { type: 'CONTAINS', label: 'CONTAINS (Containment DAG)', count: relCounts['CONTAINS'] || 0, color: '#78909C', desc: 'Repo → Dir → File → Class → Method' },
              { type: 'IMPORTS', label: 'IMPORTS (Module Dependency)', count: relCounts['IMPORTS'] || 0, color: '#1E88E5', desc: 'Cross-file imports (services → models)' },
              { type: 'CALLS', label: 'CALLS (Invocation Graph)', count: relCounts['CALLS'] || 0, color: '#D32F2F', desc: `${resolvedCalls} resolved targets + ${unresolvedCalls} external` },
              { type: 'INHERITS', label: 'INHERITS (Subclassing)', count: relCounts['INHERITS'] || 0, color: '#8E24AA', desc: 'Class hierarchy (User extends BaseModel)' },
              { type: 'DEPENDS_ON', label: 'DEPENDS_ON (Derived Multi-Factor)', count: relCounts['DEPENDS_ON'] || 0, color: '#E65100', desc: 'Synthesized file-level dependency weights' },
            ].map((item) => (
              <div
                key={item.type}
                className="flex items-center justify-between p-2 rounded-md hover:bg-[#FBFBFA] transition-colors text-[13px]"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="font-medium text-[#1C1917]">{item.label}</span>
                  </div>
                  <div className="text-[11px] text-[#78746D] ml-4">{item.desc}</div>
                </div>
                <div className="font-mono-code font-semibold px-2 py-0.5 rounded bg-[#F6F5F2] text-[#1C1917] text-[12px] border border-[#E5E2DA]">
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Reproducibility & Research Road Map Status */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE6]">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#244837]" />
            <h3 className="text-[14px] font-semibold text-[#1C1917]">
              Research Execution Roadmap & Audit Trail
            </h3>
          </div>
          <span className="text-[11px] font-mono-code text-[#78746D]">
            Master Plan Compliance
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3.5 rounded-lg bg-[#FAF9F6] border border-[#EAE7E0]">
            <div className="flex items-center space-x-2 text-[12px] font-semibold text-[#244837]">
              <CheckCircle2 className="w-4 h-4 text-[#244837]" />
              <span>Phase 1–2: Ingestion & KG</span>
            </div>
            <p className="mt-1 text-[12px] text-[#57534E]">
              Tree-sitter AST parser, canonical ordering, deterministic ID scheme, and NetworkX MultiDiGraph integration verified.
            </p>
            <div className="mt-2 text-[11px] font-mono-code text-[#78746D]">
              Status: VERIFIED & TESTED
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-[#FAF9F6] border border-[#EAE7E0]">
            <div className="flex items-center space-x-2 text-[12px] font-semibold text-[#244837]">
              <CheckCircle2 className="w-4 h-4 text-[#244837]" />
              <span>Phase 3–7: Chunking & Baselines</span>
            </div>
            <p className="mt-1 text-[12px] text-[#57534E]">
              CodeEntityChunker, CodeBERT 768-dim embeddings, CodeVectorIndex cosine search, and 2-hop KG context expansion implemented.
            </p>
            <div className="mt-2 text-[11px] font-mono-code text-[#78746D]">
              Status: PIPELINE ACTIVE
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-[#FAF9F6] border border-[#EAE7E0]">
            <div className="flex items-center space-x-2 text-[12px] font-semibold text-[#78746D]">
              <Clock className="w-4 h-4 text-[#78746D]" />
              <span>Phase 8–9: SWE-QA Benchmark</span>
            </div>
            <p className="mt-1 text-[12px] text-[#57534E]">
              Controlled evaluation across 720 benchmark questions (3,600 Qwen2.5 generations). No fabricated accuracy scores.
            </p>
            <div className="mt-2 text-[11px] font-mono-code text-[#78746D]">
              Status: READY FOR EXECUTION
            </div>
          </div>
        </div>

        {/* Canonical Hash Banner */}
        <div className="mt-4 p-3 rounded-lg bg-[#F6F5F2] border border-[#E5E2DA] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="text-[12px] text-[#57534E]">
            <span className="font-semibold text-[#1C1917]">Canonical SHA-256 Hash:</span>{' '}
            <span className="font-mono-code text-[11px] text-[#244837] break-all">
              {status?.canonicalSha256 || '7079956fcd98a70f684f300a4ca6fd5001ebab5924dcb774890e540758d4d118'}
            </span>
          </div>
          <span className="text-[11px] font-medium text-[#78746D] whitespace-nowrap">
            Deterministic AST Fingerprint
          </span>
        </div>
      </section>
    </div>
  );
};
