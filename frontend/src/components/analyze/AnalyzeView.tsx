import React, { useState } from 'react';
import {
  Play,
  CheckCircle2,
  Loader2,
  Copy,
  Download,
  Filter,
} from 'lucide-react';
import type { AnalyzerOutput } from '../../types/genome';
import { triggerRepositoryAnalysis, type SystemStatus } from '../../services/api';

interface AnalyzeViewProps {
  initialData: AnalyzerOutput;
  status: SystemStatus | null;
  onAnalysisUpdated: (data: AnalyzerOutput) => void;
}

export const AnalyzeView: React.FC<AnalyzeViewProps> = ({
  initialData,
  status,
  onAnalysisUpdated,
}) => {
  const [repoPath, setRepoPath] = useState<string>('sample_repo');
  const [includeDerived, setIncludeDerived] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [analysisResult, setAnalysisResult] = useState<AnalyzerOutput>(initialData);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'entities' | 'relationships' | 'raw_json'>('entities');
  const [entityFilter, setEntityFilter] = useState<string>('all');
  const [copied, setCopied] = useState<boolean>(false);

  const steps = [
    'Scanning filesystem layout (directories, files)',
    'Parsing ASTs with Tree-sitter (classes, functions, methods)',
    'Extracting primitive relationships (CONTAINS, IMPORTS, INHERITS, CALLS)',
    'Synthesizing derived DEPENDS_ON cross-file edges',
    'Computing canonical SHA-256 reproducible fingerprint',
  ];

  const handleRunAnalysis = async () => {
    setLoading(true);
    setFeedbackMessage(null);
    setCurrentStep(1);

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 250);

    const res = await triggerRepositoryAnalysis(
      repoPath,
      includeDerived,
      status?.isLiveServer || false
    );

    clearInterval(stepInterval);
    setCurrentStep(5);
    setLoading(false);

    if (res.success) {
      setAnalysisResult(res.data);
      onAnalysisUpdated(res.data);
      setFeedbackMessage(res.message);
    } else {
      setFeedbackMessage(`Error: ${res.message}`);
    }
  };

  const filteredEntities = analysisResult.entities.filter((e) => {
    if (entityFilter === 'all') return true;
    return e.type.toLowerCase() === entityFilter.toLowerCase();
  });

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(analysisResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(analysisResult, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_output_${repoPath.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Execution Controls Card */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-[#F0ECE6] gap-4">
          <div>
            <h1 className="text-xl font-serif-heading font-medium text-[#1C1917]">
              Repository Intelligence · Static Analysis Engine
            </h1>
            <p className="mt-1 text-[13px] text-[#57534E]">
              Extracts deterministic Abstract Syntax Trees, lexical scoping, call graphs, and canonical provenance.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                status?.isLiveServer
                  ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#166534]'
                  : 'bg-[#F6F5F2] border-[#E5E2DA] text-[#57534E]'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  status?.isLiveServer ? 'bg-[#16A34A] animate-pulse' : 'bg-[#78746D]'
                }`}
              />
              <span>
                {status?.isLiveServer ? 'Live Python CLI / Server Connected' : 'Offline Verified Snapshot'}
              </span>
            </span>
          </div>
        </div>

        {/* Path Input & Options Form */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-6 space-y-1.5">
            <label className="block text-[12px] font-semibold text-[#1C1917]">
              Repository Root Directory
            </label>
            <div className="relative">
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="e.g. sample_repo or path/to/repo"
                className="w-full px-3 py-2 text-[13px] font-mono-code bg-[#FBFBFA] border border-[#D5D1C8] focus:border-[#244837] focus:ring-1 focus:ring-[#244837] rounded-md outline-hidden text-[#1C1917]"
              />
            </div>
            <p className="text-[11px] text-[#78746D]">
              Verified sample repo: <code className="font-mono-code bg-[#F6F5F2] px-1 py-0.5 rounded">sample_repo</code>
            </p>
          </div>

          <div className="md:col-span-3 space-y-2">
            <label className="flex items-center space-x-2 text-[13px] text-[#44403C] cursor-pointer">
              <input
                type="checkbox"
                checked={includeDerived}
                onChange={(e) => setIncludeDerived(e.target.checked)}
                className="rounded border-[#D5D1C8] text-[#244837] focus:ring-[#244837] w-4 h-4"
              />
              <span>Derive DEPENDS_ON edges</span>
            </label>
            <div className="text-[11px] text-[#78746D]">
              Multi-factor call + import synthesis
            </div>
          </div>

          <div className="md:col-span-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2 bg-[#244837] hover:bg-[#1B372A] disabled:opacity-50 text-white text-[13px] font-medium rounded-md transition-all shadow-xs cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing AST...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Execute Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Step Progression checklist when analyzing */}
        {loading && (
          <div className="mt-5 p-4 bg-[#FAF9F6] border border-[#EAE7E0] rounded-lg space-y-2">
            <div className="text-[12px] font-semibold text-[#1C1917] mb-2">
              Execution Progress:
            </div>
            {steps.map((s, idx) => (
              <div key={idx} className="flex items-center space-x-2 text-[12px]">
                {currentStep > idx + 1 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#244837]" />
                ) : currentStep === idx + 1 ? (
                  <Loader2 className="w-3.5 h-3.5 text-[#244837] animate-spin" />
                ) : (
                  <span className="w-3.5 h-3.5 rounded-full border border-[#D5D1C8] inline-block" />
                )}
                <span
                  className={
                    currentStep === idx + 1
                      ? 'font-medium text-[#1C1917]'
                      : currentStep > idx + 1
                      ? 'text-[#57534E]'
                      : 'text-[#8C877F]'
                  }
                >
                  {s}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Feedback alert */}
        {feedbackMessage && !loading && (
          <div className="mt-4 p-3 rounded-lg bg-[#EBF2EE] border border-[#C8DBD0] text-[12px] text-[#244837] flex items-center justify-between">
            <span>{feedbackMessage}</span>
            <span className="font-mono-code text-[11px] text-[#3D6B54]">
              Status: 200 OK
            </span>
          </div>
        )}
      </section>

      {/* Results Inspector Card */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl overflow-hidden shadow-2xs">
        {/* Navigation Tabs for Inspector */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[#F0ECE6] bg-[#FAF9F6]">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('entities')}
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                activeTab === 'entities'
                  ? 'bg-white text-[#1C1917] border border-[#D5D1C8] shadow-2xs'
                  : 'text-[#57534E] hover:text-[#1C1917]'
              }`}
            >
              Entities ({analysisResult.entities.length})
            </button>
            <button
              onClick={() => setActiveTab('relationships')}
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                activeTab === 'relationships'
                  ? 'bg-white text-[#1C1917] border border-[#D5D1C8] shadow-2xs'
                  : 'text-[#57534E] hover:text-[#1C1917]'
              }`}
            >
              Relationships ({analysisResult.relationships.length})
            </button>
            <button
              onClick={() => setActiveTab('raw_json')}
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                activeTab === 'raw_json'
                  ? 'bg-white text-[#1C1917] border border-[#D5D1C8] shadow-2xs'
                  : 'text-[#57534E] hover:text-[#1C1917]'
              }`}
            >
              Canonical JSON
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyJson}
              className="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-[#44403C] hover:text-[#1C1917] bg-white border border-[#E5E2DA] rounded transition-colors"
            >
              <Copy className="w-3 h-3 text-[#78746D]" />
              <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
            </button>
            <button
              onClick={handleDownloadJson}
              className="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-[#44403C] hover:text-[#1C1917] bg-white border border-[#E5E2DA] rounded transition-colors"
            >
              <Download className="w-3 h-3 text-[#78746D]" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Entities Table */}
        {activeTab === 'entities' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Filter className="w-3.5 h-3.5 text-[#78746D]" />
                <span className="text-[12px] font-medium text-[#57534E]">Filter by entity type:</span>
                <select
                  value={entityFilter}
                  onChange={(e) => setEntityFilter(e.target.value)}
                  className="text-[12px] bg-[#FBFBFA] border border-[#D5D1C8] rounded px-2 py-1 outline-hidden"
                >
                  <option value="all">All Types ({analysisResult.entities.length})</option>
                  <option value="Repository">Repository</option>
                  <option value="Directory">Directory</option>
                  <option value="File">File</option>
                  <option value="Class">Class</option>
                  <option value="Function">Function</option>
                  <option value="Method">Method</option>
                </select>
              </div>

              <div className="text-[12px] font-mono-code text-[#78746D]">
                Showing {filteredEntities.length} entities
              </div>
            </div>

            <div className="overflow-x-auto border border-[#E8E5DF] rounded-lg">
              <table className="min-w-full divide-y divide-[#E8E5DF] text-[13px]">
                <thead className="bg-[#FAF9F6]">
                  <tr>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Type</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Name</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Path</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Location</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Qualified ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0ECE6] bg-white">
                  {filteredEntities.map((e) => (
                    <tr key={e.id} className="hover:bg-[#FAF9F6] transition-colors">
                      <td className="px-4 py-2 whitespace-nowrap">
                        <span className="inline-block px-2 py-0.5 text-[11px] font-medium rounded-full bg-[#F6F5F2] text-[#1C1917] border border-[#E5E2DA]">
                          {e.type}
                        </span>
                      </td>
                      <td className="px-4 py-2 font-medium text-[#1C1917] whitespace-nowrap">
                        {e.name}
                      </td>
                      <td className="px-4 py-2 font-mono-code text-[12px] text-[#57534E] whitespace-nowrap">
                        {e.path}
                      </td>
                      <td className="px-4 py-2 font-mono-code text-[11px] text-[#78746D] whitespace-nowrap">
                        {e.location ? `L${e.location.start_line}-${e.location.end_line}` : '—'}
                      </td>
                      <td className="px-4 py-2 font-mono-code text-[11px] text-[#78746D] max-w-xs truncate" title={e.id}>
                        {e.id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Relationships Table */}
        {activeTab === 'relationships' && (
          <div className="p-6">
            <div className="overflow-x-auto border border-[#E8E5DF] rounded-lg">
              <table className="min-w-full divide-y divide-[#E8E5DF] text-[13px]">
                <thead className="bg-[#FAF9F6]">
                  <tr>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Type</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Source</th>
                    <th className="px-4 py-2.5 text-center font-semibold text-[#1C1917]"></th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Target</th>
                    <th className="px-4 py-2.5 text-left font-semibold text-[#1C1917]">Status / Properties</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0ECE6] bg-white">
                  {analysisResult.relationships.map((rel) => {
                    const isUnresolved = rel.properties?.resolved === false;
                    return (
                      <tr key={rel.id} className="hover:bg-[#FAF9F6] transition-colors">
                        <td className="px-4 py-2 whitespace-nowrap">
                          <span
                            className={`inline-block px-2 py-0.5 text-[11px] font-medium rounded-full ${
                              rel.type === 'CALLS'
                                ? isUnresolved
                                  ? 'bg-[#FEE2E2] text-[#991B1B]'
                                  : 'bg-[#FEF3C7] text-[#92400E]'
                                : rel.type === 'CONTAINS'
                                ? 'bg-[#F3F4F6] text-[#374151]'
                                : rel.type === 'IMPORTS'
                                ? 'bg-[#DBEAFE] text-[#1E40AF]'
                                : 'bg-[#EDE9FE] text-[#5B21B6]'
                            }`}
                          >
                            {rel.type}
                          </span>
                        </td>
                        <td className="px-4 py-2 font-mono-code text-[11px] text-[#1C1917] max-w-xs truncate" title={rel.source}>
                          {rel.source}
                        </td>
                        <td className="px-4 py-2 text-center text-[#9CA3AF]">
                          →
                        </td>
                        <td className="px-4 py-2 font-mono-code text-[11px] text-[#1C1917] max-w-xs truncate" title={rel.target}>
                          {rel.target}
                        </td>
                        <td className="px-4 py-2 text-[11px] text-[#78746D]">
                          {rel.properties?.raw_call ? (
                            <span>raw_call: {rel.properties.raw_call}</span>
                          ) : rel.properties?.derived ? (
                            <span>weight: {rel.properties.weight}</span>
                          ) : (
                            'primitive'
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Raw Canonical JSON */}
        {activeTab === 'raw_json' && (
          <div className="p-4 bg-[#1C1917] text-[#FAF9F6] font-mono-code text-[12px] overflow-auto max-h-[500px]">
            <pre className="whitespace-pre">{JSON.stringify(analysisResult, null, 2)}</pre>
          </div>
        )}
      </section>
    </div>
  );
};
