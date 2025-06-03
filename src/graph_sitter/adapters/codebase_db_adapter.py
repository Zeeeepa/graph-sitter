"""
Codebase Database Adapter for Enhanced Analysis Integration

This adapter provides seamless integration between the existing 
graph_sitter/codebase/codebase_analysis.py functionality and the new 
comprehensive database schema.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)


@dataclass
class AnalysisResult:
    """Enhanced analysis result with database integration"""
    id: str
    codebase_id: str
    summary: str
    metrics: Dict[str, Any]
    quality_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: datetime


@dataclass
class CodebaseMetrics:
    """Comprehensive codebase metrics"""
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage: float
    languages: Dict[str, int]


class CodebaseDBAdapter:
    """
    Adapter for integrating existing codebase analysis with the new database schema.
    
    This adapter maintains backward compatibility while enhancing functionality
    with database storage, historical tracking, and advanced analytics.
    """
    
    def __init__(self, db_connection, organization_id: str):
        """
        Initialize the adapter with database connection and organization context.
        
        Args:
            db_connection: Database connection object
            organization_id: Organization UUID for multi-tenant isolation
        """
        self.db = db_connection
        self.organization_id = organization_id
    
    def analyze_codebase_enhanced(self, codebase: Codebase, 
                                 analysis_config: Optional[Dict] = None) -> AnalysisResult:
        """
        Enhanced codebase analysis with database storage and historical comparison.
        
        Args:
            codebase: Codebase object to analyze
            analysis_config: Optional configuration for analysis
            
        Returns:
            AnalysisResult with enhanced metrics and recommendations
        """
        # Use existing analysis function for backward compatibility
        legacy_summary = get_codebase_summary(codebase)
        
        # Create analysis run record
        analysis_run_id = self._create_analysis_run(codebase, analysis_config)
        
        # Enhanced metrics calculation
        metrics = self._calculate_enhanced_metrics(codebase)
        
        # Store detailed analysis results
        self._store_file_analyses(analysis_run_id, codebase)
        self._store_code_element_analyses(analysis_run_id, codebase)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(metrics)
        
        # Generate issues and recommendations
        issues = self._identify_issues(codebase, metrics)
        recommendations = self._generate_recommendations(metrics, issues)
        
        # Store aggregated results
        self._store_analysis_results(analysis_run_id, metrics, quality_score, issues)
        
        # Get historical trends for comparison
        trends = self._get_quality_trends(codebase.repository_id if hasattr(codebase, 'repository_id') else None)
        
        return AnalysisResult(
            id=analysis_run_id,
            codebase_id=self._get_or_create_codebase_id(codebase),
            summary=legacy_summary,
            metrics=metrics.__dict__,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
            created_at=datetime.utcnow()
        )
    
    def get_file_analysis_enhanced(self, file: SourceFile, 
                                  store_results: bool = True) -> Dict[str, Any]:
        """
        Enhanced file analysis with optional database storage.
        
        Args:
            file: SourceFile object to analyze
            store_results: Whether to store results in database
            
        Returns:
            Enhanced file analysis results
        """
        # Use existing analysis function
        legacy_summary = get_file_summary(file)
        
        # Enhanced file metrics
        file_metrics = self._calculate_file_metrics(file)
        
        # Store in database if requested
        if store_results:
            self._store_file_analysis(file, file_metrics)
        
        return {
            'legacy_summary': legacy_summary,
            'enhanced_metrics': file_metrics,
            'quality_score': self._calculate_file_quality_score(file_metrics),
            'issues': self._identify_file_issues(file, file_metrics),
            'recommendations': self._generate_file_recommendations(file_metrics)
        }
    
    def get_historical_analysis(self, codebase_id: str, 
                               days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical analysis results for trend analysis.
        
        Args:
            codebase_id: Codebase identifier
            days_back: Number of days to look back
            
        Returns:
            List of historical analysis results
        """
        query = """
        SELECT 
            ar.id,
            ar.created_at,
            ar.quality_score,
            ar.metrics,
            ar.total_issues,
            ar.critical_issues,
            ar.analysis_duration_ms
        FROM analysis_runs ar
        WHERE ar.codebase_id = %s
        AND ar.created_at >= NOW() - INTERVAL '%s days'
        ORDER BY ar.created_at DESC
        """
        
        with self.db.cursor() as cursor:
            cursor.execute(query, (codebase_id, days_back))
            results = cursor.fetchall()
            
        return [dict(row) for row in results]
    
    def get_quality_trends(self, repository_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quality trends for a repository or organization.
        
        Args:
            repository_id: Optional repository identifier
            
        Returns:
            Quality trends and statistics
        """
        if repository_id:
            return self._get_repository_quality_trends(repository_id)
        else:
            return self._get_organization_quality_trends()
    
    def compare_analyses(self, analysis_id_1: str, analysis_id_2: str) -> Dict[str, Any]:
        """
        Compare two analysis results to show improvements or regressions.
        
        Args:
            analysis_id_1: First analysis ID
            analysis_id_2: Second analysis ID
            
        Returns:
            Comparison results with deltas and insights
        """
        analysis_1 = self._get_analysis_by_id(analysis_id_1)
        analysis_2 = self._get_analysis_by_id(analysis_id_2)
        
        if not analysis_1 or not analysis_2:
            raise ValueError("One or both analysis results not found")
        
        return {
            'quality_score_delta': analysis_2['quality_score'] - analysis_1['quality_score'],
            'metrics_comparison': self._compare_metrics(analysis_1['metrics'], analysis_2['metrics']),
            'issues_delta': analysis_2['total_issues'] - analysis_1['total_issues'],
            'improvement_areas': self._identify_improvement_areas(analysis_1, analysis_2),
            'regression_areas': self._identify_regression_areas(analysis_1, analysis_2)
        }
    
    def _create_analysis_run(self, codebase: Codebase, config: Optional[Dict] = None) -> str:
        """Create a new analysis run record in the database."""
        analysis_id = str(uuid.uuid4())
        codebase_id = self._get_or_create_codebase_id(codebase)
        
        query = """
        INSERT INTO analysis_runs (
            id, organization_id, codebase_id, analysis_type, 
            configuration, status, started_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.db.cursor() as cursor:
            cursor.execute(query, (
                analysis_id,
                self.organization_id,
                codebase_id,
                'comprehensive',
                json.dumps(config or {}),
                'running',
                datetime.utcnow()
            ))
            self.db.commit()
        
        return analysis_id
    
    def _calculate_enhanced_metrics(self, codebase: Codebase) -> CodebaseMetrics:
        """Calculate enhanced metrics for the codebase."""
        files = list(codebase.files)
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        
        # Basic counts
        total_files = len(files)
        total_functions = len(functions)
        total_classes = len(classes)
        
        # Calculate total lines (approximation)
        total_lines = sum(len(file.content.split('\n')) if hasattr(file, 'content') else 0 
                         for file in files)
        
        # Calculate complexity score (simplified)
        complexity_score = self._calculate_complexity_score(functions, classes)
        
        # Calculate maintainability index (simplified)
        maintainability_index = self._calculate_maintainability_index(
            total_lines, complexity_score, total_functions
        )
        
        # Calculate technical debt ratio (simplified)
        technical_debt_ratio = self._calculate_technical_debt_ratio(codebase)
        
        # Language distribution
        languages = self._calculate_language_distribution(files)
        
        return CodebaseMetrics(
            total_files=total_files,
            total_functions=total_functions,
            total_classes=total_classes,
            total_lines=total_lines,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            technical_debt_ratio=technical_debt_ratio,
            test_coverage=0.0,  # Would need integration with coverage tools
            languages=languages
        )
    
    def _calculate_complexity_score(self, functions: List[Function], classes: List[Class]) -> float:
        """Calculate overall complexity score."""
        if not functions and not classes:
            return 0.0
        
        # Simplified complexity calculation
        function_complexity = len(functions) * 1.0  # Base complexity per function
        class_complexity = len(classes) * 2.0      # Classes are more complex
        
        total_elements = len(functions) + len(classes)
        if total_elements == 0:
            return 0.0
        
        return min((function_complexity + class_complexity) / total_elements, 10.0)
    
    def _calculate_maintainability_index(self, total_lines: int, complexity: float, 
                                       total_functions: int) -> float:
        """Calculate maintainability index (0-100 scale)."""
        if total_lines == 0:
            return 100.0
        
        # Simplified maintainability calculation
        # Higher lines and complexity reduce maintainability
        base_score = 100.0
        line_penalty = min(total_lines / 10000.0 * 20, 30)  # Max 30 point penalty
        complexity_penalty = min(complexity * 5, 25)        # Max 25 point penalty
        
        return max(base_score - line_penalty - complexity_penalty, 0.0)
    
    def _calculate_technical_debt_ratio(self, codebase: Codebase) -> float:
        """Calculate technical debt ratio."""
        # Simplified calculation based on code patterns
        # In a real implementation, this would analyze code smells, duplications, etc.
        total_symbols = len(list(codebase.symbols))
        if total_symbols == 0:
            return 0.0
        
        # Placeholder calculation - would need more sophisticated analysis
        return min(total_symbols / 1000.0, 1.0)
    
    def _calculate_language_distribution(self, files: List[SourceFile]) -> Dict[str, int]:
        """Calculate language distribution across files."""
        languages = {}
        for file in files:
            # Extract language from file extension (simplified)
            if hasattr(file, 'name') and '.' in file.name:
                ext = file.name.split('.')[-1].lower()
                language = self._extension_to_language(ext)
                languages[language] = languages.get(language, 0) + 1
        
        return languages
    
    def _extension_to_language(self, extension: str) -> str:
        """Map file extension to language."""
        mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'rs': 'rust',
            'go': 'go',
            'php': 'php',
            'rb': 'ruby',
            'swift': 'swift',
            'kt': 'kotlin',
            'cs': 'csharp',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'md': 'markdown',
            'yml': 'yaml',
            'yaml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'sh': 'shell'
        }
        return mapping.get(extension, 'other')
    
    def _calculate_quality_score(self, metrics: CodebaseMetrics) -> float:
        """Calculate overall quality score (0-100)."""
        # Weighted combination of different metrics
        maintainability_weight = 0.4
        complexity_weight = 0.3
        debt_weight = 0.3
        
        # Normalize complexity score (lower is better)
        normalized_complexity = max(0, 100 - (metrics.complexity_score * 10))
        
        # Normalize technical debt (lower is better)
        normalized_debt = max(0, 100 - (metrics.technical_debt_ratio * 100))
        
        quality_score = (
            metrics.maintainability_index * maintainability_weight +
            normalized_complexity * complexity_weight +
            normalized_debt * debt_weight
        )
        
        return round(quality_score, 2)
    
    def _identify_issues(self, codebase: Codebase, metrics: CodebaseMetrics) -> List[Dict[str, Any]]:
        """Identify issues in the codebase."""
        issues = []
        
        # High complexity issue
        if metrics.complexity_score > 7.0:
            issues.append({
                'type': 'high_complexity',
                'severity': 'warning',
                'message': f'High complexity score: {metrics.complexity_score:.1f}',
                'recommendation': 'Consider refactoring complex functions and classes'
            })
        
        # Low maintainability issue
        if metrics.maintainability_index < 50:
            issues.append({
                'type': 'low_maintainability',
                'severity': 'error',
                'message': f'Low maintainability index: {metrics.maintainability_index:.1f}',
                'recommendation': 'Improve code structure and reduce complexity'
            })
        
        # High technical debt issue
        if metrics.technical_debt_ratio > 0.5:
            issues.append({
                'type': 'high_technical_debt',
                'severity': 'warning',
                'message': f'High technical debt ratio: {metrics.technical_debt_ratio:.2f}',
                'recommendation': 'Address code smells and refactor problematic areas'
            })
        
        # Large codebase issue
        if metrics.total_lines > 100000:
            issues.append({
                'type': 'large_codebase',
                'severity': 'info',
                'message': f'Large codebase: {metrics.total_lines:,} lines',
                'recommendation': 'Consider modularization and architectural improvements'
            })
        
        return issues
    
    def _generate_recommendations(self, metrics: CodebaseMetrics, 
                                issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on metrics and issues."""
        recommendations = []
        
        # Extract recommendations from issues
        for issue in issues:
            if issue['recommendation'] not in recommendations:
                recommendations.append(issue['recommendation'])
        
        # Additional recommendations based on metrics
        if metrics.total_functions > 1000:
            recommendations.append('Consider implementing automated testing for better coverage')
        
        if len(metrics.languages) > 5:
            recommendations.append('Multiple languages detected - ensure consistent coding standards')
        
        if metrics.maintainability_index > 80:
            recommendations.append('Excellent maintainability - consider this as a reference for other projects')
        
        return recommendations
    
    def _get_or_create_codebase_id(self, codebase: Codebase) -> str:
        """Get or create codebase ID in the database."""
        # This would typically use repository information to identify the codebase
        # For now, generate a UUID (in real implementation, use repository ID)
        return str(uuid.uuid4())
    
    def _store_analysis_results(self, analysis_run_id: str, metrics: CodebaseMetrics,
                               quality_score: float, issues: List[Dict[str, Any]]):
        """Store aggregated analysis results."""
        query = """
        UPDATE analysis_runs 
        SET 
            status = 'completed',
            completed_at = %s,
            quality_score = %s,
            metrics = %s,
            total_issues = %s,
            critical_issues = %s
        WHERE id = %s
        """
        
        critical_issues = len([i for i in issues if i['severity'] == 'error'])
        
        with self.db.cursor() as cursor:
            cursor.execute(query, (
                datetime.utcnow(),
                quality_score,
                json.dumps(metrics.__dict__),
                len(issues),
                critical_issues,
                analysis_run_id
            ))
            self.db.commit()
    
    def _store_file_analyses(self, analysis_run_id: str, codebase: Codebase):
        """Store individual file analysis results."""
        # Implementation would store detailed file-level analysis
        pass
    
    def _store_code_element_analyses(self, analysis_run_id: str, codebase: Codebase):
        """Store code element (function/class) analysis results."""
        # Implementation would store detailed code element analysis
        pass
    
    def _calculate_file_metrics(self, file: SourceFile) -> Dict[str, Any]:
        """Calculate metrics for a single file."""
        return {
            'line_count': len(file.content.split('\n')) if hasattr(file, 'content') else 0,
            'function_count': len(file.functions),
            'class_count': len(file.classes),
            'import_count': len(file.imports),
            'complexity_score': len(file.functions) * 0.5 + len(file.classes) * 1.0
        }
    
    def _calculate_file_quality_score(self, file_metrics: Dict[str, Any]) -> float:
        """Calculate quality score for a single file."""
        # Simplified file quality calculation
        base_score = 100.0
        
        # Penalize very large files
        if file_metrics['line_count'] > 500:
            base_score -= min((file_metrics['line_count'] - 500) / 50, 30)
        
        # Penalize high complexity
        if file_metrics['complexity_score'] > 10:
            base_score -= min((file_metrics['complexity_score'] - 10) * 5, 25)
        
        return max(base_score, 0.0)
    
    def _identify_file_issues(self, file: SourceFile, 
                            file_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues in a single file."""
        issues = []
        
        if file_metrics['line_count'] > 1000:
            issues.append({
                'type': 'large_file',
                'severity': 'warning',
                'message': f'Large file: {file_metrics["line_count"]} lines'
            })
        
        if file_metrics['complexity_score'] > 15:
            issues.append({
                'type': 'high_complexity',
                'severity': 'error',
                'message': f'High complexity: {file_metrics["complexity_score"]:.1f}'
            })
        
        return issues
    
    def _generate_file_recommendations(self, file_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a single file."""
        recommendations = []
        
        if file_metrics['line_count'] > 500:
            recommendations.append('Consider splitting this file into smaller modules')
        
        if file_metrics['function_count'] > 20:
            recommendations.append('Consider organizing functions into classes or modules')
        
        return recommendations
    
    def _store_file_analysis(self, file: SourceFile, file_metrics: Dict[str, Any]):
        """Store file analysis results in database."""
        # Implementation would store file-level analysis
        pass
    
    def _get_repository_quality_trends(self, repository_id: str) -> Dict[str, Any]:
        """Get quality trends for a specific repository."""
        # Implementation would query historical data for trends
        return {
            'trend_direction': 'improving',
            'quality_score_change': 5.2,
            'period_days': 30
        }
    
    def _get_organization_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends for the entire organization."""
        # Implementation would query organization-wide trends
        return {
            'average_quality_score': 75.5,
            'total_projects': 12,
            'improving_projects': 8,
            'declining_projects': 2
        }
    
    def _get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis results by ID."""
        # Implementation would query database for analysis results
        return None
    
    def _compare_metrics(self, metrics_1: Dict, metrics_2: Dict) -> Dict[str, Any]:
        """Compare two sets of metrics."""
        # Implementation would compare metrics and calculate deltas
        return {}
    
    def _identify_improvement_areas(self, analysis_1: Dict, analysis_2: Dict) -> List[str]:
        """Identify areas that have improved between analyses."""
        return []
    
    def _identify_regression_areas(self, analysis_1: Dict, analysis_2: Dict) -> List[str]:
        """Identify areas that have regressed between analyses."""
        return []


# Example usage and integration
def create_enhanced_analyzer(db_connection, organization_id: str) -> CodebaseDBAdapter:
    """
    Factory function to create an enhanced codebase analyzer.
    
    Args:
        db_connection: Database connection
        organization_id: Organization UUID
        
    Returns:
        Configured CodebaseDBAdapter instance
    """
    return CodebaseDBAdapter(db_connection, organization_id)


# Backward compatibility wrapper
def get_codebase_summary_enhanced(codebase: Codebase, 
                                 db_adapter: Optional[CodebaseDBAdapter] = None) -> str:
    """
    Enhanced version of get_codebase_summary with optional database integration.
    
    This function maintains backward compatibility while providing enhanced features
    when a database adapter is provided.
    
    Args:
        codebase: Codebase to analyze
        db_adapter: Optional database adapter for enhanced features
        
    Returns:
        Codebase summary string (enhanced if db_adapter provided)
    """
    # Always provide the original functionality
    original_summary = get_codebase_summary(codebase)
    
    # If database adapter is provided, enhance with additional information
    if db_adapter:
        try:
            enhanced_result = db_adapter.analyze_codebase_enhanced(codebase)
            return f"{original_summary}\n\nEnhanced Analysis:\n" \
                   f"Quality Score: {enhanced_result.quality_score}/100\n" \
                   f"Issues Found: {len(enhanced_result.issues)}\n" \
                   f"Recommendations: {len(enhanced_result.recommendations)}"
        except Exception as e:
            # Fallback to original functionality if enhancement fails
            print(f"Enhanced analysis failed, using original: {e}")
            return original_summary
    
    return original_summary

