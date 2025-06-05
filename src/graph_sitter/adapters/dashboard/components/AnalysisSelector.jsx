/**
 * Analysis Selector Component
 * 
 * Provides dropdown controls for selecting analysis types and targets
 * as requested by the user for the interactive dashboard.
 */

import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Card,
  CardContent,
  Badge,
  Separator
} from '@/components/ui';
import { 
  Bug, 
  Zap, 
  Network, 
  BarChart3, 
  TrendingUp,
  Info
} from 'lucide-react';

const AnalysisSelector = ({
  analysisTypes,
  selectedType,
  selectedTarget,
  onTypeChange,
  onTargetChange
}) => {
  // Get icon for analysis type
  const getAnalysisIcon = (type) => {
    const iconMap = {
      error_analysis: Bug,
      blast_radius: Zap,
      dependency: Network,
      complexity: BarChart3,
      performance: TrendingUp
    };
    
    const IconComponent = iconMap[type] || Info;
    return <IconComponent className="w-4 h-4" />;
  };

  // Get available targets for selected analysis type
  const getAvailableTargets = () => {
    if (!selectedType || !analysisTypes[selectedType]) {
      return [];
    }
    return analysisTypes[selectedType].targets || [];
  };

  // Get target descriptions
  const getTargetDescription = (target) => {
    const descriptions = {
      // Error analysis targets
      syntax: 'Python syntax errors and parsing issues',
      runtime: 'Potential runtime errors and exceptions',
      logical: 'Logic errors and code smells',
      performance: 'Performance bottlenecks and inefficiencies',
      security: 'Security vulnerabilities and risks',
      
      // Blast radius targets
      error: 'Impact analysis from error locations',
      function: 'Impact analysis from specific functions',
      class: 'Impact analysis from class definitions',
      module: 'Impact analysis from module level',
      
      // Dependency targets
      imports: 'Import and export relationships',
      inheritance: 'Class inheritance hierarchies',
      calls: 'Function call relationships',
      
      // Complexity targets
      file: 'File-level complexity metrics',
      cyclomatic: 'Cyclomatic complexity analysis',
      cognitive: 'Cognitive complexity assessment',
      
      // Performance targets
      bottlenecks: 'Performance bottleneck identification',
      optimization: 'Optimization opportunities',
      memory: 'Memory usage analysis'
    };
    
    return descriptions[target] || `Analysis focused on ${target}`;
  };

  return (
    <div className="space-y-6">
      {/* Analysis Type Selection */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700">
          Analysis Type
        </label>
        <Select value={selectedType} onValueChange={onTypeChange}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select analysis type..." />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(analysisTypes).map(([key, config]) => (
              <SelectItem key={key} value={key}>
                <div className="flex items-center space-x-2">
                  {getAnalysisIcon(key)}
                  <span>{config.name}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {/* Analysis Type Description */}
        {selectedType && analysisTypes[selectedType] && (
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-3">
              <div className="flex items-start space-x-2">
                <div className={`mt-0.5 ${analysisTypes[selectedType].color}`}>
                  {getAnalysisIcon(selectedType)}
                </div>
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    {analysisTypes[selectedType].name}
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    {analysisTypes[selectedType].description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Separator />

      {/* Target Selection */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700">
          Analysis Target
        </label>
        <Select 
          value={selectedTarget} 
          onValueChange={onTargetChange}
          disabled={!selectedType}
        >
          <SelectTrigger className="w-full">
            <SelectValue 
              placeholder={
                selectedType 
                  ? "Select analysis target..." 
                  : "Select analysis type first"
              } 
            />
          </SelectTrigger>
          <SelectContent>
            {getAvailableTargets().map((target) => (
              <SelectItem key={target} value={target}>
                <div className="flex flex-col items-start">
                  <span className="font-medium capitalize">
                    {target.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-gray-500">
                    {getTargetDescription(target)}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Target Description */}
        {selectedTarget && (
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-3">
              <div className="flex items-start space-x-2">
                <Info className="w-4 h-4 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-900 capitalize">
                    {selectedTarget.replace(/_/g, ' ')} Analysis
                  </p>
                  <p className="text-xs text-green-700 mt-1">
                    {getTargetDescription(selectedTarget)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Analysis Configuration Summary */}
      {selectedType && selectedTarget && (
        <>
          <Separator />
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700">
              Configuration Summary
            </label>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="flex items-center space-x-1">
                {getAnalysisIcon(selectedType)}
                <span>{analysisTypes[selectedType].name}</span>
              </Badge>
              <Badge variant="secondary" className="capitalize">
                {selectedTarget.replace(/_/g, ' ')}
              </Badge>
            </div>
            
            {/* Visualization Options */}
            <Card className="bg-gray-50">
              <CardContent className="p-3">
                <p className="text-xs font-medium text-gray-700 mb-2">
                  Available Visualizations:
                </p>
                <div className="flex flex-wrap gap-1">
                  {analysisTypes[selectedType].visualizations?.map((viz) => (
                    <Badge key={viz} variant="outline" className="text-xs">
                      {viz.replace(/_/g, ' ')}
                    </Badge>
                  )) || (
                    <Badge variant="outline" className="text-xs">
                      Standard Graph View
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Quick Selection Presets */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700">
          Quick Presets
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => {
              onTypeChange('error_analysis');
              onTargetChange('syntax');
            }}
            className="p-2 text-left border rounded-md hover:bg-red-50 hover:border-red-200 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Bug className="w-4 h-4 text-red-500" />
              <div>
                <p className="text-xs font-medium">Syntax Errors</p>
                <p className="text-xs text-gray-500">Find parsing issues</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => {
              onTypeChange('blast_radius');
              onTargetChange('error');
            }}
            className="p-2 text-left border rounded-md hover:bg-orange-50 hover:border-orange-200 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-orange-500" />
              <div>
                <p className="text-xs font-medium">Error Impact</p>
                <p className="text-xs text-gray-500">Trace error effects</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => {
              onTypeChange('dependency');
              onTargetChange('module');
            }}
            className="p-2 text-left border rounded-md hover:bg-blue-50 hover:border-blue-200 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Network className="w-4 h-4 text-blue-500" />
              <div>
                <p className="text-xs font-medium">Dependencies</p>
                <p className="text-xs text-gray-500">Module relationships</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => {
              onTypeChange('performance');
              onTargetChange('function');
            }}
            className="p-2 text-left border rounded-md hover:bg-green-50 hover:border-green-200 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <div>
                <p className="text-xs font-medium">Performance</p>
                <p className="text-xs text-gray-500">Optimize functions</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalysisSelector;

