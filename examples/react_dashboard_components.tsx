/**
 * React Dashboard Components for Codebase Analysis
 * 
 * This file demonstrates how to create expandable React components
 * that consume the hierarchical analysis data from the dashboard API.
 */

import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

// TypeScript interfaces matching the API response models
interface CodeIssue {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  file_path: string;
  line_start?: number;
  line_end?: number;
  symbol_name?: string;
  symbol_type?: string;
  impact_score: number;
  affected_symbols: string[];
  suggested_fix?: string;
  ai_analysis?: string;
}

interface AnalysisNode {
  id: string;
  name: string;
  type: string;
  summary: Record<string, any>;
  issues: CodeIssue[];
  children: AnalysisNode[];
  metadata: Record<string, any>;
  expandable: boolean;
}

interface CodebaseMetrics {
  total_files: number;
  total_functions: number;
  total_classes: number;
  total_symbols: number;
  total_imports: number;
  total_nodes: number;
  total_edges: number;
}

// Severity color mapping
const severityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  info: 'bg-gray-100 text-gray-800 border-gray-200'
};

// Issue severity badge component
const SeverityBadge: React.FC<{ severity: CodeIssue['severity'] }> = ({ severity }) => (
  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${severityColors[severity]}`}>
    {severity.toUpperCase()}
  </span>
);

// Individual issue card component
const IssueCard: React.FC<{ issue: CodeIssue; onAnalyzeWithAI?: (issueId: string) => void }> = ({ 
  issue, 
  onAnalyzeWithAI 
}) => {
  const [expanded, setExpanded] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);

  const handleAIAnalysis = async () => {
    if (onAnalyzeWithAI) {
      setAiAnalyzing(true);
      try {
        await onAnalyzeWithAI(issue.id);
      } finally {
        setAiAnalyzing(false);
      }
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-3 bg-white shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <SeverityBadge severity={issue.severity} />
            <span className="text-sm text-gray-500 capitalize">
              {issue.category.replace('_', ' ')}
            </span>
            {issue.impact_score > 0 && (
              <span className="text-sm text-purple-600 font-medium">
                Impact: {issue.impact_score.toFixed(1)}
              </span>
            )}
          </div>
          
          <h4 className="font-medium text-gray-900 mb-1">{issue.title}</h4>
          <p className="text-sm text-gray-600 mb-2">{issue.description}</p>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>📄 {issue.file_path}</span>
            {issue.line_start && (
              <span>📍 Line {issue.line_start}</span>
            )}
            {issue.symbol_name && (
              <span>🔧 {issue.symbol_name}</span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {onAnalyzeWithAI && (
            <button
              onClick={handleAIAnalysis}
              disabled={aiAnalyzing}
              className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              {aiAnalyzing ? '🤖 Analyzing...' : '🤖 AI Analysis'}
            </button>
          )}
          
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {expanded ? <ChevronDownIcon className="w-4 h-4" /> : <ChevronRightIcon className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {issue.suggested_fix && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-700 mb-1">💡 Suggested Fix:</h5>
              <p className="text-sm text-gray-600 bg-green-50 p-2 rounded">
                {issue.suggested_fix}
              </p>
            </div>
          )}
          
          {issue.affected_symbols.length > 0 && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-700 mb-1">
                💥 Affected Symbols ({issue.affected_symbols.length}):
              </h5>
              <div className="flex flex-wrap gap-1">
                {issue.affected_symbols.slice(0, 5).map((symbol, index) => (
                  <span key={index} className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {symbol}
                  </span>
                ))}
                {issue.affected_symbols.length > 5 && (
                  <span className="text-xs text-gray-500">
                    +{issue.affected_symbols.length - 5} more
                  </span>
                )}
              </div>
            </div>
          )}
          
          {issue.ai_analysis && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-1">🤖 AI Analysis:</h5>
              <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
                {issue.ai_analysis}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Summary statistics component
const SummaryStats: React.FC<{ summary: Record<string, any> }> = ({ summary }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
    {Object.entries(summary).map(([key, value]) => (
      <div key={key} className="bg-gray-50 p-3 rounded-lg">
        <div className="text-sm text-gray-500 capitalize">
          {key.replace('_', ' ')}
        </div>
        <div className="text-lg font-semibold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : String(value)}
        </div>
      </div>
    ))}
  </div>
);

// Main expandable analysis node component
const AnalysisNodeComponent: React.FC<{ 
  node: AnalysisNode; 
  level?: number;
  onAnalyzeWithAI?: (issueId: string) => void;
}> = ({ node, level = 0, onAnalyzeWithAI }) => {
  const [expanded, setExpanded] = useState(level === 0); // Root node expanded by default
  
  const hasContent = node.issues.length > 0 || node.children.length > 0;
  const indentClass = level > 0 ? `ml-${Math.min(level * 4, 16)}` : '';
  
  // Node type icons
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'codebase': return '🏗️';
      case 'category': return '📋';
      case 'files': return '📁';
      case 'file': return '📄';
      case 'flows': return '🔄';
      case 'function_flow': return '⚡';
      default: return '📊';
    }
  };

  return (
    <div className={`${indentClass} mb-2`}>
      <div 
        className={`
          border rounded-lg p-4 bg-white shadow-sm cursor-pointer
          hover:shadow-md transition-shadow duration-200
          ${expanded ? 'border-blue-200' : 'border-gray-200'}
        `}
        onClick={() => hasContent && setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg">{getNodeIcon(node.type)}</span>
            <div>
              <h3 className="font-medium text-gray-900">
                {node.name}
                <span className="ml-2 text-sm text-gray-500 capitalize">
                  ({node.type})
                </span>
              </h3>
              
              {/* Quick stats */}
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                {node.issues.length > 0 && (
                  <span className="flex items-center gap-1">
                    🚨 {node.issues.length} issues
                  </span>
                )}
                {node.children.length > 0 && (
                  <span className="flex items-center gap-1">
                    📂 {node.children.length} children
                  </span>
                )}
                {Object.keys(node.summary).length > 0 && (
                  <span className="flex items-center gap-1">
                    📊 {Object.keys(node.summary).length} metrics
                  </span>
                )}
              </div>
            </div>
          </div>
          
          {hasContent && (
            <div className="flex items-center gap-2">
              {/* Issue severity indicators */}
              {node.issues.length > 0 && (
                <div className="flex gap-1">
                  {['critical', 'high', 'medium', 'low'].map(severity => {
                    const count = node.issues.filter(i => i.severity === severity).length;
                    if (count === 0) return null;
                    return (
                      <span 
                        key={severity}
                        className={`text-xs px-1 py-0.5 rounded ${severityColors[severity as keyof typeof severityColors]}`}
                      >
                        {count}
                      </span>
                    );
                  })}
                </div>
              )}
              
              {expanded ? 
                <ChevronDownIcon className="w-5 h-5 text-gray-400" /> : 
                <ChevronRightIcon className="w-5 h-5 text-gray-400" />
              }
            </div>
          )}
        </div>
        
        {/* Summary stats when collapsed */}
        {!expanded && Object.keys(node.summary).length > 0 && (
          <div className="mt-3 grid grid-cols-3 gap-2">
            {Object.entries(node.summary).slice(0, 3).map(([key, value]) => (
              <div key={key} className="text-center">
                <div className="text-xs text-gray-500 capitalize">
                  {key.replace('_', ' ')}
                </div>
                <div className="text-sm font-medium text-gray-700">
                  {typeof value === 'number' ? value.toLocaleString() : String(value)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Expanded content */}
      {expanded && hasContent && (
        <div className="mt-4 ml-4 space-y-4">
          {/* Summary statistics */}
          {Object.keys(node.summary).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">📊 Summary</h4>
              <SummaryStats summary={node.summary} />
            </div>
          )}
          
          {/* Issues */}
          {node.issues.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                🚨 Issues ({node.issues.length})
              </h4>
              <div className="space-y-2">
                {node.issues.map(issue => (
                  <IssueCard 
                    key={issue.id} 
                    issue={issue} 
                    onAnalyzeWithAI={onAnalyzeWithAI}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Child nodes */}
          {node.children.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                📂 Sub-components ({node.children.length})
              </h4>
              <div className="space-y-2">
                {node.children.map(child => (
                  <AnalysisNodeComponent 
                    key={child.id} 
                    node={child} 
                    level={level + 1}
                    onAnalyzeWithAI={onAnalyzeWithAI}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main dashboard component
const CodebaseAnalysisDashboard: React.FC<{ codebaseId: string }> = ({ codebaseId }) => {
  const [dashboardData, setDashboardData] = useState<AnalysisNode | null>(null);
  const [metrics, setMetrics] = useState<CodebaseMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch dashboard data
        const dashboardResponse = await fetch(`/api/dashboard/${codebaseId}`);
        if (!dashboardResponse.ok) throw new Error('Failed to fetch dashboard data');
        const dashboard = await dashboardResponse.json();
        
        // Fetch metrics
        const metricsResponse = await fetch(`/api/metrics/${codebaseId}`);
        if (!metricsResponse.ok) throw new Error('Failed to fetch metrics');
        const metricsData = await metricsResponse.json();
        
        setDashboardData(dashboard);
        setMetrics(metricsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [codebaseId]);

  // Handle AI analysis
  const handleAnalyzeWithAI = async (issueId: string) => {
    try {
      const response = await fetch(`/api/analyze/${codebaseId}/ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_id: issueId })
      });
      
      if (!response.ok) throw new Error('AI analysis failed');
      
      const result = await response.json();
      
      // Update the issue with AI analysis
      // In a real app, you'd update the state to reflect the new AI analysis
      console.log('AI Analysis result:', result);
      
      // Refresh dashboard data to get updated AI analysis
      window.location.reload(); // Simple refresh - in production, update state
    } catch (err) {
      console.error('AI analysis error:', err);
      alert('AI analysis failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading codebase analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">Error Loading Analysis</h3>
        <p className="text-red-600 mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Codebase Analysis Dashboard
        </h1>
        <p className="text-gray-600">
          Interactive analysis of code quality, issues, and dependencies
        </p>
      </div>

      {/* Metrics overview */}
      {metrics && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">📊 Codebase Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">{metrics.total_files.toLocaleString()}</div>
              <div className="text-sm text-blue-800">Files</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">{metrics.total_functions.toLocaleString()}</div>
              <div className="text-sm text-green-800">Functions</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-purple-600">{metrics.total_classes.toLocaleString()}</div>
              <div className="text-sm text-purple-800">Classes</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-yellow-600">{metrics.total_symbols.toLocaleString()}</div>
              <div className="text-sm text-yellow-800">Symbols</div>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-indigo-600">{metrics.total_imports.toLocaleString()}</div>
              <div className="text-sm text-indigo-800">Imports</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-600">{metrics.total_nodes.toLocaleString()}</div>
              <div className="text-sm text-gray-800">Nodes</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-red-600">{metrics.total_edges.toLocaleString()}</div>
              <div className="text-sm text-red-800">Edges</div>
            </div>
          </div>
        </div>
      )}

      {/* Main analysis tree */}
      {dashboardData && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🔍 Detailed Analysis</h2>
          <AnalysisNodeComponent 
            node={dashboardData} 
            onAnalyzeWithAI={handleAnalyzeWithAI}
          />
        </div>
      )}
    </div>
  );
};

export default CodebaseAnalysisDashboard;

