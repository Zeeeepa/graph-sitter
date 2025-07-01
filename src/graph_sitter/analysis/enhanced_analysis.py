"""
Enhanced codebase analysis integrating all analysis capabilities.

This module provides the main interface for comprehensive codebase analysis,
integrating metrics, call graph analysis, dead code detection, and dependency analysis
with database storage capabilities.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from graph_sitter.core.codebase import Codebase
from .database import (
    AnalysisDatabase, CodebaseRecord, FileRecord, FunctionRecord, 
    ClassRecord, FunctionCallRecord, DependencyRecord, ImportRecord
)
from .metrics import CodeMetrics, FunctionMetrics, ClassMetrics, FileMetrics
from .call_graph import CallGraphAnalyzer, CallGraphMetrics
from .dead_code import DeadCodeDetector, DeadCodeReport
from .dependency_analyzer import DependencyAnalyzer, DependencyMetrics, ImportAnalysis


class EnhancedCodebaseAnalysis:
    """
    Enhanced codebase analysis following graph-sitter.com patterns.
    
    Provides comprehensive analysis capabilities including:
    - Advanced code metrics
    - Call graph analysis
    - Dead code detection
    - Dependency analysis
    - Database storage and retrieval
    """
    
    def __init__(self, codebase: Codebase, db_path: str = ":memory:"):
        """Initialize enhanced analysis with codebase and database."""
        self.codebase = codebase
        self.db = AnalysisDatabase(db_path)
        
        # Initialize analyzers
        self.metrics_analyzer = CodeMetrics(codebase)
        self.call_graph_analyzer = CallGraphAnalyzer(codebase)
        self.dead_code_detector = DeadCodeDetector(codebase)
        self.dependency_analyzer = DependencyAnalyzer(codebase)
        
        self.codebase_id: Optional[int] = None
    
    def run_full_analysis(self, store_in_db: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive analysis of the entire codebase.
        
        Args:
            store_in_db: Whether to store results in database
            
        Returns:
            Dictionary containing all analysis results
        """
        print("🔍 Starting comprehensive codebase analysis...")
        
        # 1. Basic codebase metrics
        print("📊 Analyzing codebase metrics...")
        codebase_summary = self.metrics_analyzer.get_codebase_summary()
        
        # 2. File-level analysis
        print("📁 Analyzing files...")
        file_analyses = {}
        for file in self.codebase.files:
            file_analyses[file.filepath] = self.metrics_analyzer.analyze_file(file)
        
        # 3. Function-level analysis
        print("🔧 Analyzing functions...")
        function_analyses = {}
        for function in self.codebase.functions:
            function_analyses[function.qualified_name] = self.metrics_analyzer.analyze_function(function)
        
        # 4. Class-level analysis
        print("🏗️ Analyzing classes...")
        class_analyses = {}
        for class_def in self.codebase.classes:
            class_analyses[class_def.qualified_name] = self.metrics_analyzer.analyze_class(class_def)
        
        # 5. Call graph analysis
        print("📞 Analyzing call graph...")
        call_graph_metrics = self.call_graph_analyzer.get_call_graph_metrics()
        
        # 6. Dead code detection
        print("💀 Detecting dead code...")
        dead_code_report = self.dead_code_detector.analyze()
        
        # 7. Dependency analysis
        print("🔗 Analyzing dependencies...")
        dependency_metrics = self.dependency_analyzer.get_dependency_metrics()
        import_analysis = self.dependency_analyzer.analyze_imports()
        
        # 8. Circular dependency detection
        print("🔄 Detecting circular dependencies...")
        circular_dependencies = self.dependency_analyzer.find_circular_dependencies()
        
        # Compile comprehensive results
        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'codebase_summary': codebase_summary,
            'file_analyses': {path: asdict(analysis) for path, analysis in file_analyses.items()},
            'function_analyses': {name: asdict(analysis) for name, analysis in function_analyses.items()},
            'class_analyses': {name: asdict(analysis) for name, analysis in class_analyses.items()},
            'call_graph_metrics': asdict(call_graph_metrics),
            'dead_code_report': asdict(dead_code_report),
            'dependency_metrics': asdict(dependency_metrics),
            'import_analysis': asdict(import_analysis),
            'circular_dependencies': [asdict(cd) for cd in circular_dependencies],
            'analysis_insights': self._generate_insights(
                codebase_summary, call_graph_metrics, dead_code_report, 
                dependency_metrics, circular_dependencies
            )
        }
        
        # Store in database if requested
        if store_in_db:
            print("💾 Storing analysis results in database...")
            self.codebase_id = self._store_analysis_in_db(
                analysis_results, file_analyses, function_analyses, class_analyses
            )
            analysis_results['codebase_id'] = self.codebase_id
        
        print("✅ Analysis complete!")
        return analysis_results
    
    def get_function_context_analysis(self, function_name: str) -> Dict[str, Any]:
        """
        Get comprehensive context analysis for a function.
        
        Based on graph-sitter.com function context analysis patterns.
        """
        function = self._get_function_by_name(function_name)
        if not function:
            return {}
        
        # Get function metrics
        metrics = self.metrics_analyzer.analyze_function(function)
        
        # Get call graph context
        call_paths = self.call_graph_analyzer.find_call_paths(
            function.qualified_name, function.qualified_name, max_depth=5
        )
        
        # Get dependency context
        dependencies = self.dependency_analyzer.analyze_symbol_dependencies(
            function.qualified_name
        )
        
        # Get usage patterns
        usage_patterns = self._analyze_function_usage_patterns(function)
        
        return {
            'function': function.qualified_name,
            'metrics': asdict(metrics),
            'call_context': {
                'incoming_calls': len(function.call_sites) if hasattr(function, 'call_sites') else 0,
                'outgoing_calls': len(function.function_calls) if hasattr(function, 'function_calls') else 0,
                'call_paths': [asdict(path) for path in call_paths[:10]]  # Limit to top 10
            },
            'dependencies': dependencies,
            'usage_patterns': usage_patterns,
            'recommendations': self._generate_function_recommendations(function, metrics)
        }
    
    def get_codebase_health_score(self) -> Dict[str, Any]:
        """Calculate overall codebase health score."""
        if not self.codebase_id:
            # Run analysis if not done yet
            self.run_full_analysis()
        
        # Get metrics from database
        codebase_metrics = self.db.get_codebase_metrics(self.codebase_id)
        dead_code_candidates = self.db.get_dead_code_candidates(self.codebase_id)
        complex_functions = self.db.get_complex_functions(self.codebase_id)
        
        # Calculate health scores (0-100)
        maintainability_score = codebase_metrics.get('avg_maintainability', 50)
        complexity_score = max(0, 100 - codebase_metrics.get('avg_function_complexity', 5) * 10)
        dead_code_score = max(0, 100 - len(dead_code_candidates) * 2)
        
        overall_score = (maintainability_score * 0.4 + 
                        complexity_score * 0.3 + 
                        dead_code_score * 0.3)
        
        return {
            'overall_health_score': round(overall_score, 1),
            'maintainability_score': round(maintainability_score, 1),
            'complexity_score': round(complexity_score, 1),
            'dead_code_score': round(dead_code_score, 1),
            'health_rating': self._get_health_rating(overall_score),
            'recommendations': self._generate_health_recommendations(
                maintainability_score, complexity_score, dead_code_score
            )
        }
    
    def query_analysis_data(self, query_type: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Query stored analysis data with various filters.
        
        Args:
            query_type: Type of query ('dead_code', 'complex_functions', 'recursive_functions', etc.)
            **kwargs: Additional query parameters
            
        Returns:
            List of matching analysis results
        """
        if not self.codebase_id:
            return []
        
        if query_type == 'dead_code':
            return self.db.get_dead_code_candidates(self.codebase_id)
        elif query_type == 'complex_functions':
            min_complexity = kwargs.get('min_complexity', 10)
            return self.db.get_complex_functions(self.codebase_id, min_complexity)
        elif query_type == 'recursive_functions':
            return self.db.get_recursive_functions(self.codebase_id)
        elif query_type == 'call_graph':
            return self.db.get_call_graph_data(self.codebase_id)
        else:
            return []
    
    def generate_analysis_report(self, output_format: str = 'markdown') -> str:
        """Generate a comprehensive analysis report."""
        if not self.codebase_id:
            analysis_results = self.run_full_analysis()
        else:
            # Get stored results
            analysis_results = self._get_stored_analysis_results()
        
        if output_format == 'markdown':
            return self._generate_markdown_report(analysis_results)
        elif output_format == 'json':
            return json.dumps(analysis_results, indent=2)
        else:
            return str(analysis_results)
    
    def close(self):
        """Close database connection."""
        self.db.close()
    
    # Private helper methods
    
    def _store_analysis_in_db(self, analysis_results: Dict[str, Any],
                             file_analyses: Dict[str, FileMetrics],
                             function_analyses: Dict[str, FunctionMetrics],
                             class_analyses: Dict[str, ClassMetrics]) -> int:
        """Store analysis results in database."""
        
        # Store codebase record
        codebase_summary = analysis_results['codebase_summary']
        codebase_record = CodebaseRecord(
            path=getattr(self.codebase, 'path', '.'),
            name=getattr(self.codebase, 'name', 'Unknown'),
            total_files=codebase_summary['total_files'],
            total_functions=codebase_summary['total_functions'],
            total_classes=codebase_summary['total_classes'],
            total_imports=0,  # Would need to calculate
            total_symbols=codebase_summary['total_files'] + codebase_summary['total_functions'] + codebase_summary['total_classes'],
            analysis_timestamp=analysis_results['timestamp'],
            metadata=json.dumps({
                'maintainability_score': codebase_summary.get('maintainability_score', 0),
                'technical_debt_ratio': codebase_summary.get('technical_debt_ratio', 0)
            })
        )
        codebase_id = self.db.store_codebase(codebase_record)
        
        # Store file records
        file_id_map = {}
        for filepath, file_metrics in file_analyses.items():
            file_record = FileRecord(
                codebase_id=codebase_id,
                filepath=filepath,
                filename=file_metrics.filename,
                file_type='python',  # Default, could be detected
                lines_of_code=file_metrics.lines_of_code,
                functions_count=file_metrics.functions_count,
                classes_count=file_metrics.classes_count,
                imports_count=file_metrics.imports_count,
                complexity_score=file_metrics.complexity_score,
                maintainability_index=file_metrics.maintainability_index,
                metadata=json.dumps({
                    'test_coverage_estimate': file_metrics.test_coverage_estimate,
                    'documentation_coverage': file_metrics.documentation_coverage
                })
            )
            file_id = self.db.store_file(file_record)
            file_id_map[filepath] = file_id
        
        # Store function records
        for qualified_name, func_metrics in function_analyses.items():
            function = self._get_function_by_name(qualified_name)
            if function and hasattr(function, 'filepath'):
                file_id = file_id_map.get(function.filepath)
                if file_id:
                    function_record = FunctionRecord(
                        file_id=file_id,
                        name=func_metrics.name,
                        qualified_name=func_metrics.qualified_name,
                        start_line=0,  # Would need to extract from function
                        end_line=0,
                        lines_of_code=func_metrics.lines_of_code,
                        cyclomatic_complexity=func_metrics.cyclomatic_complexity,
                        parameters_count=func_metrics.parameters_count,
                        return_statements_count=func_metrics.return_statements_count,
                        call_sites_count=func_metrics.call_sites_count,
                        function_calls_count=func_metrics.function_calls_count,
                        is_recursive=func_metrics.is_recursive,
                        is_async=func_metrics.is_async,
                        is_generator=func_metrics.is_generator,
                        docstring="",  # Would need to extract
                        metadata=json.dumps({
                            'nesting_depth': func_metrics.nesting_depth,
                            'cognitive_complexity': func_metrics.cognitive_complexity,
                            'maintainability_index': func_metrics.maintainability_index
                        })
                    )
                    self.db.store_function(function_record)
        
        # Store class records
        for qualified_name, class_metrics in class_analyses.items():
            class_def = self._get_class_by_name(qualified_name)
            if class_def and hasattr(class_def, 'filepath'):
                file_id = file_id_map.get(class_def.filepath)
                if file_id:
                    class_record = ClassRecord(
                        file_id=file_id,
                        name=class_metrics.name,
                        qualified_name=class_metrics.qualified_name,
                        start_line=0,  # Would need to extract
                        end_line=0,
                        methods_count=class_metrics.methods_count,
                        attributes_count=class_metrics.attributes_count,
                        inheritance_depth=class_metrics.inheritance_depth,
                        parent_classes=json.dumps(class_metrics.parent_classes),
                        child_classes=json.dumps(class_metrics.child_classes),
                        is_abstract=class_metrics.is_abstract,
                        docstring="",  # Would need to extract
                        metadata=json.dumps({
                            'complexity_score': class_metrics.complexity_score,
                            'cohesion_score': class_metrics.cohesion_score,
                            'coupling_score': class_metrics.coupling_score
                        })
                    )
                    self.db.store_class(class_record)
        
        return codebase_id
    
    def _get_function_by_name(self, name: str):
        """Get function object by name."""
        for function in self.codebase.functions:
            if function.qualified_name == name or function.name == name:
                return function
        return None
    
    def _get_class_by_name(self, name: str):
        """Get class object by name."""
        for class_def in self.codebase.classes:
            if class_def.qualified_name == name or class_def.name == name:
                return class_def
        return None
    
    def _analyze_function_usage_patterns(self, function) -> Dict[str, Any]:
        """Analyze usage patterns for a function."""
        patterns = {
            'is_entry_point': function.name in ['main', '__main__', 'run'],
            'is_test_function': 'test' in function.name.lower(),
            'is_private': function.name.startswith('_'),
            'has_decorators': hasattr(function, 'decorators') and len(function.decorators) > 0,
            'usage_frequency': 'low'  # Would need call site analysis
        }
        
        # Determine usage frequency
        if hasattr(function, 'call_sites'):
            call_count = len(function.call_sites)
            if call_count == 0:
                patterns['usage_frequency'] = 'unused'
            elif call_count <= 2:
                patterns['usage_frequency'] = 'low'
            elif call_count <= 10:
                patterns['usage_frequency'] = 'medium'
            else:
                patterns['usage_frequency'] = 'high'
        
        return patterns
    
    def _generate_function_recommendations(self, function, metrics: FunctionMetrics) -> List[str]:
        """Generate recommendations for a function."""
        recommendations = []
        
        if metrics.cyclomatic_complexity > 10:
            recommendations.append("Consider breaking down this function to reduce complexity")
        
        if metrics.lines_of_code > 50:
            recommendations.append("Function is quite long, consider splitting into smaller functions")
        
        if metrics.parameters_count > 5:
            recommendations.append("Consider using a configuration object to reduce parameter count")
        
        if metrics.is_recursive and metrics.cyclomatic_complexity > 5:
            recommendations.append("Recursive function with high complexity - consider iterative approach")
        
        if metrics.maintainability_index < 20:
            recommendations.append("Low maintainability - consider refactoring")
        
        return recommendations
    
    def _generate_insights(self, codebase_summary: Dict[str, Any],
                          call_graph_metrics: CallGraphMetrics,
                          dead_code_report: DeadCodeReport,
                          dependency_metrics: DependencyMetrics,
                          circular_dependencies: List) -> Dict[str, Any]:
        """Generate high-level insights from analysis results."""
        insights = {
            'code_quality': 'good',  # Default
            'main_issues': [],
            'strengths': [],
            'improvement_areas': []
        }
        
        # Analyze code quality indicators
        if dead_code_report.total_dead_items > codebase_summary['total_functions'] * 0.1:
            insights['main_issues'].append(f"High amount of dead code: {dead_code_report.total_dead_items} items")
            insights['code_quality'] = 'needs_improvement'
        
        if len(circular_dependencies) > 0:
            insights['main_issues'].append(f"Circular dependencies detected: {len(circular_dependencies)}")
            insights['code_quality'] = 'needs_improvement'
        
        if codebase_summary.get('average_function_complexity', 0) > 8:
            insights['main_issues'].append("High average function complexity")
            insights['code_quality'] = 'needs_improvement'
        
        # Identify strengths
        if dead_code_report.total_dead_items < codebase_summary['total_functions'] * 0.05:
            insights['strengths'].append("Low amount of dead code")
        
        if len(circular_dependencies) == 0:
            insights['strengths'].append("No circular dependencies")
        
        # Suggest improvement areas
        if call_graph_metrics.max_call_depth > 10:
            insights['improvement_areas'].append("Reduce call depth complexity")
        
        if dependency_metrics.circular_dependencies > 0:
            insights['improvement_areas'].append("Resolve circular dependencies")
        
        return insights
    
    def _get_health_rating(self, score: float) -> str:
        """Get health rating based on score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_health_recommendations(self, maintainability: float, 
                                       complexity: float, dead_code: float) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        if maintainability < 50:
            recommendations.append("Focus on improving code maintainability through refactoring")
        
        if complexity < 50:
            recommendations.append("Reduce function complexity by breaking down large functions")
        
        if dead_code < 50:
            recommendations.append("Remove dead code to improve codebase cleanliness")
        
        return recommendations
    
    def _get_stored_analysis_results(self) -> Dict[str, Any]:
        """Get stored analysis results from database."""
        # This would retrieve and reconstruct analysis results from the database
        # For now, return empty dict
        return {}
    
    def _generate_markdown_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a markdown report from analysis results."""
        report = f"""# Codebase Analysis Report

Generated on: {analysis_results['timestamp']}

## Summary

- **Total Files**: {analysis_results['codebase_summary']['total_files']}
- **Total Functions**: {analysis_results['codebase_summary']['total_functions']}
- **Total Classes**: {analysis_results['codebase_summary']['total_classes']}
- **Average Function Complexity**: {analysis_results['codebase_summary'].get('average_function_complexity', 'N/A')}

## Call Graph Metrics

- **Total Function Calls**: {analysis_results['call_graph_metrics']['total_calls']}
- **Max Call Depth**: {analysis_results['call_graph_metrics']['max_call_depth']}
- **Recursive Functions**: {len(analysis_results['call_graph_metrics']['recursive_functions'])}

## Dead Code Analysis

- **Dead Functions**: {len(analysis_results['dead_code_report']['dead_functions'])}
- **Dead Classes**: {len(analysis_results['dead_code_report']['dead_classes'])}
- **Unused Imports**: {len(analysis_results['dead_code_report']['unused_imports'])}

## Dependency Analysis

- **Total Dependencies**: {analysis_results['dependency_metrics']['total_dependencies']}
- **Circular Dependencies**: {analysis_results['dependency_metrics']['circular_dependencies']}
- **Import Dependencies**: {analysis_results['dependency_metrics']['import_dependencies']}

## Key Insights

"""
        
        insights = analysis_results.get('analysis_insights', {})
        if insights.get('main_issues'):
            report += "### Main Issues\n"
            for issue in insights['main_issues']:
                report += f"- {issue}\n"
            report += "\n"
        
        if insights.get('strengths'):
            report += "### Strengths\n"
            for strength in insights['strengths']:
                report += f"- {strength}\n"
            report += "\n"
        
        if insights.get('improvement_areas'):
            report += "### Improvement Areas\n"
            for area in insights['improvement_areas']:
                report += f"- {area}\n"
            report += "\n"
        
        return report

