import React from 'react';
import {
  BookOpen,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { getResearchQuestions } from '../../services/api';

export const ResearchView: React.FC = () => {
  const rqs = getResearchQuestions();

  const hypotheses = [
    {
      id: 'H1',
      title: 'Cross-File Multi-Hop Recall',
      text: 'Graph-aware retrieval will improve retrieval recall for questions requiring cross-file and multi-hop structural reasoning compared with semantic-only retrieval.',
      status: 'Ready for Benchmark',
    },
    {
      id: 'H2',
      title: 'Answer Correctness & Completeness',
      text: 'Graph-aware retrieval will improve answer correctness and completeness for structural, dependency, and multi-hop repository questions.',
      status: 'Ready for Benchmark',
    },
    {
      id: 'H3',
      title: 'Complementary Hybrid Signals',
      text: 'Hybrid semantic + graph retrieval will retrieve complementary evidence and may outperform either retrieval mode alone on broad repository QA.',
      status: 'Ready for Benchmark',
    },
    {
      id: 'H4',
      title: 'Provenance & Faithfulness',
      text: 'Provenance-aware graph context will make generated answers more directly traceable to repository evidence and significantly reduce hallucinations.',
      status: 'Baseline Verified',
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-medium bg-[#EBF2EE] text-[#244837] border border-[#C8DBD0] mb-3">
            <BookOpen className="w-3.5 h-3.5 text-[#244837]" />
            <span>Formal Research Protocol & Experimental Design</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-serif-heading font-medium text-[#1C1917]">
            Research Questions & Benchmark Specifications
          </h1>
          <p className="mt-1 text-[13px] text-[#57534E] leading-relaxed">
            ProjectGenome operationalizes research around five formal research questions (RQ1–RQ5) and four
            testable hypotheses (H1–H4), evaluated over a 720-question repository QA benchmark.
          </p>
        </div>
      </section>

      {/* Research Questions List */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <h2 className="text-[15px] font-semibold text-[#1C1917] tracking-tight pb-3 border-b border-[#F0ECE6]">
          Master Research Questions (RQ1–RQ5)
        </h2>

        <div className="mt-4 space-y-4">
          {rqs.map((rq) => (
            <div
              key={rq.id}
              className="p-4 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0] hover:border-[#D5D1C8] transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono-code text-xs px-2 py-0.5 rounded bg-[#244837] text-white font-semibold">
                    {rq.id}
                  </span>
                  <h3 className="font-semibold text-[14px] text-[#1C1917]">
                    {rq.title}
                  </h3>
                </div>

                <span
                  className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono-code border ${
                    rq.status === 'Baseline Verified'
                      ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#166534]'
                      : 'bg-[#F6F5F2] border-[#E5E2DA] text-[#57534E]'
                  }`}
                >
                  <Clock className="w-3 h-3 text-[#78746D]" />
                  <span>{rq.status}</span>
                </span>
              </div>

              <p className="mt-2 text-[13px] text-[#57534E] leading-relaxed">
                {rq.description}
              </p>

              <div className="mt-3 pt-3 border-t border-[#F0ECE6] flex flex-wrap items-center justify-between text-[11px] text-[#78746D] gap-2">
                <div>
                  <span className="font-semibold text-[#1C1917]">Metrics:</span>{' '}
                  {rq.metrics.join(', ')}
                </div>
                <div className="font-mono-code">
                  Target: {rq.target_model}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Hypotheses Grid */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <h2 className="text-[15px] font-semibold text-[#1C1917] tracking-tight pb-3 border-b border-[#F0ECE6]">
          Hypotheses Tracking (H1–H4)
        </h2>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          {hypotheses.map((h) => (
            <div
              key={h.id}
              className="p-4 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0] space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-mono-code text-xs px-2 py-0.5 rounded bg-[#F6F5F2] text-[#244837] font-semibold border border-[#C8DBD0]">
                    {h.id}
                  </span>
                  <span className="font-semibold text-[13px] text-[#1C1917]">
                    {h.title}
                  </span>
                </div>
                <span className="text-[11px] font-mono-code text-[#78746D]">
                  {h.status}
                </span>
              </div>
              <p className="text-[12px] text-[#57534E] leading-relaxed">
                {h.text}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Benchmark Protocol Specifications Card */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <h2 className="text-[15px] font-semibold text-[#1C1917] tracking-tight pb-3 border-b border-[#F0ECE6]">
          Standardized Benchmark Execution Protocol
        </h2>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          <div className="p-4 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0]">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Verified Questions
            </div>
            <div className="mt-1 text-2xl font-serif-heading font-semibold text-[#1C1917]">
              720
            </div>
            <div className="text-[11px] text-[#57534E] mt-1">
              Multi-hop SWE-QA benchmark
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0]">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Total Generations
            </div>
            <div className="mt-1 text-2xl font-serif-heading font-semibold text-[#244837]">
              3,600
            </div>
            <div className="text-[11px] text-[#57534E] mt-1">
              5 retrieval systems × 720 queries
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#FAF8F5] border border-[#EAE7E0]">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[#78746D]">
              Generator Backbone
            </div>
            <div className="mt-1 text-lg font-serif-heading font-semibold text-[#1C1917] truncate">
              Qwen2.5-Coder-7B
            </div>
            <div className="text-[11px] text-[#57534E] mt-1">
              Fixed temperature & context budget
            </div>
          </div>
        </div>

        {/* Reproducibility Audit */}
        <div className="mt-6 pt-4 border-t border-[#F0ECE6] flex flex-col sm:flex-row sm:items-center justify-between text-[12px] text-[#57534E] gap-2">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#244837]" />
            <span className="font-semibold text-[#1C1917]">
              Strict Non-Fabrication Policy:
            </span>
            <span>
              Results published only upon complete benchmark execution.
            </span>
          </div>
          <div className="font-mono-code text-[11px] text-[#78746D]">
            ISO/IEC Research Rigor
          </div>
        </div>
      </section>
    </div>
  );
};
