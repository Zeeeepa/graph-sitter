"""
Analysis Integration Adapter

Bridges existing graph_sitter.codebase.codebase_analysis functionality
with the new database models for seamless integration and backward compatibility.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from ..models.analytics import AnalysisRun, FileAnalysis, CodeElementAnalysis, Metric
from ..models.projects import Repository
from ..connection import database_session_scope
from ...codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)
from ...core.codebase import Codebase
from ...core.file import SourceFile
from ...core.class_definition import Class
from ...core.function import Function
from ...core.symbol import Symbol

logger = logging.getLogger(__name__)


class CodebaseAnalysisAdapter:
    """
    Adapter for integrating existing codebase analysis with database storage.
    
    Provides seamless integration between the existing graph-sitter analysis
    functions and the new database models while maintaining backward compatibility.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize adapter with optional database session."""
        self.session = session
        self._use_context_manager = session is None
    
    def analyze_and_store_codebase(
        self, 
        codebase: Codebase, 
        repository_id: str,
        organization_id: str,
        commit_sha: str,
        branch_name: str = 'main',
        project_id: Optional[str] = None,
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> AnalysisRun:
        """
        Analyze codebase and store results in database.
        
        This is the main integration point that takes an existing Codebase
        object and stores comprehensive analysis results in the database.
        """
        if self._use_context_manager:
            with database_session_scope() as session:
                return self._perform_analysis(
                    session, codebase, repository_id, organization_id,
                    commit_sha, branch_name, project_id, analysis_config
                )
        else:
            return self._perform_analysis(
                self.session, codebase, repository_id, organization_id,
                commit_sha, branch_name, project_id, analysis_config
            )
    
    def _perform_analysis(
        self,
        session: Session,
        codebase: Codebase,
        repository_id: str,
        organization_id: str,
        commit_sha: str,
        branch_name: str,
        project_id: Optional[str],
        analysis_config: Optional[Dict[str, Any]]
    ) -> AnalysisRun:
        """Perform the actual analysis and database storage."""
        
        logger.info(f"Starting codebase analysis for repository {repository_id}, commit {commit_sha}")
        
        # Create analysis run
        analysis_run = AnalysisRun(
            organization_id=organization_id,
            repository_id=repository_id,
            project_id=project_id,
            branch_name=branch_name,
            commit_sha=commit_sha,
            analysis_type='comprehensive',
            tool_name='graph-sitter',
            tool_version='1.0.0',
            configuration=analysis_config or {},
            status='running'
        )
        session.add(analysis_run)
        session.flush()  # Get the ID
        
        try:
            # Get codebase summary using existing function
            codebase_summary = get_codebase_summary(codebase)
            logger.info(f"Codebase summary: {codebase_summary}")
            
            # Analyze files
            file_analyses = self._analyze_files(session, analysis_run, codebase)
            
            # Analyze code elements
            code_element_analyses = self._analyze_code_elements(session, analysis_run, codebase, file_analyses)
            
            # Calculate metrics
            metrics = self._calculate_metrics(session, analysis_run, codebase, file_analyses, code_element_analyses)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(file_analyses, code_element_analyses, metrics)
            
            # Prepare results
            results = {
                'codebase_summary': codebase_summary,
                'total_files': len(list(codebase.files)),
                'total_functions': len(list(codebase.functions)),
                'total_classes': len(list(codebase.classes)),
                'total_symbols': len(list(codebase.symbols)),
                'total_imports': len(list(codebase.imports)),
                'total_external_modules': len(list(codebase.external_modules)),
                'language_distribution': self._get_language_distribution(codebase),
                'complexity_metrics': self._get_complexity_metrics(code_element_analyses),
                'quality_metrics': self._get_quality_metrics(file_analyses, code_element_analyses),
            }
            
            # Complete analysis
            analysis_run.complete_analysis(results, quality_score)
            
            # Update repository metadata
            self._update_repository_metadata(session, repository_id, results)
            
            logger.info(f"Analysis completed successfully. Quality score: {quality_score}")
            return analysis_run
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            analysis_run.fail_analysis({
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            })
            raise
    
    def _analyze_files(self, session: Session, analysis_run: AnalysisRun, codebase: Codebase) -> List[FileAnalysis]:
        """Analyze individual files and store results."""
        file_analyses = []
        
        for file in codebase.files:
            try:
                # Get file summary using existing function
                file_summary = get_file_summary(file)
                
                # Create file analysis
                file_analysis = FileAnalysis(
                    analysis_run_id=str(analysis_run.id),
                    file_path=file.name,
                    language=self._detect_language(file.name),
                )
                
                # Extract metrics from file
                self._extract_file_metrics(file_analysis, file, file_summary)
                
                session.add(file_analysis)
                file_analyses.append(file_analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file.name}: {str(e)}")
                continue
        
        session.flush()
        return file_analyses
    
    def _analyze_code_elements(
        self, 
        session: Session, 
        analysis_run: AnalysisRun, 
        codebase: Codebase,
        file_analyses: List[FileAnalysis]
    ) -> List[CodeElementAnalysis]:
        """Analyze code elements (functions, classes) and store results."""
        code_element_analyses = []
        
        # Create file path to analysis mapping
        file_analysis_map = {fa.file_path: fa for fa in file_analyses}
        
        # Analyze functions
        for function in codebase.functions:
            try:
                file_analysis = file_analysis_map.get(function.file.name)
                if not file_analysis:
                    continue
                
                function_summary = get_function_summary(function)
                
                element_analysis = CodeElementAnalysis(
                    analysis_run_id=str(analysis_run.id),
                    file_analysis_id=str(file_analysis.id),
                    element_type='function',
                    element_name=function.name,
                    qualified_name=f"{function.file.name}::{function.name}",
                    start_line=getattr(function, 'start_line', 0),
                    end_line=getattr(function, 'end_line', 0),
                )
                
                self._extract_function_metrics(element_analysis, function, function_summary)
                
                session.add(element_analysis)
                code_element_analyses.append(element_analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze function {function.name}: {str(e)}")
                continue
        
        # Analyze classes
        for cls in codebase.classes:
            try:
                file_analysis = file_analysis_map.get(cls.file.name)
                if not file_analysis:
                    continue
                
                class_summary = get_class_summary(cls)
                
                element_analysis = CodeElementAnalysis(
                    analysis_run_id=str(analysis_run.id),
                    file_analysis_id=str(file_analysis.id),
                    element_type='class',
                    element_name=cls.name,
                    qualified_name=f"{cls.file.name}::{cls.name}",
                    start_line=getattr(cls, 'start_line', 0),
                    end_line=getattr(cls, 'end_line', 0),
                )
                
                self._extract_class_metrics(element_analysis, cls, class_summary)
                
                session.add(element_analysis)
                code_element_analyses.append(element_analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze class {cls.name}: {str(e)}")
                continue
        
        session.flush()
        return code_element_analyses
    
    def _calculate_metrics(
        self,
        session: Session,
        analysis_run: AnalysisRun,
        codebase: Codebase,
        file_analyses: List[FileAnalysis],
        code_element_analyses: List[CodeElementAnalysis]
    ) -> List[Metric]:
        """Calculate and store various metrics."""
        metrics = []
        
        # Codebase-level metrics
        codebase_metrics = [
            ('total_files', 'codebase', 'integer', len(list(codebase.files))),
            ('total_functions', 'codebase', 'integer', len(list(codebase.functions))),
            ('total_classes', 'codebase', 'integer', len(list(codebase.classes))),
            ('total_symbols', 'codebase', 'integer', len(list(codebase.symbols))),
            ('total_imports', 'codebase', 'integer', len(list(codebase.imports))),
            ('total_external_modules', 'codebase', 'integer', len(list(codebase.external_modules))),
        ]
        
        for name, category, metric_type, value in codebase_metrics:
            metric = Metric(
                analysis_run_id=str(analysis_run.id),
                metric_name=name,
                metric_category=category,
                metric_type=metric_type,
                value=value
            )
            session.add(metric)
            metrics.append(metric)
        
        # File-level aggregated metrics
        if file_analyses:
            total_lines = sum(fa.total_lines for fa in file_analyses)
            total_complexity = sum(fa.cyclomatic_complexity for fa in file_analyses)
            avg_complexity = total_complexity / len(file_analyses) if file_analyses else 0
            
            file_metrics = [
                ('total_lines_of_code', 'aggregated', 'integer', total_lines),
                ('average_cyclomatic_complexity', 'aggregated', 'float', avg_complexity),
                ('files_with_high_complexity', 'aggregated', 'integer', 
                 sum(1 for fa in file_analyses if fa.cyclomatic_complexity > 10)),
            ]
            
            for name, category, metric_type, value in file_metrics:
                metric = Metric(
                    analysis_run_id=str(analysis_run.id),
                    metric_name=name,
                    metric_category=category,
                    metric_type=metric_type,
                    value=value
                )
                session.add(metric)
                metrics.append(metric)
        
        # Code element metrics
        if code_element_analyses:
            functions = [cea for cea in code_element_analyses if cea.element_type == 'function']
            classes = [cea for cea in code_element_analyses if cea.element_type == 'class']
            
            if functions:
                avg_function_complexity = sum(f.cyclomatic_complexity for f in functions) / len(functions)
                metric = Metric(
                    analysis_run_id=str(analysis_run.id),
                    metric_name='average_function_complexity',
                    metric_category='functions',
                    metric_type='float',
                    value=avg_function_complexity
                )
                session.add(metric)
                metrics.append(metric)
            
            if classes:
                avg_methods_per_class = sum(c.parameter_count for c in classes) / len(classes)
                metric = Metric(
                    analysis_run_id=str(analysis_run.id),
                    metric_name='average_methods_per_class',
                    metric_category='classes',
                    metric_type='float',
                    value=avg_methods_per_class
                )
                session.add(metric)
                metrics.append(metric)
        
        session.flush()
        return metrics
    
    def _extract_file_metrics(self, file_analysis: FileAnalysis, file: SourceFile, file_summary: str) -> None:
        """Extract metrics from file analysis."""
        # Basic counts
        file_analysis.function_count = len(file.functions)
        file_analysis.class_count = len(file.classes)
        file_analysis.import_count = len(file.imports)
        
        # Estimate lines of code (simplified)
        file_analysis.total_lines = len(file.symbols) * 5  # Rough estimate
        file_analysis.lines_of_code = int(file_analysis.total_lines * 0.7)  # Estimate
        file_analysis.comment_lines = int(file_analysis.total_lines * 0.2)  # Estimate
        file_analysis.blank_lines = file_analysis.total_lines - file_analysis.lines_of_code - file_analysis.comment_lines
        
        # Calculate complexity (simplified)
        file_analysis.cyclomatic_complexity = len(file.functions) + len(file.classes)
        file_analysis.cognitive_complexity = file_analysis.cyclomatic_complexity
        
        # Store analysis results
        file_analysis.analysis_results = {
            'summary': file_summary,
            'symbol_count': len(file.symbols),
            'import_details': [imp.name for imp in file.imports],
        }
    
    def _extract_function_metrics(self, element_analysis: CodeElementAnalysis, function: Function, function_summary: str) -> None:
        """Extract metrics from function analysis."""
        element_analysis.parameter_count = len(function.parameters)
        element_analysis.lines_of_code = len(function.return_statements) * 3  # Rough estimate
        element_analysis.cyclomatic_complexity = len(function.function_calls) + 1  # Simplified
        element_analysis.cognitive_complexity = element_analysis.cyclomatic_complexity
        element_analysis.usage_count = len(function.call_sites)
        element_analysis.dependency_count = len(function.dependencies)
        element_analysis.has_documentation = len(function.decorators) > 0  # Simplified check
        
        # Store analysis results
        element_analysis.analysis_results = {
            'summary': function_summary,
            'return_statements': len(function.return_statements),
            'function_calls': len(function.function_calls),
            'decorators': [d.name for d in function.decorators],
        }
    
    def _extract_class_metrics(self, element_analysis: CodeElementAnalysis, cls: Class, class_summary: str) -> None:
        """Extract metrics from class analysis."""
        element_analysis.parameter_count = len(cls.methods)  # Use methods as parameter count
        element_analysis.lines_of_code = len(cls.methods) * 5  # Rough estimate
        element_analysis.cyclomatic_complexity = len(cls.methods) + len(cls.attributes)
        element_analysis.cognitive_complexity = element_analysis.cyclomatic_complexity
        element_analysis.usage_count = len(cls.symbol_usages)
        element_analysis.dependency_count = len(cls.dependencies)
        element_analysis.has_documentation = len(cls.decorators) > 0  # Simplified check
        
        # Store analysis results
        element_analysis.analysis_results = {
            'summary': class_summary,
            'methods': len(cls.methods),
            'attributes': len(cls.attributes),
            'parent_classes': cls.parent_class_names,
            'decorators': [d.name for d in cls.decorators],
        }
    
    def _calculate_quality_score(
        self, 
        file_analyses: List[FileAnalysis], 
        code_element_analyses: List[CodeElementAnalysis],
        metrics: List[Metric]
    ) -> float:
        """Calculate overall quality score."""
        if not file_analyses:
            return 0.0
        
        # Simple quality scoring algorithm
        total_score = 0.0
        factors = 0
        
        # Factor 1: Complexity (lower is better)
        avg_complexity = sum(fa.cyclomatic_complexity for fa in file_analyses) / len(file_analyses)
        complexity_score = max(0, 100 - (avg_complexity * 5))  # Penalize high complexity
        total_score += complexity_score
        factors += 1
        
        # Factor 2: Documentation coverage
        documented_elements = sum(1 for cea in code_element_analyses if cea.has_documentation)
        total_elements = len(code_element_analyses)
        doc_score = (documented_elements / total_elements * 100) if total_elements > 0 else 50
        total_score += doc_score
        factors += 1
        
        # Factor 3: Code organization (functions per file)
        total_functions = sum(fa.function_count for fa in file_analyses)
        total_files = len(file_analyses)
        functions_per_file = total_functions / total_files if total_files > 0 else 0
        org_score = min(100, functions_per_file * 10)  # Reward organized code
        total_score += org_score
        factors += 1
        
        return round(total_score / factors, 2) if factors > 0 else 0.0
    
    def _get_language_distribution(self, codebase: Codebase) -> Dict[str, int]:
        """Get language distribution from codebase."""
        languages = {}
        for file in codebase.files:
            lang = self._detect_language(file.name)
            languages[lang] = languages.get(lang, 0) + 1
        return languages
    
    def _get_complexity_metrics(self, code_element_analyses: List[CodeElementAnalysis]) -> Dict[str, Any]:
        """Get complexity metrics summary."""
        if not code_element_analyses:
            return {}
        
        complexities = [cea.cyclomatic_complexity for cea in code_element_analyses]
        return {
            'average_complexity': sum(complexities) / len(complexities),
            'max_complexity': max(complexities),
            'min_complexity': min(complexities),
            'high_complexity_elements': sum(1 for c in complexities if c > 10),
        }
    
    def _get_quality_metrics(self, file_analyses: List[FileAnalysis], code_element_analyses: List[CodeElementAnalysis]) -> Dict[str, Any]:
        """Get quality metrics summary."""
        return {
            'total_files': len(file_analyses),
            'total_elements': len(code_element_analyses),
            'documented_elements': sum(1 for cea in code_element_analyses if cea.has_documentation),
            'average_file_complexity': sum(fa.cyclomatic_complexity for fa in file_analyses) / len(file_analyses) if file_analyses else 0,
            'files_with_issues': sum(1 for fa in file_analyses if fa.issue_count > 0),
        }
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        ext_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.sh': 'shell',
        }
        
        for ext, lang in ext_map.items():
            if filename.lower().endswith(ext):
                return lang
        
        return 'other'
    
    def _update_repository_metadata(self, session: Session, repository_id: str, results: Dict[str, Any]) -> None:
        """Update repository with analysis results."""
        try:
            repository = session.query(Repository).filter_by(id=repository_id).first()
            if repository:
                repository.update_analysis_metadata(results)
                session.add(repository)
        except Exception as e:
            logger.warning(f"Failed to update repository metadata: {str(e)}")


# Convenience functions for backward compatibility
def analyze_codebase_with_storage(
    codebase: Codebase,
    repository_id: str,
    organization_id: str,
    commit_sha: str,
    branch_name: str = 'main',
    project_id: Optional[str] = None,
    analysis_config: Optional[Dict[str, Any]] = None
) -> AnalysisRun:
    """
    Convenience function to analyze codebase and store results.
    
    This function provides a simple interface for existing code to
    use the new database storage without major changes.
    """
    adapter = CodebaseAnalysisAdapter()
    return adapter.analyze_and_store_codebase(
        codebase=codebase,
        repository_id=repository_id,
        organization_id=organization_id,
        commit_sha=commit_sha,
        branch_name=branch_name,
        project_id=project_id,
        analysis_config=analysis_config
    )


def get_latest_analysis_for_repository(repository_id: str, branch_name: str = 'main') -> Optional[AnalysisRun]:
    """Get the latest analysis run for a repository and branch."""
    with database_session_scope() as session:
        return session.query(AnalysisRun).filter_by(
            repository_id=repository_id,
            branch_name=branch_name,
            status='completed'
        ).order_by(AnalysisRun.completed_at.desc()).first()


def get_repository_quality_trend(repository_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get quality score trend for a repository over time."""
    with database_session_scope() as session:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        analyses = session.query(AnalysisRun).filter(
            AnalysisRun.repository_id == repository_id,
            AnalysisRun.status == 'completed',
            AnalysisRun.completed_at >= cutoff_date
        ).order_by(AnalysisRun.completed_at.asc()).all()
        
        return [
            {
                'date': analysis.completed_at.isoformat(),
                'quality_score': float(analysis.quality_score) if analysis.quality_score else None,
                'complexity_score': float(analysis.complexity_score) if analysis.complexity_score else None,
                'total_issues': analysis.total_issues,
                'commit_sha': analysis.commit_sha,
            }
            for analysis in analyses
        ]

