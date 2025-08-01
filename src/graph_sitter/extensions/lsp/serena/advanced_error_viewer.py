#!/usr/bin/env python3
"""
Advanced Error Viewer for Serena Integration

This module provides comprehensive error viewing capabilities with intelligent
context inclusion and deep code understanding.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict
from pathlib import Path

from .advanced_context import AdvancedContextEngine, ContextualError
from .knowledge_integration import AdvancedKnowledgeIntegration

logger = logging.getLogger(__name__)


@dataclass
class ErrorViewConfig:
    """Configuration for error viewing."""
    include_context: bool = True
    include_suggestions: bool = True
    include_related_errors: bool = True
    include_code_examples: bool = True
    max_context_depth: int = 3
    max_suggestions: int = 10
    max_related_errors: int = 5


@dataclass
class ErrorVisualization:
    """Error visualization data."""
    error_id: str
    visual_type: str  # "code_highlight", "dependency_graph", "flow_chart"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorCluster:
    """Cluster of related errors."""
    cluster_id: str
    cluster_type: str  # "file_based", "function_based", "pattern_based"
    errors: List[str] = field(default_factory=list)
    common_patterns: List[str] = field(default_factory=list)
    suggested_fixes: List[Dict[str, Any]] = field(default_factory=list)
    priority_score: float = 0.0


class AdvancedErrorViewer:
    """
    Advanced error viewer that provides comprehensive error analysis,
    visualization, and intelligent fix suggestions.
    """
    
    def __init__(
        self,
        codebase,
        knowledge_integration: Optional[AdvancedKnowledgeIntegration] = None,
        config: Optional[ErrorViewConfig] = None
    ):
        self.codebase = codebase
        self.knowledge_integration = knowledge_integration
        self.config = config or ErrorViewConfig()
        self.context_engine = AdvancedContextEngine(codebase, knowledge_integration)
        
        # Caches
        self.error_cache = {}
        self.cluster_cache = {}
        self.visualization_cache = {}
    
    async def view_error_comprehensive(
        self,
        error_info: Dict[str, Any],
        include_visualizations: bool = True
    ) -> Dict[str, Any]:
        """
        Provide comprehensive error view with all available context and analysis.
        """
        error_id = error_info.get("id", "unknown")
        
        # Check cache
        cache_key = f"comprehensive_{error_id}"
        if cache_key in self.error_cache:
            return self.error_cache[cache_key]
        
        # Analyze error context
        contextual_error = await self.context_engine.analyze_error_context(
            error_info, include_deep_analysis=True
        )
        
        # Build comprehensive view
        comprehensive_view = {
            "error_overview": self._build_error_overview(contextual_error),
            "context_analysis": self._build_context_analysis(contextual_error),
            "impact_assessment": self._build_impact_assessment(contextual_error),
            "fix_recommendations": self._build_fix_recommendations(contextual_error),
            "related_analysis": await self._build_related_analysis(contextual_error),
            "knowledge_insights": await self._build_knowledge_insights(contextual_error)
        }
        
        # Add visualizations if requested
        if include_visualizations:
            comprehensive_view["visualizations"] = await self._generate_visualizations(contextual_error)
        
        # Add metadata
        comprehensive_view["metadata"] = {
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "analysis_depth": self.config.max_context_depth,
            "knowledge_integration_enabled": self.knowledge_integration is not None
        }
        
        # Cache the result
        self.error_cache[cache_key] = comprehensive_view
        
        return comprehensive_view
    
    def _build_error_overview(self, error: ContextualError) -> Dict[str, Any]:
        """Build error overview section."""
        return {
            "basic_info": {
                "id": error.error_id,
                "type": error.error_type,
                "severity": error.severity,
                "message": error.message,
                "description": error.description
            },
            "location": {
                "file_path": error.file_path,
                "line_number": error.line_number,
                "function_name": error.function_name,
                "class_name": error.class_name
            },
            "immediate_context": error.immediate_context,
            "quick_summary": self._generate_quick_summary(error)
        }
    
    def _build_context_analysis(self, error: ContextualError) -> Dict[str, Any]:
        """Build context analysis section."""
        return {
            "function_context": error.function_context,
            "class_context": error.class_context,
            "file_context": error.file_context,
            "module_context": error.module_context,
            "project_context": error.project_context,
            "context_summary": self._summarize_context(error)
        }
    
    def _build_impact_assessment(self, error: ContextualError) -> Dict[str, Any]:
        """Build impact assessment section."""
        return {
            "impact_analysis": error.impact_analysis,
            "affected_components": self._identify_affected_components(error),
            "risk_assessment": self._assess_risks(error),
            "priority_recommendation": self._recommend_priority(error)
        }
    
    def _build_fix_recommendations(self, error: ContextualError) -> Dict[str, Any]:
        """Build fix recommendations section."""
        return {
            "immediate_fixes": [fix for fix in error.fix_suggestions if fix.get("priority") == "critical"],
            "short_term_fixes": [fix for fix in error.fix_suggestions if fix.get("priority") == "high"],
            "long_term_improvements": [fix for fix in error.fix_suggestions if fix.get("priority") in ["medium", "low"]],
            "code_examples": error.code_examples,
            "best_practices": error.best_practices,
            "implementation_guide": self._generate_implementation_guide(error)
        }
    
    async def _build_related_analysis(self, error: ContextualError) -> Dict[str, Any]:
        """Build related analysis section."""
        related_errors = await self._find_related_errors(error)
        error_patterns = await self._analyze_error_patterns(error)
        
        return {
            "related_errors": related_errors,
            "error_patterns": error_patterns,
            "dependency_impact": self._analyze_dependency_impact(error),
            "similar_issues": await self._find_similar_issues(error)
        }
    
    async def _build_knowledge_insights(self, error: ContextualError) -> Dict[str, Any]:
        """Build knowledge insights section using Serena integration."""
        insights = {
            "semantic_analysis": {},
            "architectural_insights": {},
            "best_practice_violations": [],
            "ecosystem_knowledge": {}
        }
        
        if self.knowledge_integration:
            try:
                knowledge = await self.knowledge_integration.extract_comprehensive_knowledge(
                    file_path=error.file_path,
                    symbol_name=error.function_name or error.class_name,
                    line_number=error.line_number
                )
                
                # Extract semantic insights
                if "semantic" in knowledge:
                    insights["semantic_analysis"] = knowledge["semantic"]
                
                # Extract architectural insights
                if "architectural" in knowledge:
                    insights["architectural_insights"] = knowledge["architectural"]
                
                # Extract dependency insights
                if "dependency" in knowledge:
                    insights["dependency_analysis"] = knowledge["dependency"]
                
                # Extract contextual insights
                if "contextual_analysis" in knowledge:
                    insights["ecosystem_knowledge"] = knowledge["contextual_analysis"].get("ecosystem_context", {})
                
            except Exception as e:
                logger.error(f"Failed to build knowledge insights: {e}")
                insights["error"] = str(e)
        
        return insights
    
    async def _generate_visualizations(self, error: ContextualError) -> List[ErrorVisualization]:
        """Generate visualizations for the error."""
        visualizations = []
        
        try:
            # Code highlight visualization
            code_viz = await self._create_code_highlight_visualization(error)
            if code_viz:
                visualizations.append(code_viz)
            
            # Dependency graph visualization
            if error.dependency_chain:
                dep_viz = await self._create_dependency_visualization(error)
                if dep_viz:
                    visualizations.append(dep_viz)
            
            # Control flow visualization
            if error.function_context:
                flow_viz = await self._create_control_flow_visualization(error)
                if flow_viz:
                    visualizations.append(flow_viz)
            
            # Impact visualization
            impact_viz = await self._create_impact_visualization(error)
            if impact_viz:
                visualizations.append(impact_viz)
                
        except Exception as e:
            logger.error(f"Failed to generate visualizations: {e}")
        
        return visualizations
    
    async def _create_code_highlight_visualization(self, error: ContextualError) -> Optional[ErrorVisualization]:
        """Create code highlighting visualization."""
        if not error.immediate_context.get("surrounding_code"):
            return None
        
        surrounding_code = error.immediate_context["surrounding_code"]
        
        return ErrorVisualization(
            error_id=error.error_id,
            visual_type="code_highlight",
            data={
                "lines": surrounding_code["lines"],
                "start_line": surrounding_code["start_line"],
                "end_line": surrounding_code["end_line"],
                "error_line": surrounding_code["error_line"],
                "highlights": [
                    {
                        "line": surrounding_code["error_line"],
                        "type": "error",
                        "message": error.message
                    }
                ],
                "annotations": self._generate_code_annotations(error)
            },
            metadata={
                "file_path": error.file_path,
                "language": self._detect_language(error.file_path)
            }
        )
    
    async def _create_dependency_visualization(self, error: ContextualError) -> Optional[ErrorVisualization]:
        """Create dependency graph visualization."""
        if not error.dependency_chain:
            return None
        
        nodes = []
        edges = []
        
        # Create nodes for each dependency
        for i, dep in enumerate(error.dependency_chain):
            nodes.append({
                "id": f"dep_{i}",
                "label": dep,
                "type": "dependency",
                "level": i
            })
        
        # Create edges between dependencies
        for i in range(len(error.dependency_chain) - 1):
            edges.append({
                "source": f"dep_{i}",
                "target": f"dep_{i+1}",
                "type": "depends_on"
            })
        
        return ErrorVisualization(
            error_id=error.error_id,
            visual_type="dependency_graph",
            data={
                "nodes": nodes,
                "edges": edges,
                "layout": "hierarchical"
            },
            metadata={
                "dependency_count": len(error.dependency_chain),
                "max_depth": len(error.dependency_chain)
            }
        )
    
    async def _create_control_flow_visualization(self, error: ContextualError) -> Optional[ErrorVisualization]:
        """Create control flow visualization."""
        if not error.function_context:
            return None
        
        control_flow = error.function_context.get("control_flow", {})
        
        return ErrorVisualization(
            error_id=error.error_id,
            visual_type="control_flow",
            data={
                "if_statements": control_flow.get("if_statements", 0),
                "loops": control_flow.get("loops", 0),
                "try_blocks": control_flow.get("try_blocks", 0),
                "complexity_score": error.function_context.get("function_info", {}).get("complexity", 0)
            },
            metadata={
                "function_name": error.function_name,
                "visualization_type": "flow_chart"
            }
        )
    
    async def _create_impact_visualization(self, error: ContextualError) -> Optional[ErrorVisualization]:
        """Create impact visualization."""
        impact_data = {
            "scope": error.impact_analysis.get("scope", "unknown"),
            "severity": error.severity,
            "affected_components": len(error.impact_analysis.get("affected_components", [])),
            "risk_level": error.impact_analysis.get("change_risk", "unknown")
        }
        
        return ErrorVisualization(
            error_id=error.error_id,
            visual_type="impact_chart",
            data=impact_data,
            metadata={
                "chart_type": "radar",
                "metrics": list(impact_data.keys())
            }
        )
    
    async def cluster_related_errors(self, errors: List[Dict[str, Any]]) -> List[ErrorCluster]:
        """Cluster related errors for better organization."""
        clusters = []
        
        try:
            # File-based clustering
            file_clusters = self._cluster_by_file(errors)
            clusters.extend(file_clusters)
            
            # Function-based clustering
            function_clusters = self._cluster_by_function(errors)
            clusters.extend(function_clusters)
            
            # Pattern-based clustering
            pattern_clusters = await self._cluster_by_pattern(errors)
            clusters.extend(pattern_clusters)
            
            # Calculate priority scores
            for cluster in clusters:
                cluster.priority_score = self._calculate_cluster_priority(cluster, errors)
            
            # Sort by priority
            clusters.sort(key=lambda c: c.priority_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to cluster errors: {e}")
        
        return clusters
    
    def _cluster_by_file(self, errors: List[Dict[str, Any]]) -> List[ErrorCluster]:
        """Cluster errors by file."""
        file_groups = defaultdict(list)
        
        for error in errors:
            file_path = error.get("file_path", "unknown")
            file_groups[file_path].append(error.get("id", "unknown"))
        
        clusters = []
        for file_path, error_ids in file_groups.items():
            if len(error_ids) > 1:  # Only create clusters with multiple errors
                clusters.append(ErrorCluster(
                    cluster_id=f"file_{hash(file_path)}",
                    cluster_type="file_based",
                    errors=error_ids,
                    common_patterns=[f"All errors in file: {Path(file_path).name}"]
                ))
        
        return clusters
    
    def _cluster_by_function(self, errors: List[Dict[str, Any]]) -> List[ErrorCluster]:
        """Cluster errors by function."""
        function_groups = defaultdict(list)
        
        for error in errors:
            function_name = error.get("function_name")
            if function_name:
                key = f"{error.get('file_path', 'unknown')}:{function_name}"
                function_groups[key].append(error.get("id", "unknown"))
        
        clusters = []
        for func_key, error_ids in function_groups.items():
            if len(error_ids) > 1:
                file_path, function_name = func_key.split(":", 1)
                clusters.append(ErrorCluster(
                    cluster_id=f"function_{hash(func_key)}",
                    cluster_type="function_based",
                    errors=error_ids,
                    common_patterns=[f"All errors in function: {function_name}"]
                ))
        
        return clusters
    
    async def _cluster_by_pattern(self, errors: List[Dict[str, Any]]) -> List[ErrorCluster]:
        """Cluster errors by common patterns."""
        pattern_groups = defaultdict(list)
        
        for error in errors:
            error_type = error.get("type", "unknown")
            severity = error.get("severity", "unknown")
            pattern_key = f"{error_type}_{severity}"
            pattern_groups[pattern_key].append(error.get("id", "unknown"))
        
        clusters = []
        for pattern_key, error_ids in pattern_groups.items():
            if len(error_ids) > 1:
                error_type, severity = pattern_key.split("_", 1)
                clusters.append(ErrorCluster(
                    cluster_id=f"pattern_{hash(pattern_key)}",
                    cluster_type="pattern_based",
                    errors=error_ids,
                    common_patterns=[f"Type: {error_type}, Severity: {severity}"]
                ))
        
        return clusters
    
    def _calculate_cluster_priority(self, cluster: ErrorCluster, all_errors: List[Dict[str, Any]]) -> float:
        """Calculate priority score for an error cluster."""
        priority_score = 0.0
        
        # Base score on number of errors
        priority_score += len(cluster.errors) * 10
        
        # Boost score based on severity
        for error in all_errors:
            if error.get("id") in cluster.errors:
                severity = error.get("severity", "low")
                if severity == "critical":
                    priority_score += 50
                elif severity == "high":
                    priority_score += 30
                elif severity == "medium":
                    priority_score += 15
                else:
                    priority_score += 5
        
        # Boost score for certain error types
        for error in all_errors:
            if error.get("id") in cluster.errors:
                error_type = error.get("type", "")
                if "security" in error_type:
                    priority_score += 25
                elif "performance" in error_type:
                    priority_score += 15
                elif "complexity" in error_type:
                    priority_score += 10
        
        return priority_score
    
    # Helper methods
    def _generate_quick_summary(self, error: ContextualError) -> str:
        """Generate a quick summary of the error."""
        summary_parts = [f"{error.severity.title()} {error.error_type} in {Path(error.file_path).name}"]
        
        if error.function_name:
            summary_parts.append(f"function '{error.function_name}'")
        elif error.class_name:
            summary_parts.append(f"class '{error.class_name}'")
        
        if error.line_number:
            summary_parts.append(f"at line {error.line_number}")
        
        return " ".join(summary_parts)
    
    def _summarize_context(self, error: ContextualError) -> Dict[str, str]:
        """Summarize the context analysis."""
        summary = {}
        
        if error.function_context:
            func_info = error.function_context.get("function_info", {})
            complexity = func_info.get("complexity", 0)
            summary["function"] = f"Function with {func_info.get('parameter_count', 0)} parameters and complexity {complexity}"
        
        if error.class_context:
            class_info = error.class_context.get("class_info", {})
            summary["class"] = f"Class with {class_info.get('method_count', 0)} methods and {class_info.get('attribute_count', 0)} attributes"
        
        if error.file_context:
            file_info = error.file_context.get("file_info", {})
            summary["file"] = f"File with {file_info.get('line_count', 0)} lines"
        
        return summary
    
    def _identify_affected_components(self, error: ContextualError) -> List[str]:
        """Identify components affected by the error."""
        affected = []
        
        if error.related_symbols:
            affected.extend(error.related_symbols)
        
        if error.dependency_chain:
            affected.extend(error.dependency_chain)
        
        return list(set(affected))[:10]  # Limit to top 10
    
    def _assess_risks(self, error: ContextualError) -> Dict[str, str]:
        """Assess various risks associated with the error."""
        return {
            "change_risk": error.impact_analysis.get("change_risk", "unknown"),
            "propagation_risk": "high" if len(error.dependency_chain) > 3 else "low",
            "maintenance_risk": "high" if error.error_type == "complexity_issue" else "medium"
        }
    
    def _recommend_priority(self, error: ContextualError) -> str:
        """Recommend priority level for fixing the error."""
        if error.severity == "critical":
            return "immediate"
        elif error.severity == "high" and error.error_type == "security_vulnerability":
            return "urgent"
        elif error.impact_analysis.get("scope") == "project":
            return "high"
        else:
            return "normal"
    
    def _generate_implementation_guide(self, error: ContextualError) -> Dict[str, Any]:
        """Generate implementation guide for fixes."""
        return {
            "steps": [
                "1. Analyze the error context and impact",
                "2. Choose appropriate fix strategy",
                "3. Implement changes incrementally",
                "4. Test changes thoroughly",
                "5. Monitor for side effects"
            ],
            "considerations": [
                "Consider backward compatibility",
                "Ensure proper error handling",
                "Update documentation if needed",
                "Add tests for the fix"
            ],
            "tools_recommended": [
                "Static analysis tools",
                "Unit testing framework",
                "Code review process"
            ]
        }
    
    def _analyze_dependency_impact(self, error: ContextualError) -> Dict[str, Any]:
        """Analyze impact on dependencies."""
        return {
            "upstream_impact": len(error.dependency_chain),
            "downstream_impact": len(error.related_symbols),
            "circular_dependencies": False,  # Simplified
            "critical_path": error.dependency_chain[:3] if error.dependency_chain else []
        }
    
    async def _find_related_errors(self, error: ContextualError) -> List[str]:
        """Find errors related to the current error."""
        # This would typically query a database or error tracking system
        # For now, return empty list
        return []
    
    async def _analyze_error_patterns(self, error: ContextualError) -> List[str]:
        """Analyze patterns in the error."""
        patterns = []
        
        if error.error_type == "complexity_issue":
            patterns.append("High cyclomatic complexity pattern")
        
        if error.function_context and error.function_context.get("function_info", {}).get("parameter_count", 0) > 5:
            patterns.append("Too many parameters pattern")
        
        return patterns
    
    async def _find_similar_issues(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Find similar issues in the codebase."""
        # This would use knowledge integration to find similar patterns
        return []
    
    def _generate_code_annotations(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Generate code annotations for visualization."""
        annotations = []
        
        if error.function_name:
            annotations.append({
                "type": "info",
                "message": f"Function: {error.function_name}",
                "line": error.line_number
            })
        
        if error.class_name:
            annotations.append({
                "type": "info",
                "message": f"Class: {error.class_name}",
                "line": error.line_number
            })
        
        return annotations
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust"
        }
        return language_map.get(ext, "text")

