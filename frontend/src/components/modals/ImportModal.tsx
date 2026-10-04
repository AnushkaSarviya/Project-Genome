import React, { useState, useRef } from 'react';
import { Upload, X, CheckCircle2, AlertCircle, FileText, RotateCcw } from 'lucide-react';
import type { GraphData, AnalyzerOutput } from '../../types/genome';
import defaultGraphJson from '../../data/repository_graph.json';
import defaultAnalysisJson from '../../data/sample_analysis.json';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportGraph: (data: GraphData) => void;
  onImportAnalysis: (data: AnalyzerOutput) => void;
}

export const ImportModal: React.FC<ImportModalProps> = ({
  isOpen,
  onClose,
  onImportGraph,
  onImportAnalysis,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileProcess = (file: File) => {
    setError(null);
    setSuccess(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsed = JSON.parse(content);

        // Check if it's a Graph JSON (has nodes and edges)
        if (parsed.nodes && parsed.edges) {
          onImportGraph(parsed as GraphData);
          setSuccess(`Successfully loaded Knowledge Graph: ${parsed.nodes.length} nodes, ${parsed.edges.length} edges.`);
          setTimeout(onClose, 1200);
          return;
        }

        // Check if it's an Analyzer Output JSON (has entities and relationships)
        if (parsed.entities && parsed.relationships) {
          onImportAnalysis(parsed as AnalyzerOutput);

          // Also construct GraphData representation
          const graphRepresentation: GraphData = {
            version: parsed.version || '1.0.0',
            metadata: parsed.metadata,
            nodes: parsed.entities,
            edges: parsed.relationships,
          };
          onImportGraph(graphRepresentation);

          setSuccess(`Successfully loaded Analyzer Output: ${parsed.entities.length} entities, ${parsed.relationships.length} relationships.`);
          setTimeout(onClose, 1200);
          return;
        }

        setError('Invalid schema: file must contain either {nodes, edges} or {entities, relationships}.');
      } catch (err) {
        setError(`Failed to parse JSON: ${String(err)}`);
      }
    };
    reader.readAsText(file);
  };

  const handleResetToDefault = () => {
    onImportGraph(defaultGraphJson as unknown as GraphData);
    onImportAnalysis(defaultAnalysisJson as unknown as AnalyzerOutput);
    setSuccess('Restored default verified sample_repo dataset.');
    setTimeout(onClose, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xs">
      <div className="bg-white rounded-xl border border-[#E8E5DF] shadow-xl max-w-lg w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#F0ECE6]">
          <div className="flex items-center space-x-2">
            <Upload className="w-4 h-4 text-[#244837]" />
            <h3 className="text-base font-semibold text-[#1C1917]">
              Import Repository Analysis JSON
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-[#8C877F] hover:text-[#1C1917] rounded hover:bg-[#F6F5F2]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-[13px] text-[#57534E]">
          Load any custom output from <code className="font-mono-code text-[11px] bg-[#F6F5F2] px-1 py-0.5 rounded">projectgenome.main</code> or{' '}
          <code className="font-mono-code text-[11px] bg-[#F6F5F2] px-1 py-0.5 rounded">export_json()</code>.
        </p>

        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            if (e.dataTransfer.files?.[0]) {
              handleFileProcess(e.dataTransfer.files[0]);
            }
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            dragActive
              ? 'border-[#244837] bg-[#EBF2EE]'
              : 'border-[#D5D1C8] hover:border-[#244837] bg-[#FAF8F5]'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={(e) => {
              if (e.target.files?.[0]) handleFileProcess(e.target.files[0]);
            }}
            className="hidden"
          />
          <FileText className="w-8 h-8 text-[#78746D] mx-auto mb-2" />
          <div className="text-[13px] font-medium text-[#1C1917]">
            Click to upload or drag & drop JSON
          </div>
          <div className="text-[11px] text-[#78746D] mt-1">
            Accepts <code className="font-mono-code">analysis_output.json</code> or <code className="font-mono-code">repository_graph.json</code>
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-[12px] text-[#991B1B] bg-[#FEE2E2] p-2.5 rounded-lg border border-[#FECACA]">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="flex items-center space-x-2 text-[12px] text-[#166534] bg-[#F0FDF4] p-2.5 rounded-lg border border-[#BBF7D0]">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        <div className="pt-2 flex items-center justify-between">
          <button
            onClick={handleResetToDefault}
            className="inline-flex items-center space-x-1.5 text-xs text-[#57534E] hover:text-[#1C1917] hover:underline"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to default sample_repo</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-[#57534E] hover:text-[#1C1917] bg-[#F6F5F2] hover:bg-[#EAE7E0] rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
