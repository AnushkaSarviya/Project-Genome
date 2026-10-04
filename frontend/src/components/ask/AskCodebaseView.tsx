import React, { useState } from 'react';
import {
  Search,
  Sparkles,
  GitBranch,
  FileCode2,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import type { RetrievalStrategy, QAResult } from '../../types/genome';
import { askCodebase, type SystemStatus } from '../../services/api';

interface AskCodebaseViewProps {
  status: SystemStatus | null;
  initialQuery?: string;
}

export const AskCodebaseView: React.FC<AskCodebaseViewProps> = ({
  status,
  initialQuery = '',
}) => {
  const [query, setQuery] = useState(
    initialQuery ||
      'Which function handles the user lookup used by UserService and what does it call?'
  );
  const [strategy, setStrategy] = useState<RetrievalStrategy>('graph_aware');
  const [loading, setLoading] = useState<boolean>(false);
  const [qaResult, setQaResult] = useState<QAResult | null>(null);

  const sampleQuestions = [
    'Which function handles the user lookup used by UserService and what does it call?',
    'What classes inherit from BaseModel in the repository?',
    'Trace the call graph starting from main()',
    'Which external or unresolved functions are called in this codebase?',
  ];

  const handleAsk = async (customQuery?: string) => {
    const q = customQuery || query;
    if (!q.trim()) return;
    setLoading(true);

    try {
      const res = await askCodebase(q, strategy, status?.isLiveServer || false);
      setQaResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Editorial Header */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-medium bg-[#EBF2EE] text-[#244837] border border-[#C8DBD0] mb-3">
            <Sparkles className="w-3.5 h-3.5 text-[#244837]" />
            <span>Repository-Level Question Answering Workspace</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-serif-heading font-medium text-[#1C1917]">
            Ask the Codebase
          </h1>
          <p className="mt-1 text-[13px] text-[#57534E] leading-relaxed">
            Query the codebase via Graph-Aware Retrieval.
          </p>
          <details className="mt-2 text-[12px] text-[#78746D] group">
            <summary className="cursor-pointer font-medium hover:text-[#244837]">How it works</summary>
            <div className="mt-2 pl-3 border-l-2 border-[#EAE7E0] space-y-1">
              <p>Tests different retrieval modes for providing context to <code className="font-mono-code bg-[#F6F5F2] px-1 py-0.5 rounded text-[#244837]">Qwen2.5-Coder-7B-Instruct</code>.</p>
              <p>Graph-aware retrieval resolves cross-file dependencies via structural AST edges.</p>
            </div>
          </details>
        </div>

        {/* Query Input Box */}
        <div className="mt-6 space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#8C877F] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAsk();
                }}
                placeholder="Ask a question about the repository architecture, calls, or inheritance..."
                className="w-full pl-10 pr-4 py-2.5 text-[14px] bg-[#FAF8F5] border border-[#D5D1C8] focus:border-[#244837] focus:ring-1 focus:ring-[#244837] rounded-lg outline-hidden text-[#1C1917]"
              />
            </div>
            <button
              onClick={() => handleAsk()}
              disabled={loading}
              className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-[#244837] hover:bg-[#1B372A] disabled:opacity-50 text-white text-[13px] font-medium rounded-lg transition-all shadow-xs cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Retrieving Context...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Ask Repository</span>
                </>
              )}
            </button>
          </div>

          {/* Strategy Selector Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#F0ECE6]">
            <span className="text-[11px] font-semibold text-[#78746D] uppercase tracking-wider mr-1">
              Retrieval Strategy:
            </span>
            {[
              { id: 'graph_aware', label: 'Graph-Aware (CodeBERT + KG)', badge: 'Recommended' },
              { id: 'hybrid', label: 'Hybrid (BM25 + CodeBERT RRF)' },
              { id: 'semantic', label: 'Semantic (CodeBERT 768d)' },
              { id: 'structural', label: 'Structural (KG AST Only)' },
              { id: 'bm25', label: 'BM25 Lexical' },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setStrategy(st.id as RetrievalStrategy)}
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md text-[12px] font-medium transition-all border ${
                  strategy === st.id
                    ? 'bg-[#244837] text-white border-[#244837] shadow-xs'
                    : 'bg-white text-[#57534E] border-[#D5D1C8] hover:bg-[#F6F5F2]'
                }`}
              >
                <span>{st.label}</span>
                {st.badge && (
                  <span className="text-[9px] font-mono-code px-1 rounded bg-[#EBF2EE] text-[#244837]">
                    {st.badge}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Sample Questions Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] text-[#78746D]">Sample queries:</span>
            {sampleQuestions.map((sq, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(sq);
                  handleAsk(sq);
                }}
                className="text-[11px] font-mono-code px-2 py-0.5 rounded bg-[#FAF8F5] hover:bg-[#F2EFE9] text-[#44403C] border border-[#E5E2DA] transition-colors"
              >
                "{sq.length > 42 ? `${sq.slice(0, 40)}…` : sq}"
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Answer & Evidence Presentation */}
      {qaResult && (
        <section className="space-y-6">
          {/* Formulated Answer Card */}
          <div className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#F0ECE6] gap-2">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#16A34A]" />
                <h3 className="text-base font-serif-heading font-medium text-[#1C1917]">
                  Repository-Level Answer
                </h3>
              </div>

              {/* Attribution and parameters */}
              <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono-code text-[#78746D]">
                <span className="px-2 py-0.5 rounded bg-[#F6F5F2] border border-[#E5E2DA]">
                  Model: {qaResult.generator_model}
                </span>
                <span className="px-2 py-0.5 rounded bg-[#F6F5F2] border border-[#E5E2DA]">
                  Encoder: {qaResult.encoder_model || 'CodeBERT'}
                </span>
                <span className="px-2 py-0.5 rounded bg-[#F6F5F2] border border-[#E5E2DA]">
                  Latency: {qaResult.latency_ms}ms
                </span>
                <span className="px-2 py-0.5 rounded bg-[#EBF2EE] text-[#244837] border border-[#C8DBD0] font-semibold">
                  Confidence: {Math.round(qaResult.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Answer Body */}
            <div className="mt-4 text-[14px] leading-relaxed text-[#1C1917] whitespace-pre-line font-sans">
              {qaResult.answer}
            </div>

            {/* Graph Traversal Breadcrumb Trail if available */}
            {qaResult.graph_path && qaResult.graph_path.length > 0 && (
              <div className="mt-5 p-3 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0]">
                <div className="flex items-center space-x-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#78746D] mb-2">
                  <GitBranch className="w-3.5 h-3.5 text-[#244837]" />
                  <span>KG Traversal Breadcrumb Path</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono-code">
                  {qaResult.graph_path.map((step, idx) => (
                    <React.Fragment key={idx}>
                      <span className="px-2 py-0.5 rounded bg-white text-[#1C1917] border border-[#D5D1C8] shadow-2xs">
                        {step.split(':').pop()}
                      </span>
                      {idx < (qaResult.graph_path?.length || 0) - 1 && (
                        <ChevronRight className="w-3 h-3 text-[#9CA3AF]" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Retrieved Evidence & Source Code Grounding */}
          <div className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
            <div className="flex items-center justify-between pb-4 border-b border-[#F0ECE6]">
              <div className="flex items-center space-x-2">
                <FileCode2 className="w-4 h-4 text-[#244837]" />
                <h3 className="text-base font-semibold text-[#1C1917]">
                  Retrieved Code Evidence & Provenance
                </h3>
              </div>
              <span className="text-[12px] font-mono-code text-[#78746D]">
                {qaResult.evidence.length} chunks ({qaResult.context_tokens} tokens)
              </span>
            </div>

            <div className="mt-4 space-y-4">
              {qaResult.evidence.map((ev, index) => (
                <div
                  key={ev.id || index}
                  className="border border-[#E8E5DF] rounded-lg overflow-hidden bg-[#FAF8F5]"
                >
                  {/* Chunk Header */}
                  <div className="px-4 py-2.5 bg-white border-b border-[#E8E5DF] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono-code text-[11px] px-2 py-0.5 rounded bg-[#F6F5F2] font-semibold text-[#1C1917] border border-[#E5E2DA]">
                        {ev.type}
                      </span>
                      <span className="font-semibold text-[13px] text-[#1C1917]">
                        {ev.name}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] font-mono-code text-[#78746D]">
                      <span>{ev.provenance}</span>
                      <span className="px-1.5 py-0.5 rounded bg-[#EBF2EE] text-[#244837] font-semibold">
                        Score: {ev.score.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Retrieval Reason */}
                  <div className="px-4 py-2 text-[12px] text-[#57534E] bg-[#FAF9F6] border-b border-[#EAE7E0]">
                    <span className="font-semibold text-[#1C1917]">Why retrieved:</span>{' '}
                    {ev.explanation}
                  </div>

                  {/* Code Snippet */}
                  <div className="p-4 bg-[#1C1917] text-[#FAF9F6] font-mono-code text-[12px] overflow-x-auto">
                    <pre className="whitespace-pre">{ev.source_snippet}</pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
