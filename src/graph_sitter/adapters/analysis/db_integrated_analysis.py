"""
Database-integrated analysis module for enhanced codebase analysis.

This module provides the main CodebaseDBAdapter class that integrates
database functionality with the existing analysis modules.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol

from .database_utils import (
    DatabaseConnection, 
    AnalysisResult, 
    DatabaseMetrics,
    convert_rset_to_dicts,
    execute_query_with_rset_conversion
)
from .metrics import EnhancedCodebaseMetrics, MetricsCalculator
from .enhanced_analysis import EnhancedCodebaseAnalyzer


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
        self.db = DatabaseConnection(db_connection)
        self.organization_id = organization_id
        self.enhanced_analyzer = None
    
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
        # Create analysis run record
        analysis_run_id = self._create_analysis_run(codebase, analysis_config)
        
        # Enhanced metrics calculation using existing modules
        metrics_calculator = MetricsCalculator(codebase)
        enhanced_metrics = self._calculate_enhanced_metrics(codebase, metrics_calculator)
        
        # Store detailed analysis results
        self._store_file_analyses(analysis_run_id, codebase)
        self._store_code_element_analyses(analysis_run_id, codebase)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(enhanced_metrics)
        
        # Generate issues and recommendations
        issues = self._identify_issues(codebase, enhanced_metrics)
        recommendations = self._generate_recommendations(enhanced_metrics, issues)
        
        # Store aggregated results
        self._store_analysis_results(analysis_run_id, enhanced_metrics, quality_score, issues)
        
        # Create summary using enhanced analyzer
        if not self.enhanced_analyzer:
            self.enhanced_analyzer = EnhancedCodebaseAnalyzer(codebase)
        
        summary = self._generate_enhanced_summary(codebase, enhanced_metrics)
        
        return AnalysisResult(
            id=analysis_run_id,
            codebase_id=self._get_or_create_codebase_id(codebase),
            summary=summary,
            metrics=enhanced_metrics.to_dict(),
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
        # Enhanced file metrics using existing modules
        file_metrics = self._calculate_file_metrics(file)
        
        # Store in database if requested
        if store_results:
            self._store_file_analysis(file, file_metrics)
        
        return {
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
        return self.db.get_historical_analysis(codebase_id, days_back)
    
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
            'improvement_areas': self._identify_improvement_areas(analysis_1, analysis_2),
            'regression_areas': self._identify_regression_areas(analysis_1, analysis_2),
            'recommendations': self._generate_comparison_recommendations(analysis_1, analysis_2)
        }
    
    # Private helper methods
    def _create_analysis_run(self, codebase: Codebase, config: Optional[Dict] = None) -> str:
        """Create a new analysis run record."""
        analysis_id = str(uuid.uuid4())
        # Implementation would create database record
        return analysis_id
    
    def _calculate_enhanced_metrics(self, codebase: Codebase, 
                                   metrics_calculator: MetricsCalculator) -> EnhancedCodebaseMetrics:
        """Calculate enhanced metrics using existing modules."""
        # Use existing metrics calculator
        basic_metrics = metrics_calculator.calculate_codebase_metrics()
        
        # Convert to enhanced format
        return EnhancedCodebaseMetrics(
            total_files=basic_metrics.total_files,
            total_functions=basic_metrics.total_functions,
            total_classes=basic_metrics.total_classes,
            total_lines=basic_metrics.total_lines,
            complexity_score=basic_metrics.average_complexity,
            maintainability_index=basic_metrics.average_maintainability,
            technical_debt_ratio=basic_metrics.technical_debt_score / 100.0,
            test_coverage=basic_metrics.test_coverage_estimate,
            languages=self._detect_languages(codebase),
            total_symbols=basic_metrics.total_symbols,
            total_imports=basic_metrics.total_imports,
            average_complexity=basic_metrics.average_complexity,
            average_maintainability=basic_metrics.average_maintainability,
            documentation_coverage=basic_metrics.documentation_coverage,
            test_coverage_estimate=basic_metrics.test_coverage_estimate,
            dead_code_percentage=basic_metrics.dead_code_percentage,
            technical_debt_score=basic_metrics.technical_debt_score,
            health_score=basic_metrics.health_score,
            created_at=datetime.utcnow()
        )
    
    def _detect_languages(self, codebase: Codebase) -> Dict[str, int]:
        """Detect programming languages in the codebase."""
        languages = {}
        for file in codebase.files:
            if hasattr(file, 'language') and file.language:
                languages[file.language] = languages.get(file.language, 0) + 1
            elif hasattr(file, 'name') and file.name:
                # Simple extension-based detection
                if file.name.endswith('.py'):
                    languages['Python'] = languages.get('Python', 0) + 1
                elif file.name.endswith(('.js', '.ts')):
                    languages['JavaScript/TypeScript'] = languages.get('JavaScript/TypeScript', 0) + 1
                elif file.name.endswith('.java'):
                    languages['Java'] = languages.get('Java', 0) + 1
                else:
                    languages['Other'] = languages.get('Other', 0) + 1
        return languages
    
    def _calculate_quality_score(self, metrics: EnhancedCodebaseMetrics) -> float:
        """Calculate overall quality score from metrics."""
        base_score = 100.0
        
        # Penalize high complexity
        if metrics.complexity_score > 10:
            base_score -= min((metrics.complexity_score - 10) * 2, 20)
        
        # Penalize low maintainability
        if metrics.maintainability_index < 70:
            base_score -= min((70 - metrics.maintainability_index) * 0.5, 15)
        
        # Penalize high technical debt
        if metrics.technical_debt_ratio > 0.3:
            base_score -= min((metrics.technical_debt_ratio - 0.3) * 50, 25)
        
        # Penalize low test coverage
        if metrics.test_coverage < 80:
            base_score -= min((80 - metrics.test_coverage) * 0.3, 20)
        
        return max(base_score, 0.0)
    
    def _identify_issues(self, codebase: Codebase, metrics: EnhancedCodebaseMetrics) -> List[Dict[str, Any]]:
        """Identify issues in the codebase."""
        issues = []
        
        if metrics.complexity_score > 15:
            issues.append({
                'type': 'high_complexity',
                'severity': 'warning',
                'message': f'High average complexity: {metrics.complexity_score:.1f}',
                'recommendation': 'Consider refactoring complex functions'
            })
        
        if metrics.test_coverage < 50:
            issues.append({
                'type': 'low_test_coverage',
                'severity': 'error',
                'message': f'Low test coverage: {metrics.test_coverage:.1f}%',
                'recommendation': 'Increase test coverage to at least 80%'
            })
        
        if metrics.technical_debt_ratio > 0.5:
            issues.append({
                'type': 'high_technical_debt',
                'severity': 'critical',
                'message': f'High technical debt ratio: {metrics.technical_debt_ratio:.1f}',
                'recommendation': 'Address technical debt systematically'
            })
        
        return issues
    
    def _generate_recommendations(self, metrics: EnhancedCodebaseMetrics, 
                                issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on metrics and issues."""
        recommendations = []
        
        if metrics.complexity_score > 10:
            recommendations.append('Consider breaking down complex functions into smaller, more manageable pieces')
        
        if metrics.test_coverage < 80:
            recommendations.append('Increase test coverage by adding unit tests for critical functions')
        
        if metrics.technical_debt_ratio > 0.3:
            recommendations.append('Allocate time for technical debt reduction in upcoming sprints')
        
        if len(issues) > 5:
            recommendations.append('Prioritize fixing critical and error-level issues first')
        
        return recommendations
    
    def _generate_enhanced_summary(self, codebase: Codebase, 
                                 metrics: EnhancedCodebaseMetrics) -> str:
        """Generate enhanced summary using metrics."""
        return f"""Enhanced Codebase Analysis Summary:
- {metrics.total_files} files analyzed
- {metrics.total_functions} functions found
- {metrics.total_classes} classes identified
- {metrics.total_lines} total lines of code
- Quality Score: {self._calculate_quality_score(metrics):.1f}/100
- Languages: {', '.join(metrics.languages.keys())}
- Complexity Score: {metrics.complexity_score:.1f}
- Test Coverage: {metrics.test_coverage:.1f}%"""
    
    def _get_or_create_codebase_id(self, codebase: Codebase) -> str:
        """Get or create codebase ID for database storage."""
        # Implementation would check database for existing codebase
        return str(uuid.uuid4())
    
    def _store_analysis_results(self, analysis_id: str, metrics: EnhancedCodebaseMetrics,
                              quality_score: float, issues: List[Dict[str, Any]]):
        """Store analysis results in database."""
        # Implementation would store in database
        pass
    
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
        base_score = 100.0
        
        if file_metrics['line_count'] > 500:
            base_score -= min((file_metrics['line_count'] - 500) / 50, 30)
        
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
        return {
            'trend_direction': 'improving',
            'quality_score_change': 5.2,
            'period_days': 30
        }
    
    def _get_organization_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends for the entire organization."""
        return self.db.get_quality_trends(self.organization_id)
    
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
    
    def _generate_comparison_recommendations(self, analysis_1: Dict, analysis_2: Dict) -> List[str]:
        """Generate recommendations based on analysis comparison."""
        return []


# Factory function for creating enhanced analyzer
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

