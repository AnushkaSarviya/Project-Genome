import React, { useState, useEffect } from 'react';
import { Header, type TabKey } from './components/layout/Header';
import { OverviewView } from './components/overview/OverviewView';
import { AnalyzeView } from './components/analyze/AnalyzeView';
import { GraphExplorerView } from './components/graph/GraphExplorerView';
import { AskCodebaseView } from './components/ask/AskCodebaseView';
import { RetrievalComparisonView } from './components/comparison/RetrievalComparisonView';
import { ResearchView } from './components/research/ResearchView';
import { ImportModal } from './components/modals/ImportModal';

import type { GraphData, AnalyzerOutput } from './types/genome';
import {
  checkServerHealth,
  fetchSystemStatus,
  loadGraphData,
  loadAnalysisData,
  type SystemStatus,
} from './services/api';

import defaultGraphJson from './data/repository_graph.json';
import defaultAnalysisJson from './data/sample_analysis.json';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({
    version: (defaultGraphJson as any).version || '1.0.0',
    metadata: (defaultGraphJson as any).metadata,
    nodes: (defaultGraphJson as any).nodes || (defaultGraphJson as any).entities || [],
    edges: (defaultGraphJson as any).edges || (defaultGraphJson as any).relationships || [],
  });
  const [analysisData, setAnalysisData] = useState<AnalyzerOutput>(defaultAnalysisJson as unknown as AnalyzerOutput);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [askPreQuery, setAskPreQuery] = useState<string>('');

  // Initial load and live engine detection
  useEffect(() => {
    let isMounted = true;

    async function init() {
      const isLive = await checkServerHealth();
      const sysStatus = await fetchSystemStatus(isLive);
      if (!isMounted) return;
      setStatus(sysStatus);

      if (isLive) {
        const g = await loadGraphData(true);
        const a = await loadAnalysisData(true);
        if (isMounted) {
          setGraphData(g);
          setAnalysisData(a);
        }
      }
    }

    init();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleNavigateToAsk = (initialQuery: string) => {
    setAskPreQuery(initialQuery);
    setActiveTab('ask');
  };

  return (
    <div className="min-h-screen bg-[#FBFBFA] flex flex-col font-sans text-[#1C1917]">
      {/* Top Refined Header */}
      <Header
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        status={status}
        onUploadClick={() => setIsImportModalOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">
        {activeTab === 'overview' && (
          <OverviewView
            graphData={graphData}
            status={status}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'analyze' && (
          <AnalyzeView
            initialData={analysisData}
            status={status}
            onAnalysisUpdated={(newData) => {
              setAnalysisData(newData);
              // Also sync into graph data representation
              setGraphData({
                version: newData.version,
                metadata: newData.metadata,
                nodes: newData.entities,
                edges: newData.relationships,
              });
            }}
          />
        )}

        {activeTab === 'graph' && (
          <GraphExplorerView
            graphData={graphData}
            onNavigateToAsk={handleNavigateToAsk}
            onUpdateNode={(updatedNode) => {
              setGraphData(prev => ({
                ...prev,
                nodes: (prev.nodes || []).map(n => n.id === updatedNode.id ? updatedNode : n)
              }));
              setAnalysisData(prev => ({
                ...prev,
                entities: (prev.entities || []).map(e => e.id === updatedNode.id ? updatedNode : e)
              }));
            }}
          />
        )}

        {activeTab === 'ask' && (
          <AskCodebaseView
            status={status}
            initialQuery={askPreQuery}
          />
        )}

        {activeTab === 'comparison' && <RetrievalComparisonView />}

        {activeTab === 'research' && <ResearchView />}
      </main>

      {/* Refined Footer */}
      <footer className="border-t border-[#E8E5DF] bg-[#FAF8F5] py-8 text-xs text-[#78746D]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-[#1C1917]">ProjectGenome</span>
            {' '}— Knowledge Graph-Aware Retrieval for Repository-Level Software Understanding.
          </div>
          <div className="flex items-center space-x-4 font-mono-code text-[11px]">
            <span>SHA-256: 7079956f...</span>
            <span>·</span>
            <span>NetworkX + CodeBERT + Qwen2.5</span>
          </div>
        </div>
      </footer>

      {/* JSON Import Modal */}
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportGraph={(data) => setGraphData(data)}
        onImportAnalysis={(data) => setAnalysisData(data)}
      />
    </div>
  );
};

export default App;
