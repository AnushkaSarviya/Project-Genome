import React, { useState, useMemo } from 'react';
import {
  Search,
  X,
  Sparkles,
  Network,
} from 'lucide-react';
import type { GraphData, EntityNode, NodeType, RelationshipType } from '../../types/genome';
import { NODE_STYLES, REL_STYLES } from '../../utils/theme';
import { GraphCanvas } from './GraphCanvas';
import { clientSideExpandContext } from '../../services/api';

interface GraphExplorerViewProps {
  graphData: GraphData;
  onNavigateToAsk?: (initialQuery: string) => void;
  onUpdateNode?: (node: EntityNode) => void;
}

export const GraphExplorerView: React.FC<GraphExplorerViewProps> = ({
  graphData,
  onNavigateToAsk,
  onUpdateNode,
}) => {
  const [layoutMode, setLayoutMode] = useState<'hierarchical' | 'force'>('hierarchical');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<EntityNode | null>(null);
  
  const [isEditingNode, setIsEditingNode] = useState(false);
  const [editNodeName, setEditNodeName] = useState('');
  const [editNodeDocstring, setEditNodeDocstring] = useState('');

  // Filter states
  const allNodeTypes: NodeType[] = [
    'Repository',
    'Directory',
    'File',
    'Class',
    'Function',
    'Method',
    'UnresolvedReference',
  ];

  const allRelTypes: RelationshipType[] = [
    'CONTAINS',
    'IMPORTS',
    'CALLS',
    'INHERITS',
    'DEPENDS_ON',
  ];

  const [visibleNodeTypes, setVisibleNodeTypes] = useState<Set<NodeType>>(
    new Set(allNodeTypes)
  );

  const [visibleRelTypes, setVisibleRelTypes] = useState<Set<RelationshipType>>(
    new Set(allRelTypes)
  );

  // Neighborhood expansion state
  const [expandedHopLevel, setExpandedHopLevel] = useState<number | null>(null);
  const [expandedNeighborhood, setExpandedNeighborhood] = useState<Set<string> | null>(null);

  // Toggle node type visibility
  const toggleNodeType = (type: NodeType) => {
    setVisibleNodeTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  // Toggle rel type visibility
  const toggleRelType = (type: RelationshipType) => {
    setVisibleRelTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  // Node count per type
  const nodeCounts = useMemo(() => {
    return (graphData.nodes || []).reduce((acc, n) => {
      acc[n.type] = (acc[n.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [graphData.nodes]);

  // Edges count per rel type
  const edgeCounts = useMemo(() => {
    return (graphData.edges || []).reduce((acc, e) => {
      acc[e.type] = (acc[e.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [graphData.edges]);

  const unresolvedEdgesCount = useMemo(() => {
    const nodeIds = new Set((graphData.nodes || []).map(n => n.id));
    return (graphData.edges || []).filter(e => !nodeIds.has(e.source) || !nodeIds.has(e.target)).length;
  }, [graphData.nodes, graphData.edges]);

  // Context expansion handler
  const handleExpandContext = (hops: number) => {
    if (!selectedNode) return;
    setExpandedHopLevel(hops);
    const expansion = clientSideExpandContext(
      graphData,
      [selectedNode.id],
      hops,
      Array.from(visibleRelTypes)
    );
    const nodeIds = new Set(expansion.nodes.map((n) => n.id));
    setExpandedNeighborhood(nodeIds);
  };

  const handleClearExpansion = () => {
    setExpandedHopLevel(null);
    setExpandedNeighborhood(null);
  };

  // Inspect incoming & outgoing relationships for selected node
  const nodeConnections = useMemo(() => {
    if (!selectedNode) return { incoming: [], outgoing: [] };
    const incoming = (graphData.edges || []).filter((e) => e.target === selectedNode.id);
    const outgoing = (graphData.edges || []).filter((e) => e.source === selectedNode.id);
    return { incoming, outgoing };
  }, [selectedNode, graphData.edges]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Controls Bar */}
      <section className="bg-white border border-[#E8E5DF] rounded-xl p-4 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Search box with auto suggestions */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-[#8C877F] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search entity by name or qualified ID (e.g. UserService, get_user)..."
              className="w-full pl-9 pr-3 py-1.5 text-[13px] bg-[#FAF8F5] border border-[#D5D1C8] focus:border-[#244837] focus:ring-1 focus:ring-[#244837] rounded-md outline-hidden text-[#1C1917]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-[#8C877F] hover:text-[#1C1917]"
              >
                ✕
              </button>
            )}
          </div>

          {/* Layout Mode & Reset Controls */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center bg-[#F6F5F2] border border-[#E5E2DA] rounded-lg p-0.5">
              <button
                onClick={() => setLayoutMode('hierarchical')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  layoutMode === 'hierarchical'
                    ? 'bg-white text-[#1C1917] shadow-2xs font-semibold'
                    : 'text-[#57534E] hover:text-[#1C1917]'
                }`}
              >
                Hierarchical
              </button>
              <button
                onClick={() => setLayoutMode('force')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  layoutMode === 'force'
                    ? 'bg-white text-[#1C1917] shadow-2xs font-semibold'
                    : 'text-[#57534E] hover:text-[#1C1917]'
                }`}
              >
                Force Layout
              </button>
            </div>

            <button
              onClick={() => {
                setVisibleNodeTypes(new Set(allNodeTypes));
                setVisibleRelTypes(new Set(allRelTypes));
                setSelectedNode(null);
                handleClearExpansion();
                setSearchQuery('');
              }}
              className="px-2.5 py-1 text-xs font-medium text-[#57534E] hover:text-[#1C1917] bg-white border border-[#E5E2DA] rounded-md transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Filter Pills Bar */}
        <div className="mt-3 pt-3 border-t border-[#F0ECE6] flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-medium text-[#78746D] uppercase tracking-wider mr-1">
            Node Types:
          </span>
          {allNodeTypes.map((type) => {
            const isVisible = visibleNodeTypes.has(type);
            const style = NODE_STYLES[type];
            return (
              <button
                key={type}
                onClick={() => toggleNodeType(type)}
                className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all border ${
                  isVisible
                    ? 'bg-white border-[#D5D1C8] text-[#1C1917] shadow-2xs'
                    : 'bg-[#F6F5F2] border-transparent text-[#8C877F] line-through'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: style.color }}
                />
                <span>{style.label}</span>
                <span className="text-[10px] font-mono-code text-[#78746D]">
                  ({nodeCounts[type] || 0})
                </span>
              </button>
            );
          })}
        </div>

        {/* Relationship Filters */}
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-medium text-[#78746D] uppercase tracking-wider mr-1">
            Edges:
          </span>
          {allRelTypes.map((relType) => {
            const isVisible = visibleRelTypes.has(relType);
            const style = REL_STYLES[relType];
            return (
              <button
                key={relType}
                onClick={() => toggleRelType(relType)}
                className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border ${
                  isVisible
                    ? 'bg-white border-[#D5D1C8] text-[#1C1917] shadow-2xs'
                    : 'bg-[#F6F5F2] border-transparent text-[#8C877F] line-through'
                }`}
              >
                <span
                  className="w-2 h-0.5"
                  style={{ backgroundColor: style.color }}
                />
                <span>{relType}</span>
                <span className="text-[10px] font-mono-code text-[#78746D]">
                  ({edgeCounts[relType] || 0})
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Main Graph & Inspector Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Graph Canvas Column */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          {unresolvedEdgesCount > 0 && (
            <div className="p-2 bg-[#FFF8E1] border border-[#FDE68A] text-[#92400E] text-[12px] font-medium rounded-lg flex items-center shadow-xs">
              <span className="mr-2">⚠️</span>
              <span>
                <strong>Diagnostic Warning:</strong> {unresolvedEdgesCount} edges reference missing nodes and have been safely ignored by the graph renderer.
              </span>
            </div>
          )}
          <div className="relative">
            {(!graphData.edges || graphData.edges.length === 0) && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/80 backdrop-blur-xs rounded-xl border border-[#E8E5DF]">
                <div className="bg-white p-6 rounded-xl border border-[#E8E5DF] shadow-sm max-w-md text-center">
                  <div className="w-12 h-12 bg-[#F6F5F2] rounded-full flex items-center justify-center mx-auto mb-4">
                    <Network className="w-6 h-6 text-[#8C877F]" />
                  </div>
                  <h3 className="text-lg font-semibold text-[#1C1917] mb-2">No Relationships Found</h3>
                  <p className="text-[13px] text-[#57534E] leading-relaxed">
                    The current graph data contains <strong>{graphData.nodes?.length || 0} entities</strong> but <strong>0 edges</strong>. 
                    This could mean the imported JSON lacks relationship data, or the repository analysis did not detect any structural dependencies.
                  </p>
                </div>
              </div>
            )}
            <GraphCanvas
              graphData={graphData}
              layoutMode={layoutMode}
              visibleNodeTypes={visibleNodeTypes}
              visibleRelTypes={visibleRelTypes}
              selectedNodeId={selectedNode ? selectedNode.id : null}
              onSelectNode={(node) => {
                setSelectedNode(node);
                setIsEditingNode(false);
                if (expandedHopLevel) handleClearExpansion();
              }}
              highlightedNodeIds={expandedNeighborhood || undefined}
              searchQuery={searchQuery}
            />
          </div>
        </div>

        {/* Contextual Inspector Panel */}
        <div className="lg:col-span-4 bg-white border border-[#E8E5DF] rounded-xl p-5 shadow-2xs">
          {selectedNode ? (
            <div className="space-y-4">
              {/* Header with Type Badge & Close Button */}
              <div className="flex items-start justify-between pb-3 border-b border-[#F0ECE6]">
                <div className="flex-1 mr-4">
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className="inline-block px-2 py-0.5 text-[11px] font-semibold rounded-full border"
                      style={{
                        backgroundColor: NODE_STYLES[selectedNode.type]?.badgeBg,
                        color: NODE_STYLES[selectedNode.type]?.badgeText,
                        borderColor: NODE_STYLES[selectedNode.type]?.color + '40',
                      }}
                    >
                      {selectedNode.type}
                    </span>
                    {!isEditingNode && onUpdateNode && (
                      <button
                        onClick={() => {
                          setEditNodeName(selectedNode.name);
                          setEditNodeDocstring(selectedNode.properties.docstring || '');
                          setIsEditingNode(true);
                        }}
                        className="text-[11px] font-medium text-[#57534E] hover:text-[#244837] underline"
                      >
                        Edit
                      </button>
                    )}
                  </div>
                  {isEditingNode ? (
                    <input
                      type="text"
                      value={editNodeName}
                      onChange={(e) => setEditNodeName(e.target.value)}
                      className="w-full px-2 py-1 text-sm bg-white border border-[#D5D1C8] focus:border-[#244837] focus:ring-1 focus:ring-[#244837] rounded outline-hidden font-semibold text-[#1C1917]"
                    />
                  ) : (
                    <h3 className="text-base font-semibold text-[#1C1917] tracking-tight">
                      {selectedNode.name}
                    </h3>
                  )}
                </div>

                <button
                  onClick={() => {
                    setSelectedNode(null);
                    setIsEditingNode(false);
                    handleClearExpansion();
                  }}
                  className="p-1 text-[#8C877F] hover:text-[#1C1917] rounded hover:bg-[#F6F5F2]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Qualified ID & File Coordinates */}
              <div className="space-y-1.5 bg-[#FAF8F5] p-3 rounded-lg border border-[#EAE7E0]">
                <div className="text-[11px] font-mono-code text-[#78746D] truncate" title={selectedNode.id}>
                  <span className="font-semibold text-[#1C1917]">ID:</span> {selectedNode.id}
                </div>
                {selectedNode.path && (
                  <div className="text-[11px] font-mono-code text-[#57534E]">
                    <span className="font-semibold text-[#1C1917]">File:</span> {selectedNode.path}
                    {selectedNode.location && (
                      <span className="text-[#244837] ml-1">
                        (L{selectedNode.location.start_line}–{selectedNode.location.end_line})
                      </span>
                    )}
                  </div>
                )}
                {selectedNode.properties.qualified_name && (
                  <div className="text-[11px] font-mono-code text-[#57534E]">
                    <span className="font-semibold text-[#1C1917]">Qualified:</span>{' '}
                    {selectedNode.properties.qualified_name}
                  </div>
                )}
              </div>

              {/* Docstring */}
              {(selectedNode.properties.docstring || isEditingNode) && (
                <div>
                  <div className="text-[11px] font-semibold text-[#78746D] uppercase tracking-wider mb-1">
                    Docstring
                  </div>
                  {isEditingNode ? (
                    <textarea
                      value={editNodeDocstring}
                      onChange={(e) => setEditNodeDocstring(e.target.value)}
                      rows={3}
                      className="w-full text-[12px] p-2 bg-white border border-[#D5D1C8] focus:border-[#244837] focus:ring-1 focus:ring-[#244837] rounded outline-hidden text-[#1C1917]"
                      placeholder="Add docstring..."
                    />
                  ) : (
                    <div className="text-[12px] italic text-[#44403C] bg-[#FAF8F5] p-2.5 rounded border border-[#EAE7E0]">
                      "{selectedNode.properties.docstring}"
                    </div>
                  )}
                </div>
              )}

              {isEditingNode && (
                <div className="flex space-x-2 pt-2">
                  <button
                    onClick={() => {
                      if (!onUpdateNode) return;
                      const updated = {
                        ...selectedNode,
                        name: editNodeName,
                        properties: {
                          ...selectedNode.properties,
                          docstring: editNodeDocstring || null
                        }
                      };
                      onUpdateNode(updated);
                      setSelectedNode(updated);
                      setIsEditingNode(false);
                    }}
                    className="flex-1 bg-[#244837] hover:bg-[#1B372A] text-white py-1.5 rounded text-xs font-medium transition-colors"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => setIsEditingNode(false)}
                    className="flex-1 bg-white hover:bg-[#F6F5F2] text-[#57534E] border border-[#D5D1C8] py-1.5 rounded text-xs font-medium transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {/* AST Attributes */}
              {selectedNode.properties.bases && selectedNode.properties.bases.length > 0 && (
                <div>
                  <div className="text-[11px] font-semibold text-[#78746D] uppercase tracking-wider mb-1">
                    Inherits From (Bases)
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.properties.bases.map((b) => (
                      <span
                        key={b}
                        className="px-2 py-0.5 rounded text-[11px] font-mono-code bg-[#EDE9FE] text-[#5B21B6] border border-[#DDD6FE]"
                      >
                        {b}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedNode.properties.parameters && selectedNode.properties.parameters.length > 0 && (
                <div>
                  <div className="text-[11px] font-semibold text-[#78746D] uppercase tracking-wider mb-1">
                    Parameters
                  </div>
                  <div className="font-mono-code text-[11px] text-[#244837] bg-[#F6F5F2] px-2 py-1 rounded">
                    ({selectedNode.properties.parameters.join(', ')})
                  </div>
                </div>
              )}

              {/* Multi-Hop Traversal Controls */}
              <div className="pt-2 border-t border-[#F0ECE6]">
                <div className="text-[11px] font-semibold text-[#1C1917] mb-2 flex items-center justify-between">
                  <span>Graph-Aware Context Expansion</span>
                  {expandedHopLevel && (
                    <button
                      onClick={handleClearExpansion}
                      className="text-[10px] text-[#991B1B] hover:underline"
                    >
                      Clear ({expandedNeighborhood?.size} nodes)
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleExpandContext(1)}
                    className={`px-2.5 py-1.5 text-xs font-medium rounded border transition-colors ${
                      expandedHopLevel === 1
                        ? 'bg-[#244837] text-white border-[#244837]'
                        : 'bg-white text-[#1C1917] border-[#D5D1C8] hover:bg-[#F6F5F2]'
                    }`}
                  >
                    1-Hop Neighbors
                  </button>
                  <button
                    onClick={() => handleExpandContext(2)}
                    className={`px-2.5 py-1.5 text-xs font-medium rounded border transition-colors ${
                      expandedHopLevel === 2
                        ? 'bg-[#244837] text-white border-[#244837]'
                        : 'bg-white text-[#1C1917] border-[#D5D1C8] hover:bg-[#F6F5F2]'
                    }`}
                  >
                    2-Hop Neighborhood
                  </button>
                </div>
              </div>

              {/* Incoming / Outgoing edges list */}
              <div className="space-y-3 pt-2 border-t border-[#F0ECE6] text-[12px]">
                {nodeConnections.outgoing.length > 0 && (
                  <div>
                    <div className="font-semibold text-[#78746D] text-[11px] uppercase tracking-wider mb-1">
                      Outgoing Relationships ({nodeConnections.outgoing.length})
                    </div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {nodeConnections.outgoing.map((e) => (
                        <div
                          key={e.id}
                          className="flex items-center justify-between p-1.5 rounded bg-[#FAF8F5] border border-[#EAE7E0] text-[11px]"
                        >
                          <span className="font-semibold text-[#1C1917]">{e.type}</span>
                          <span className="font-mono-code text-[#78746D] truncate max-w-[140px]" title={e.target}>
                            {e.target.split(':').pop()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {nodeConnections.incoming.length > 0 && (
                  <div>
                    <div className="font-semibold text-[#78746D] text-[11px] uppercase tracking-wider mb-1">
                      Incoming Relationships ({nodeConnections.incoming.length})
                    </div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {nodeConnections.incoming.map((e) => (
                        <div
                          key={e.id}
                          className="flex items-center justify-between p-1.5 rounded bg-[#FAF8F5] border border-[#EAE7E0] text-[11px]"
                        >
                          <span className="font-semibold text-[#1C1917]">{e.type}</span>
                          <span className="font-mono-code text-[#78746D] truncate max-w-[140px]" title={e.source}>
                            {e.source.split(':').pop()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Ask Question About Entity Button */}
              {onNavigateToAsk && (
                <div className="pt-3 border-t border-[#F0ECE6]">
                  <button
                    onClick={() =>
                      onNavigateToAsk(`What does ${selectedNode.name} do and what does it call?`)
                    }
                    className="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-2 bg-[#F6F5F2] hover:bg-[#ECE9E2] text-[#1C1917] border border-[#E5E2DA] rounded-lg text-xs font-medium transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#244837]" />
                    <span>Query in Ask Codebase</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-10 px-4 space-y-3">
              <div className="w-10 h-10 rounded-full bg-[#F6F5F2] text-[#78746D] mx-auto flex items-center justify-center">
                <Network className="w-5 h-5" />
              </div>
              <h4 className="text-[14px] font-semibold text-[#1C1917]">
                Entity Inspector
              </h4>
              <p className="text-[12px] text-[#57534E] leading-relaxed">
                Click any node on the graph canvas to inspect its AST properties, source provenance, call targets, and multi-hop neighborhood.
              </p>
              <div className="pt-2 text-[11px] font-mono-code text-[#78746D] bg-[#FAF8F5] p-2.5 rounded border border-[#EAE7E0]">
                Tip: You can pan by dragging the canvas and zoom with the scroll wheel or controls.
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
