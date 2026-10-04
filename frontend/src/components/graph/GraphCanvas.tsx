import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import type { GraphData, EntityNode, NodeType, RelationshipType } from '../../types/genome';
import { NODE_STYLES, REL_STYLES } from '../../utils/theme';

interface GraphCanvasProps {
  graphData: GraphData;
  layoutMode: 'hierarchical' | 'force';
  visibleNodeTypes: Set<NodeType>;
  visibleRelTypes: Set<RelationshipType>;
  selectedNodeId: string | null;
  onSelectNode: (node: EntityNode | null) => void;
  highlightedNodeIds?: Set<string>;
  searchQuery?: string;
}

interface NodePosition {
  x: number;
  y: number;
  vx?: number;
  vy?: number;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  graphData,
  layoutMode,
  visibleNodeTypes,
  visibleRelTypes,
  selectedNodeId,
  onSelectNode,
  highlightedNodeIds,
  searchQuery = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });
  const [transform, setTransform] = useState({ x: 450, y: 80, scale: 0.85 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Resize listener
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 900,
          height: containerRef.current.clientHeight || 600,
        });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Filter nodes & edges based on visibility settings
  const filteredNodes = useMemo(() => {
    return (graphData?.nodes || []).filter((n) => visibleNodeTypes.has(n.type));
  }, [graphData?.nodes, visibleNodeTypes]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, EntityNode>();
    filteredNodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [filteredNodes]);

  const filteredEdges = useMemo(() => {
    return (graphData?.edges || []).filter((e) => {
      if (!visibleRelTypes.has(e.type)) return false;
      return nodeMap.has(e.source) && nodeMap.has(e.target);
    });
  }, [graphData.edges, visibleRelTypes, nodeMap]);

  // Compute Layout Positions (Hierarchical vs Force)
  const positions = useMemo<Record<string, NodePosition>>(() => {
    const pos: Record<string, NodePosition> = {};
    if (filteredNodes.length === 0) return pos;

    if (layoutMode === 'hierarchical') {
      // Direct implementation of hierarchical architectural layer assignment
      // from src/visualization/graph_visualizer.py
      const typeLayers: Record<NodeType, number> = {
        Repository: 0,
        Directory: 1,
        File: 2,
        Class: 3,
        Function: 3,
        Method: 4,
        UnresolvedReference: 5,
      };

      const layers: Record<number, string[]> = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [] };

      filteredNodes.forEach((n) => {
        const layer = n.is_synthetic ? 5 : typeLayers[n.type] ?? 2;
        if (!layers[layer]) layers[layer] = [];
        layers[layer].push(n.id);
      });

      const verticalSpacing = 110;
      const horizontalSpacing = 130;

      Object.entries(layers).forEach(([layerStr, nodeIds]) => {
        const layer = parseInt(layerStr, 10);
        const count = nodeIds.length;
        const totalWidth = (count - 1) * horizontalSpacing;
        const startX = -totalWidth / 2;

        nodeIds.forEach((id, i) => {
          pos[id] = {
            x: startX + i * horizontalSpacing,
            y: layer * verticalSpacing,
          };
        });
      });

      return pos;
    }

    // Force simulation initial radial layout
    const radius = Math.min(dimensions.width, dimensions.height) * 0.38;
    const angleStep = (2 * Math.PI) / Math.max(1, filteredNodes.length);

    filteredNodes.forEach((n, i) => {
      const angle = i * angleStep;
      pos[n.id] = {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
      };
    });

    return pos;
  }, [filteredNodes, layoutMode, dimensions]);

  // User drag overrides
  const [draggedPositions, setDraggedPositions] = useState<Record<string, { x: number; y: number }>>({});

  const nodePositions = useMemo(() => {
    const combined: Record<string, NodePosition> = { ...positions };
    Object.entries(draggedPositions).forEach(([id, override]) => {
      if (combined[id]) {
        combined[id] = { x: override.x, y: override.y };
      }
    });
    return combined;
  }, [positions, draggedPositions]);

  // Center on node if search query matches
  const centerOnNodeId = useCallback(
    (id: string) => {
      const targetPos = nodePositions[id];
      if (targetPos) {
        setTransform((prev) => ({
          ...prev,
          x: dimensions.width / 2 - targetPos.x * prev.scale,
          y: dimensions.height / 2 - targetPos.y * prev.scale,
        }));
      }
    },
    [nodePositions, dimensions]
  );

  useEffect(() => {
    if (!searchQuery.trim()) return;
    const matches = filteredNodes.filter(
      (n) =>
        n.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.id.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (matches.length === 1) {
      const timer = setTimeout(() => {
        centerOnNodeId(matches[0].id);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [searchQuery, filteredNodes, centerOnNodeId]);

  // Mouse wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform((prev) => {
      const newScale = Math.min(Math.max(prev.scale * zoomFactor, 0.25), 3.0);
      return { ...prev, scale: newScale };
    });
  };

  // Canvas Pan Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === containerRef.current || (e.target as HTMLElement).tagName === 'svg') {
      setIsPanning(true);
      setPanStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      }));
    } else if (draggedNodeId && nodePositions[draggedNodeId]) {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const mouseX = (e.clientX - rect.left - transform.x) / transform.scale;
      const mouseY = (e.clientY - rect.top - transform.y) / transform.scale;

      setDraggedPositions((prev) => ({
        ...prev,
        [draggedNodeId]: { x: mouseX, y: mouseY },
      }));
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggedNodeId(null);
  };

  const handleResetZoom = useCallback(() => {
    setTransform({
      x: dimensions.width / 2,
      y: layoutMode === 'hierarchical' ? 80 : dimensions.height / 2,
      scale: 0.85,
    });
  }, [dimensions, layoutMode]);

  return (
    <div
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      className="relative w-full h-[600px] bg-[#FAF8F5] border border-[#E8E5DF] rounded-xl overflow-hidden select-none cursor-grab active:cursor-grabbing"
    >
      {/* Background Architectural Grid Pattern */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none opacity-40"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#D5D1C8" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-dots)" />
      </svg>

      {/* Floating Canvas Controls */}
      <div className="absolute top-3 left-3 z-10 flex items-center space-x-1 bg-white/90 backdrop-blur-xs border border-[#E5E2DA] rounded-lg p-1 shadow-2xs">
        <button
          onClick={() =>
            setTransform((p) => ({ ...p, scale: Math.min(p.scale * 1.2, 3.0) }))
          }
          className="w-7 h-7 flex items-center justify-center text-xs font-semibold text-[#57534E] hover:text-[#1C1917] hover:bg-[#F2EFE9] rounded"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={() =>
            setTransform((p) => ({ ...p, scale: Math.max(p.scale * 0.8, 0.25) }))
          }
          className="w-7 h-7 flex items-center justify-center text-xs font-semibold text-[#57534E] hover:text-[#1C1917] hover:bg-[#F2EFE9] rounded"
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={handleResetZoom}
          className="px-2 h-7 flex items-center justify-center text-[11px] font-medium text-[#57534E] hover:text-[#1C1917] hover:bg-[#F2EFE9] rounded"
          title="Reset View"
        >
          Reset
        </button>
      </div>

      {/* Scale & Nodes count indicator */}
      <div className="absolute bottom-3 left-3 z-10 bg-white/90 backdrop-blur-xs border border-[#E5E2DA] rounded-md px-2.5 py-1 text-[11px] font-mono-code text-[#78746D] shadow-2xs">
        <span>{filteredNodes.length} nodes · {filteredEdges.length} edges · {Math.round(transform.scale * 100)}%</span>
      </div>

      {/* SVG Rendering Layer */}
      <svg
        className="w-full h-full"
        style={{ cursor: isPanning ? 'grabbing' : 'default' }}
      >
        <defs>
          {/* Arrow markers for directed edges */}
          {Object.entries(REL_STYLES).map(([relType, style]) => (
            <marker
              key={relType}
              id={`arrow-${relType}`}
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill={style.color} />
            </marker>
          ))}
        </defs>

        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
          {/* Render Directed Edges */}
          {filteredEdges.map((edge) => {
            const srcPos = nodePositions[edge.source];
            const tgtPos = nodePositions[edge.target];
            if (!srcPos || !tgtPos) return null;

            const isSelected =
              selectedNodeId === edge.source || selectedNodeId === edge.target;
            const isHovered =
              hoveredNodeId === edge.source || hoveredNodeId === edge.target;
            const relStyle = REL_STYLES[edge.type] || REL_STYLES.CONTAINS;

            const isHighlighted =
              highlightedNodeIds &&
              (highlightedNodeIds.has(edge.source) || highlightedNodeIds.has(edge.target));

            const opacity =
              selectedNodeId || hoveredNodeId || highlightedNodeIds
                ? isSelected || isHovered || isHighlighted
                  ? 1.0
                  : 0.15
                : 0.75;

            // Draw clean curved arc for invocation/imports
            const dx = tgtPos.x - srcPos.x;
            const dy = tgtPos.y - srcPos.y;
            const dr = Math.sqrt(dx * dx + dy * dy);
            const isCurved = edge.type === 'CALLS' || edge.type === 'INHERITS';
            const pathData = isCurved
              ? `M ${srcPos.x} ${srcPos.y} A ${dr * 1.2} ${dr * 1.2} 0 0,1 ${tgtPos.x} ${tgtPos.y}`
              : `M ${srcPos.x} ${srcPos.y} L ${tgtPos.x} ${tgtPos.y}`;

            return (
              <g key={edge.id} className="transition-opacity duration-150">
                <path
                  d={pathData}
                  fill="none"
                  stroke={relStyle.color}
                  strokeWidth={isSelected ? relStyle.width * 1.5 : relStyle.width}
                  strokeDasharray={relStyle.dash}
                  markerEnd={`url(#arrow-${edge.type})`}
                  opacity={opacity}
                />
              </g>
            );
          })}

          {/* Render Nodes */}
          {filteredNodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const isSelected = selectedNodeId === node.id;
            const isHovered = hoveredNodeId === node.id;
            const isHighlighted = highlightedNodeIds?.has(node.id);
            const style = NODE_STYLES[node.type] || NODE_STYLES.File;

            const isDimmed =
              (selectedNodeId && !isSelected && !highlightedNodeIds?.has(node.id)) ||
              (hoveredNodeId && !isHovered && hoveredNodeId !== node.id);

            // Shape rendering
            const renderShape = () => {
              if (style.shape === 'square') {
                return (
                  <rect
                    x={-16}
                    y={-16}
                    width={32}
                    height={32}
                    rx={6}
                    fill={isSelected ? style.border : style.color}
                    stroke={isSelected ? '#1C1917' : style.border}
                    strokeWidth={isSelected ? 3 : 1.5}
                    className="shadow-sm"
                  />
                );
              }
              if (style.shape === 'triangle') {
                return (
                  <polygon
                    points="0,-18 18,14 -18,14"
                    fill={isSelected ? style.border : style.color}
                    stroke={isSelected ? '#1C1917' : style.border}
                    strokeWidth={isSelected ? 3 : 1.5}
                  />
                );
              }
              if (style.shape === 'diamond') {
                return (
                  <polygon
                    points="0,-18 16,0 0,18 -16,0"
                    fill={isSelected ? style.border : style.color}
                    stroke={isSelected ? '#1C1917' : style.border}
                    strokeWidth={isSelected ? 3 : 1.5}
                    strokeDasharray="3 3"
                  />
                );
              }
              // Circle
              return (
                <circle
                  r={node.type === 'Repository' ? 22 : node.type === 'Directory' ? 18 : 14}
                  fill={isSelected ? style.border : style.color}
                  stroke={isSelected ? '#1C1917' : style.border}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
              );
            };

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onMouseDown={(e) => {
                  e.stopPropagation();
                  setDraggedNodeId(node.id);
                  onSelectNode(node);
                }}
                className="cursor-pointer transition-opacity duration-150"
                opacity={isDimmed ? 0.25 : 1}
              >
                {/* Active Selection Ring */}
                {isSelected && (
                  <circle
                    r={28}
                    fill="none"
                    stroke="#244837"
                    strokeWidth={2}
                    strokeDasharray="4 2"
                    className="animate-spin-slow"
                  />
                )}

                {/* Highlight Badge */}
                {isHighlighted && !isSelected && (
                  <circle
                    r={24}
                    fill="none"
                    stroke="#D97706"
                    strokeWidth={2}
                  />
                )}

                {renderShape()}

                {/* Node Label Text */}
                <text
                  y={node.type === 'Repository' ? 34 : 26}
                  textAnchor="middle"
                  className="font-medium text-[11px] pointer-events-none fill-[#1C1917]"
                  style={{
                    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
                    fontWeight: isSelected ? 700 : 500,
                  }}
                >
                  {node.name.length > 18 ? `${node.name.slice(0, 16)}…` : node.name}
                </text>

                {/* Node Type Pill Below */}
                <text
                  y={node.type === 'Repository' ? 46 : 38}
                  textAnchor="middle"
                  className="font-mono-code text-[9px] pointer-events-none fill-[#78746D]"
                >
                  {node.type}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};
