import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Network, DataSet, Node, Edge } from 'vis-network/standalone';
import { motion } from 'framer-motion';
import { 
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  PlayIcon,
  PauseIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { GraphNode, GraphEdge, CodeGraph as CodeGraphType, GraphFilters } from '@/types';
import { useCodeAnalysis, useSymbols } from '@/store';

interface CodeGraphProps {
  className?: string;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onSelectionChange?: (nodes: string[], edges: string[]) => void;
}

interface GraphControls {
  layout: 'hierarchical' | 'force' | 'circular' | 'grid';
  physics: boolean;
  showLabels: boolean;
  nodeSize: number;
  edgeWidth: number;
  filters: GraphFilters;
}

export const CodeGraph: React.FC<CodeGraphProps> = ({
  className,
  onNodeClick,
  onEdgeClick,
  onSelectionChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const codeAnalysis = useCodeAnalysis();
  const symbols = useSymbols();
  
  const [isLoading, setIsLoading] = useState(true);
  const [showControls, setShowControls] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  
  const [controls, setControls] = useState<GraphControls>({
    layout: 'hierarchical',
    physics: true,
    showLabels: true,
    nodeSize: 20,
    edgeWidth: 2,
    filters: {
      node_types: ['file', 'function', 'class'],
      edge_types: ['imports', 'calls', 'extends'],
      min_connections: 0,
      max_depth: 3,
      focus_node: undefined
    }
  });

  // Generate graph data from code analysis
  const generateGraphData = useCallback(() => {
    if (!codeAnalysis || !symbols) {
      return { nodes: new DataSet([]), edges: new DataSet([]) };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const nodeMap = new Map<string, GraphNode>();

    // Create nodes from symbols
    symbols.forEach((symbol, index) => {
      const nodeId = `symbol-${index}`;
      const node: GraphNode = {
        id: nodeId,
        label: symbol.name,
        type: symbol.kind as any,
        file_path: symbol.location.file_path,
        location: symbol.location,
        size: controls.nodeSize,
        group: symbol.kind,
        metadata: { symbol }
      };

      nodeMap.set(nodeId, node);

      // Filter by node type
      if (!controls.filters.node_types.includes(node.type)) {
        return;
      }

      // Filter by search query
      if (searchQuery && !node.label.toLowerCase().includes(searchQuery.toLowerCase())) {
        return;
      }

      nodes.push({
        id: nodeId,
        label: controls.showLabels ? node.label : '',
        group: node.type,
        size: node.size,
        color: getNodeColor(node.type),
        font: {
          size: 12,
          color: '#333333'
        },
        borderWidth: 2,
        borderWidthSelected: 4,
        chosen: {
          node: (values: any, id: string, selected: boolean, hovering: boolean) => {
            values.borderColor = selected ? '#2563eb' : hovering ? '#60a5fa' : '#d1d5db';
          }
        }
      });

      // Create edges from symbol references
      if (symbol.references) {
        symbol.references.forEach((ref, refIndex) => {
          const targetSymbol = symbols.find(s => 
            s.location.file_path === ref.file_path &&
            s.location.line === ref.line
          );

          if (targetSymbol) {
            const targetNodeId = `symbol-${symbols.indexOf(targetSymbol)}`;
            const edgeId = `${nodeId}-${targetNodeId}-${refIndex}`;
            
            const edge: GraphEdge = {
              id: edgeId,
              from: nodeId,
              to: targetNodeId,
              type: 'references',
              weight: 1,
              metadata: { reference: ref }
            };

            // Filter by edge type
            if (!controls.filters.edge_types.includes(edge.type)) {
              return;
            }

            edges.push({
              id: edgeId,
              from: nodeId,
              to: targetNodeId,
              width: controls.edgeWidth,
              color: getEdgeColor(edge.type),
              arrows: {
                to: {
                  enabled: true,
                  scaleFactor: 0.8
                }
              },
              smooth: {
                enabled: true,
                type: 'dynamic',
                roundness: 0.5
              }
            });
          }
        });
      }
    });

    // Add file nodes
    const fileNodes = new Set<string>();
    symbols.forEach(symbol => {
      const filePath = symbol.location.file_path;
      if (!fileNodes.has(filePath)) {
        fileNodes.add(filePath);
        
        const fileName = filePath.split('/').pop() || filePath;
        const nodeId = `file-${filePath}`;
        
        if (controls.filters.node_types.includes('file')) {
          nodes.push({
            id: nodeId,
            label: controls.showLabels ? fileName : '',
            group: 'file',
            size: controls.nodeSize * 1.5,
            color: getNodeColor('file'),
            shape: 'box',
            font: {
              size: 10,
              color: '#333333'
            }
          });

          // Connect symbols to their files
          symbols
            .filter(s => s.location.file_path === filePath)
            .forEach((symbol, index) => {
              const symbolNodeId = `symbol-${symbols.indexOf(symbol)}`;
              edges.push({
                id: `${nodeId}-${symbolNodeId}`,
                from: nodeId,
                to: symbolNodeId,
                width: 1,
                color: '#e5e7eb',
                dashes: true,
                physics: false
              });
            });
        }
      }
    });

    return {
      nodes: new DataSet(nodes),
      edges: new DataSet(edges)
    };
  }, [codeAnalysis, symbols, controls, searchQuery]);

  // Initialize network
  useEffect(() => {
    if (!containerRef.current) return;

    const data = generateGraphData();
    
    const options = {
      layout: getLayoutOptions(controls.layout),
      physics: {
        enabled: controls.physics,
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09
        }
      },
      interaction: {
        hover: true,
        selectConnectedEdges: false,
        tooltipDelay: 300
      },
      nodes: {
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 5,
          x: 2,
          y: 2
        }
      },
      edges: {
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.1)',
          size: 3,
          x: 1,
          y: 1
        }
      },
      groups: {
        file: { color: '#3b82f6', shape: 'box' },
        function: { color: '#10b981', shape: 'dot' },
        class: { color: '#f59e0b', shape: 'diamond' },
        variable: { color: '#8b5cf6', shape: 'triangle' },
        constant: { color: '#ef4444', shape: 'square' },
        interface: { color: '#06b6d4', shape: 'star' },
        type: { color: '#84cc16', shape: 'triangleDown' },
        enum: { color: '#f97316', shape: 'hexagon' },
        namespace: { color: '#ec4899', shape: 'ellipse' }
      }
    };

    const network = new Network(containerRef.current, data, options);
    networkRef.current = network;

    // Event handlers
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = data.nodes.get(nodeId);
        if (nodeData && onNodeClick) {
          const graphNode = nodeMap.get(nodeId);
          if (graphNode) {
            onNodeClick(graphNode);
          }
        }
      }

      if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edgeData = data.edges.get(edgeId);
        if (edgeData && onEdgeClick) {
          // Find corresponding GraphEdge
          // Implementation depends on how edges are stored
        }
      }
    });

    network.on('selectNode', (params) => {
      setSelectedNodes(params.nodes);
      onSelectionChange?.(params.nodes, selectedEdges);
    });

    network.on('selectEdge', (params) => {
      setSelectedEdges(params.edges);
      onSelectionChange?.(selectedNodes, params.edges);
    });

    network.on('stabilizationIterationsDone', () => {
      setIsLoading(false);
    });

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [generateGraphData, controls.layout, controls.physics]);

  // Update network when controls change
  useEffect(() => {
    if (!networkRef.current) return;

    const data = generateGraphData();
    networkRef.current.setData(data);
    
    if (controls.physics) {
      networkRef.current.startSimulation();
    } else {
      networkRef.current.stopSimulation();
    }
  }, [generateGraphData, controls]);

  // Handle layout change
  const handleLayoutChange = useCallback((layout: GraphControls['layout']) => {
    setControls(prev => ({ ...prev, layout }));
    
    if (networkRef.current) {
      networkRef.current.setOptions({
        layout: getLayoutOptions(layout)
      });
    }
  }, []);

  // Handle physics toggle
  const handlePhysicsToggle = useCallback(() => {
    setControls(prev => ({ ...prev, physics: !prev.physics }));
  }, []);

  // Handle fit to screen
  const handleFitToScreen = useCallback(() => {
    if (networkRef.current) {
      networkRef.current.fit({
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuad'
        }
      });
    }
  }, []);

  // Handle focus on node
  const handleFocusNode = useCallback((nodeId: string) => {
    if (networkRef.current) {
      networkRef.current.focus(nodeId, {
        scale: 1.5,
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuad'
        }
      });
    }
  }, []);

  if (!codeAnalysis) {
    return (
      <div className={clsx('flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900', className)}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium mb-2">No Code Analysis Available</h3>
          <p>Run code analysis to visualize your codebase structure</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('relative h-full bg-white dark:bg-gray-900', className)}>
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white dark:bg-gray-900 bg-opacity-75 flex items-center justify-center z-10">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
          />
        </div>
      )}

      {/* Controls Panel */}
      <div className="absolute top-4 left-4 z-20">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowControls(!showControls)}
            className={clsx(
              'p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md shadow-sm hover:shadow-md transition-shadow',
              showControls && 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700'
            )}
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4" />
          </button>

          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            onClick={handleFitToScreen}
            className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md shadow-sm hover:shadow-md transition-shadow"
            title="Fit to screen"
          >
            <ArrowsPointingOutIcon className="w-4 h-4" />
          </button>

          <button
            onClick={handlePhysicsToggle}
            className={clsx(
              'p-2 border border-gray-200 dark:border-gray-600 rounded-md shadow-sm hover:shadow-md transition-shadow',
              controls.physics
                ? 'bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300'
                : 'bg-white dark:bg-gray-800'
            )}
            title={controls.physics ? 'Disable physics' : 'Enable physics'}
          >
            {controls.physics ? (
              <PauseIcon className="w-4 h-4" />
            ) : (
              <PlayIcon className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Extended Controls */}
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-2 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md shadow-lg"
          >
            <div className="space-y-4">
              {/* Layout Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Layout
                </label>
                <div className="flex space-x-2">
                  {(['hierarchical', 'force', 'circular', 'grid'] as const).map((layout) => (
                    <button
                      key={layout}
                      onClick={() => handleLayoutChange(layout)}
                      className={clsx(
                        'px-3 py-1 text-xs rounded-md transition-colors',
                        controls.layout === layout
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      )}
                    >
                      {layout}
                    </button>
                  ))}
                </div>
              </div>

              {/* Node Types Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Node Types
                </label>
                <div className="flex flex-wrap gap-2">
                  {['file', 'function', 'class', 'variable', 'interface', 'type'].map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={controls.filters.node_types.includes(type)}
                        onChange={(e) => {
                          const newTypes = e.target.checked
                            ? [...controls.filters.node_types, type]
                            : controls.filters.node_types.filter(t => t !== type);
                          setControls(prev => ({
                            ...prev,
                            filters: { ...prev.filters, node_types: newTypes }
                          }));
                        }}
                        className="mr-1"
                      />
                      <span className="text-xs text-gray-600 dark:text-gray-400">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Display Options */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={controls.showLabels}
                    onChange={(e) => setControls(prev => ({ ...prev, showLabels: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Show Labels</span>
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Graph Container */}
      <div ref={containerRef} className="w-full h-full" />

      {/* Selection Info */}
      {(selectedNodes.length > 0 || selectedEdges.length > 0) && (
        <div className="absolute bottom-4 right-4 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md shadow-lg">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            {selectedNodes.length > 0 && (
              <div>Selected nodes: {selectedNodes.length}</div>
            )}
            {selectedEdges.length > 0 && (
              <div>Selected edges: {selectedEdges.length}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions
function getLayoutOptions(layout: GraphControls['layout']) {
  switch (layout) {
    case 'hierarchical':
      return {
        hierarchical: {
          enabled: true,
          direction: 'UD',
          sortMethod: 'directed',
          shakeTowards: 'roots'
        }
      };
    case 'force':
      return { randomSeed: 2 };
    case 'circular':
      return { randomSeed: 3 };
    case 'grid':
      return { randomSeed: 4 };
    default:
      return {};
  }
}

function getNodeColor(type: string): string {
  const colors = {
    file: '#3b82f6',
    function: '#10b981',
    class: '#f59e0b',
    variable: '#8b5cf6',
    constant: '#ef4444',
    interface: '#06b6d4',
    type: '#84cc16',
    enum: '#f97316',
    namespace: '#ec4899'
  };
  return colors[type as keyof typeof colors] || '#6b7280';
}

function getEdgeColor(type: string): string {
  const colors = {
    imports: '#3b82f6',
    calls: '#10b981',
    extends: '#f59e0b',
    implements: '#8b5cf6',
    references: '#6b7280',
    contains: '#ef4444'
  };
  return colors[type as keyof typeof colors] || '#6b7280';
}
