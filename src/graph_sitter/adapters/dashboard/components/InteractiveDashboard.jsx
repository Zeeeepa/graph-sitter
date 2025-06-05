/**
 * Interactive Dashboard Component
 * 
 * Main dashboard component that provides the unified analysis interface
 * with dropdown selections and progressive loading as requested by the user.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertDescription,
  Badge,
  Progress
} from '@/components/ui';
import { 
  AlertTriangle, 
  BarChart3, 
  Network, 
  Zap, 
  Bug, 
  TrendingUp,
  Eye,
  Download,
  RefreshCw
} from 'lucide-react';

import AnalysisSelector from './AnalysisSelector';
import BlastRadiusVisualization from './BlastRadiusVisualization';
import ErrorAnalysisPanel from './ErrorAnalysisPanel';
import MetricsOverview from './MetricsOverview';
import DependencyGraph from './DependencyGraph';

const InteractiveDashboard = ({ 
  analysisData, 
  codebaseId, 
  onAnalysisTypeChange,
  onTargetChange,
  onVisualizationToggle 
}) => {
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('error_analysis');
  const [selectedTarget, setSelectedTarget] = useState('');
  const [showVisualization, setShowVisualization] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [visualizationData, setVisualizationData] = useState(null);

  // Analysis types configuration
  const analysisTypes = {
    error_analysis: {
      name: 'Error Analysis',
      description: 'Comprehensive error detection and impact assessment',
      icon: Bug,
      targets: ['syntax', 'runtime', 'logical', 'performance', 'security'],
      color: 'text-red-600'
    },
    blast_radius: {
      name: 'Blast Radius',
      description: 'Impact analysis from selected point',
      icon: Zap,
      targets: ['error', 'function', 'class', 'module'],
      color: 'text-orange-600'
    },
    dependency: {
      name: 'Dependency Analysis',
      description: 'Module dependencies and relationships',
      icon: Network,
      targets: ['module', 'class', 'function'],
      color: 'text-blue-600'
    },
    complexity: {
      name: 'Complexity Analysis',
      description: 'Code complexity metrics and heatmap',
      icon: BarChart3,
      targets: ['file', 'class', 'function'],
      color: 'text-purple-600'
    },
    performance: {
      name: 'Performance Analysis',
      description: 'Performance bottlenecks and optimization',
      icon: TrendingUp,
      targets: ['function', 'class', 'module'],
      color: 'text-green-600'
    }
  };

  // Handle analysis type change
  const handleAnalysisTypeChange = useCallback((type) => {
    setSelectedAnalysisType(type);
    setSelectedTarget(''); // Reset target when type changes
    onAnalysisTypeChange?.(type);
  }, [onAnalysisTypeChange]);

  // Handle target change
  const handleTargetChange = useCallback((target) => {
    setSelectedTarget(target);
    onTargetChange?.(target);
  }, [onTargetChange]);

  // Toggle visualization
  const handleVisualizationToggle = useCallback(async () => {
    if (!showVisualization) {
      setLoading(true);
      try {
        // Load visualization data
        const vizData = await loadVisualizationData(selectedAnalysisType, selectedTarget);
        setVisualizationData(vizData);
        setShowVisualization(true);
        onVisualizationToggle?.(true);
      } catch (error) {
        console.error('Failed to load visualization:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setShowVisualization(false);
      onVisualizationToggle?.(false);
    }
  }, [showVisualization, selectedAnalysisType, selectedTarget, onVisualizationToggle]);

  // Load visualization data
  const loadVisualizationData = async (analysisType, target) => {
    // Simulate API call - replace with actual data loading
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      type: analysisType,
      target: target,
      nodes: generateSampleNodes(analysisType),
      edges: generateSampleEdges(analysisType),
      metadata: {
        totalNodes: 50,
        totalEdges: 75,
        analysisTime: new Date().toISOString()
      }
    };
  };

  // Generate sample data (replace with real data)
  const generateSampleNodes = (type) => {
    const baseNodes = [
      { id: 'node1', name: 'main.py', type: 'module', impact: 0.9 },
      { id: 'node2', name: 'utils.py', type: 'module', impact: 0.7 },
      { id: 'node3', name: 'UserClass', type: 'class', impact: 0.8 },
      { id: 'node4', name: 'process_data', type: 'function', impact: 0.6 }
    ];
    
    return baseNodes.map(node => ({
      ...node,
      size: Math.max(10, node.impact * 50),
      color: getNodeColor(node.impact),
      group: type
    }));
  };

  const generateSampleEdges = (type) => {
    return [
      { source: 'node1', target: 'node2', type: 'imports' },
      { source: 'node1', target: 'node3', type: 'contains' },
      { source: 'node3', target: 'node4', type: 'calls' }
    ];
  };

  const getNodeColor = (impact) => {
    if (impact > 0.7) return '#ef4444';
    if (impact > 0.4) return '#f97316';
    return '#3b82f6';
  };

  // Calculate summary statistics
  const getSummaryStats = () => {
    if (!analysisData) return null;

    const errorAnalysis = analysisData.error_analysis || {};
    const metrics = analysisData.metrics_summary || {};
    
    return {
      totalErrors: errorAnalysis.total_errors || 0,
      criticalIssues: (errorAnalysis.errors_by_severity?.critical || []).length,
      healthScore: analysisData.health_score || 0,
      affectedComponents: analysisData.total_affected_nodes || 0
    };
  };

  const summaryStats = getSummaryStats();

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Codebase Analysis Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Comprehensive analysis for {codebaseId}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {/* Export functionality */}}
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Errors</p>
                  <p className="text-2xl font-bold text-red-600">
                    {summaryStats.totalErrors}
                  </p>
                </div>
                <Bug className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Critical Issues</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {summaryStats.criticalIssues}
                  </p>
                </div>
                <AlertTriangle className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Health Score</p>
                  <p className="text-2xl font-bold text-green-600">
                    {Math.round(summaryStats.healthScore)}%
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
              <Progress 
                value={summaryStats.healthScore} 
                className="mt-2"
              />
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Affected Components</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {summaryStats.affectedComponents}
                  </p>
                </div>
                <Network className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Analysis Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Analysis Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AnalysisSelector
            analysisTypes={analysisTypes}
            selectedType={selectedAnalysisType}
            selectedTarget={selectedTarget}
            onTypeChange={handleAnalysisTypeChange}
            onTargetChange={handleTargetChange}
          />
          
          <div className="mt-4 flex items-center space-x-4">
            <Button
              onClick={handleVisualizationToggle}
              disabled={loading}
              className="flex items-center"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Eye className="w-4 h-4 mr-2" />
              )}
              {showVisualization ? 'Hide Visualization' : 'Visualize Codebase'}
            </Button>
            
            {selectedAnalysisType && (
              <Badge variant="outline" className={analysisTypes[selectedAnalysisType].color}>
                {analysisTypes[selectedAnalysisType].name}
                {selectedTarget && ` → ${selectedTarget}`}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="visualization">Visualization</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Analysis Summary</CardTitle>
              </CardHeader>
              <CardContent>
                {analysisData?.actionable_recommendations && (
                  <div className="space-y-2">
                    <h4 className="font-semibold">Key Recommendations:</h4>
                    <ul className="space-y-1">
                      {analysisData.actionable_recommendations.slice(0, 5).map((rec, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                {analysisData?.risk_assessment && (
                  <div className="space-y-3">
                    {Object.entries(analysisData.risk_assessment).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm font-medium capitalize">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <Badge variant={Array.isArray(value) && value.length > 0 ? 'destructive' : 'secondary'}>
                          {Array.isArray(value) ? value.length : value}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="errors">
          <ErrorAnalysisPanel 
            errorData={analysisData?.error_analysis}
            selectedTarget={selectedTarget}
          />
        </TabsContent>

        <TabsContent value="dependencies">
          <DependencyGraph 
            dependencyData={analysisData?.dependency_analysis}
            selectedTarget={selectedTarget}
          />
        </TabsContent>

        <TabsContent value="metrics">
          <MetricsOverview 
            metricsData={analysisData?.metrics_summary}
            selectedTarget={selectedTarget}
          />
        </TabsContent>

        <TabsContent value="visualization">
          {showVisualization ? (
            <BlastRadiusVisualization
              data={visualizationData}
              analysisType={selectedAnalysisType}
              target={selectedTarget}
            />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Eye className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  Visualization Not Loaded
                </h3>
                <p className="text-gray-500 mb-4">
                  Click "Visualize Codebase" to load interactive visualizations
                </p>
                <Button onClick={handleVisualizationToggle}>
                  Load Visualization
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Progressive Loading Alert */}
      {loading && (
        <Alert>
          <RefreshCw className="w-4 h-4 animate-spin" />
          <AlertDescription>
            Loading comprehensive visualization data... This may take a moment.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default InteractiveDashboard;

