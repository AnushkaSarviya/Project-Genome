import React from 'react';
import {
  Network,
  Cpu,
  FileCode2,
  GitBranch,
  Search,
  SlidersHorizontal,
  BookOpen,
  Upload,
  CheckCircle2,
} from 'lucide-react';
import type { SystemStatus } from '../../services/api';

export type TabKey =
  | 'overview'
  | 'analyze'
  | 'graph'
  | 'ask'
  | 'comparison'
  | 'research';

interface HeaderProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  status: SystemStatus | null;
  onUploadClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  status,
  onUploadClick,
}) => {
  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { key: 'analyze', label: 'Analyze Repository', icon: <FileCode2 className="w-3.5 h-3.5" /> },
    { key: 'graph', label: 'Knowledge Graph', icon: <Network className="w-3.5 h-3.5" /> },
    { key: 'ask', label: 'Ask Codebase', icon: <Search className="w-3.5 h-3.5" /> },
    { key: 'comparison', label: 'Retrieval Comparison', icon: <SlidersHorizontal className="w-3.5 h-3.5" /> },
    { key: 'research', label: 'Research & Benchmarks', icon: <GitBranch className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#FBFBFA]/95 backdrop-blur-sm border-b border-[#E8E5DF]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Project Identity */}
          <div className="flex items-center space-x-3.5">
            <div className="w-8 h-8 rounded-md bg-[#244837] flex items-center justify-center text-white shadow-xs">
              <Cpu className="w-4.5 h-4.5 stroke-[1.75]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-[15px] tracking-tight text-[#1C1917]">
                  ProjectGenome
                </span>
                <span className="font-mono-code text-[11px] px-1.5 py-0.5 rounded bg-[#EBF2EE] text-[#244837] font-medium border border-[#C8DBD0]">
                  v0.1.0-research
                </span>
              </div>
              <p className="text-[11px] text-[#78746D] hidden sm:block">
                Repository Understanding · Knowledge Graph-Aware Retrieval
              </p>
            </div>
          </div>

          {/* Engine Connectivity Status & Ingest Trigger */}
          <div className="flex items-center space-x-2.5">
            {status && (
              <div
                className="flex items-center space-x-2 px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors"
                style={{
                  backgroundColor: status.isLiveServer ? '#F0FDF4' : '#F6F5F2',
                  borderColor: status.isLiveServer ? '#BBF7D0' : '#E5E2DA',
                  color: status.isLiveServer ? '#166534' : '#57534E',
                }}
                title={
                  status.isLiveServer
                    ? 'Connected to local FastAPI engine at localhost:8000'
                    : 'Running in offline mode using verified repository IR snapshot'
                }
              >
                {status.isLiveServer ? (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] animate-pulse" />
                    <span>Live Python Engine</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3 h-3 text-[#244837]" />
                    <span>Verified Snapshot: {status.repositoryIdentity.replace('repo:', '')}</span>
                  </>
                )}
              </div>
            )}

            <button
              onClick={onUploadClick}
              className="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-[#44403C] hover:text-[#1C1917] bg-white hover:bg-[#F2EFE9] border border-[#E5E2DA] rounded-md transition-colors shadow-2xs"
              title="Load custom analysis_output.json or repository_graph.json"
            >
              <Upload className="w-3 h-3 text-[#78746D]" />
              <span className="hidden md:inline">Import JSON</span>
            </button>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto -mb-px pb-0 scrollbar-none" aria-label="Tabs">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onTabChange(tab.key)}
                className={`group inline-flex items-center space-x-2 py-2.5 px-3 border-b-2 font-medium text-[13px] whitespace-nowrap transition-all ${
                  isActive
                    ? 'border-[#244837] text-[#1C1917] font-semibold'
                    : 'border-transparent text-[#6B665E] hover:text-[#1C1917] hover:border-[#D5D1C8]'
                }`}
              >
                <span
                  className={`transition-colors ${
                    isActive ? 'text-[#244837]' : 'text-[#8C877F] group-hover:text-[#4A4844]'
                  }`}
                >
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
