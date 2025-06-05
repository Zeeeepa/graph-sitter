/**
 * Blast Radius Visualization Component
 * 
 * Interactive visualization for blast radius analysis showing
 * error propagation and impact assessment.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  Slider,
  Switch,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui';
import {
  Zap,
  Target,
  Layers,
  Filter,
  Download,
  Maximize2,
  RotateCcw
} from 'lucide-react';

const BlastRadiusVisualization = ({ 
  data, 
  analysisType, 
  target,
  onNodeClick,
  onEdgeClick 
}) => {
  const svgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [impactLevel, setImpactLevel] = useState(3);
  const [showLabels, setShowLabels] = useState(true);
  const [filterBySeverity, setFilterBySeverity] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Initialize visualization
  useEffect(() => {
    if (!data || !data.nodes || !data.edges) return;

    createVisualization();
  }, [data, impactLevel, showLabels, filterBySeverity]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: Math.max(400, container.clientHeight)
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const createVisualization = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Filter data based on impact level and severity
    const filteredNodes = data.nodes.filter(node => {
      const levelFilter = node.impact_level <= impactLevel;
      const severityFilter = !filterBySeverity || node.impact_score > 0.5;
      return levelFilter && severityFilter;
    });

    const filteredEdges = data.edges.filter(edge => {
      const sourceExists = filteredNodes.some(n => n.id === edge.source);
      const targetExists = filteredNodes.some(n => n.id === edge.target);
      return sourceExists && targetExists;
    });

    // Set up SVG
    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink(filteredEdges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(innerWidth / 2, innerHeight / 2))
      .force('collision', d3.forceCollide().radius(d => d.size + 5));

    // Create arrow markers for directed edges
    const defs = g.append('defs');
    
    defs.selectAll('marker')
      .data(['impact', 'dependency', 'error'])
      .enter()
      .append('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', d => getEdgeColor(d));

    // Create edges
    const links = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredEdges)
      .enter()
      .append('line')
      .attr('stroke', d => getEdgeColor(d.type))
      .attr('stroke-width', d => Math.max(1, d.weight * 2))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', d => `url(#arrow-${d.type})`)
      .on('click', (event, d) => {
        event.stopPropagation();
        onEdgeClick?.(d);
      });

    // Create nodes
    const nodes = g.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(filteredNodes)
      .enter()
      .append('circle')
      .attr('r', d => d.size)
      .attr('fill', d => d.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        onNodeClick?.(d);
      })
      .on('mouseover', function(event, d) {
        // Highlight connected nodes
        const connectedNodeIds = new Set();
        filteredEdges.forEach(edge => {
          if (edge.source.id === d.id) connectedNodeIds.add(edge.target.id);
          if (edge.target.id === d.id) connectedNodeIds.add(edge.source.id);
        });

        nodes
          .style('opacity', node => 
            node.id === d.id || connectedNodeIds.has(node.id) ? 1 : 0.3
          );

        links
          .style('opacity', edge => 
            edge.source.id === d.id || edge.target.id === d.id ? 1 : 0.1
          );

        // Show tooltip
        showTooltip(event, d);
      })
      .on('mouseout', function() {
        nodes.style('opacity', 1);
        links.style('opacity', 0.6);
        hideTooltip();
      });

    // Add labels if enabled
    if (showLabels) {
      const labels = g.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(filteredNodes)
        .enter()
        .append('text')
        .text(d => d.name)
        .attr('font-size', '10px')
        .attr('font-family', 'Arial, sans-serif')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .style('pointer-events', 'none')
        .style('fill', '#333');

      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);

        labels
          .attr('x', d => d.x)
          .attr('y', d => d.y + d.size + 15);
      });
    } else {
      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
      });
    }

    // Add drag behavior
    const drag = d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodes.call(drag);

    // Add legend
    createLegend(g, innerWidth, innerHeight);
  };

  const getEdgeColor = (type) => {
    const colors = {
      impact: '#ef4444',
      dependency: '#3b82f6',
      error: '#f97316',
      inheritance: '#8b5cf6',
      calls: '#10b981'
    };
    return colors[type] || '#6b7280';
  };

  const createLegend = (g, width, height) => {
    const legend = g.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - 150}, 20)`);

    const legendData = [
      { type: 'high', color: '#ef4444', label: 'High Impact' },
      { type: 'medium', color: '#f97316', label: 'Medium Impact' },
      { type: 'low', color: '#3b82f6', label: 'Low Impact' }
    ];

    const legendItems = legend.selectAll('.legend-item')
      .data(legendData)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`);

    legendItems.append('circle')
      .attr('r', 6)
      .attr('fill', d => d.color);

    legendItems.append('text')
      .attr('x', 15)
      .attr('y', 0)
      .attr('dy', '.35em')
      .style('font-size', '12px')
      .text(d => d.label);
  };

  const showTooltip = (event, d) => {
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'blast-radius-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000);

    tooltip.html(`
      <strong>${d.name}</strong><br/>
      Type: ${d.type}<br/>
      Impact Level: ${d.impact_level}<br/>
      Impact Score: ${d.impact_score.toFixed(2)}<br/>
      File: ${d.file_path}
    `)
    .style('left', (event.pageX + 10) + 'px')
    .style('top', (event.pageY - 10) + 'px');
  };

  const hideTooltip = () => {
    d3.selectAll('.blast-radius-tooltip').remove();
  };

  const resetVisualization = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().duration(750).call(
      d3.zoom().transform,
      d3.zoomIdentity
    );
  };

  const exportVisualization = () => {
    const svg = svgRef.current;
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svg);
    
    const blob = new Blob([source], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `blast-radius-${analysisType}-${target}.svg`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  if (!data || !data.nodes) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Zap className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No Blast Radius Data
          </h3>
          <p className="text-gray-500">
            Select an analysis type and target to generate blast radius visualization
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              Blast Radius Visualization
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={resetVisualization}>
                <RotateCcw className="w-4 h-4 mr-1" />
                Reset
              </Button>
              <Button variant="outline" size="sm" onClick={exportVisualization}>
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Impact Level Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Impact Level</label>
              <Slider
                value={[impactLevel]}
                onValueChange={(value) => setImpactLevel(value[0])}
                max={5}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="text-xs text-gray-500">
                Level: {impactLevel}
              </div>
            </div>

            {/* Show Labels Toggle */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Show Labels</label>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={showLabels}
                  onCheckedChange={setShowLabels}
                />
                <span className="text-sm text-gray-600">
                  {showLabels ? 'On' : 'Off'}
                </span>
              </div>
            </div>

            {/* Severity Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">High Impact Only</label>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={filterBySeverity}
                  onCheckedChange={setFilterBySeverity}
                />
                <span className="text-sm text-gray-600">
                  {filterBySeverity ? 'On' : 'Off'}
                </span>
              </div>
            </div>

            {/* Analysis Info */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Analysis</label>
              <div className="flex flex-col space-y-1">
                <Badge variant="outline" className="text-xs">
                  {analysisType?.replace(/_/g, ' ')}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {target}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Visualization */}
      <Card>
        <CardContent className="p-0">
          <div className="relative">
            <svg ref={svgRef} className="w-full border rounded-lg" />
            
            {/* Selected Node Info */}
            {selectedNode && (
              <div className="absolute top-4 left-4 bg-white p-3 rounded-lg shadow-lg border max-w-xs">
                <h4 className="font-semibold text-sm mb-2">{selectedNode.name}</h4>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <Badge variant="outline" className="text-xs">
                      {selectedNode.type}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Impact Level:</span>
                    <span>{selectedNode.impact_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Impact Score:</span>
                    <span>{selectedNode.impact_score?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>File:</span>
                    <span className="truncate ml-2" title={selectedNode.file_path}>
                      {selectedNode.file_path?.split('/').pop()}
                    </span>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => setSelectedNode(null)}
                >
                  Close
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Nodes</p>
                <p className="text-2xl font-bold">{data.nodes?.length || 0}</p>
              </div>
              <Target className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Impact Levels</p>
                <p className="text-2xl font-bold">
                  {Math.max(...(data.nodes?.map(n => n.impact_level) || [0]))}
                </p>
              </div>
              <Layers className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Impact</p>
                <p className="text-2xl font-bold">
                  {data.nodes?.filter(n => n.impact_score > 0.7).length || 0}
                </p>
              </div>
              <Filter className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BlastRadiusVisualization;

