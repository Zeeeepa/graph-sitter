"""
Analytics and Codebase Analysis Models

Models for storing codebase analysis results, metrics, and trends.
Integrates with existing graph_sitter.codebase.codebase_analysis functionality.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, StatusMixin


# Define enums
ANALYSIS_TYPE_ENUM = ENUM(
    'complexity', 'dependencies', 'dead_code', 'security', 'performance', 
    'quality', 'coverage', 'documentation', 'maintainability', 'technical_debt',
    name='analysis_type',
    create_type=False  # Type already created in extensions.sql
)

LANGUAGE_TYPE_ENUM = ENUM(
    'python', 'typescript', 'javascript', 'java', 'cpp', 'rust', 'go', 
    'php', 'ruby', 'swift', 'kotlin', 'csharp', 'sql', 'html', 'css', 
    'markdown', 'yaml', 'json', 'xml', 'shell', 'dockerfile', 'other',
    name='language_type',
    create_type=False
)


class AnalysisRun(AuditedModel, StatusMixin):
    """
    Analysis run tracking for codebase analysis executions.
    
    Tracks individual analysis runs across repositories and branches
    with comprehensive metadata and performance monitoring.
    """
    __tablename__ = 'analysis_runs'
    
    # Organization and repository relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    
    # Analysis identification
    branch_name = Column(String(255), nullable=False, default='main')
    commit_sha = Column(String(40), nullable=False, index=True)
    analysis_type = Column(ANALYSIS_TYPE_ENUM, nullable=False)
    
    # Analysis configuration
    tool_name = Column(String(100), nullable=False)  # graph-sitter, sonarqube, eslint, etc.
    tool_version = Column(String(50), nullable=True)
    configuration = Column('configuration', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Execution tracking
    started_at = Column('started_at', DatabaseModel.created_at.type, nullable=False)
    completed_at = Column('completed_at', DatabaseModel.created_at.type, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Results and metrics
    results = Column('results', DatabaseModel.metadata.type, nullable=False, default=dict)
    summary_metrics = Column('summary_metrics', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Quality scoring
    quality_score = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    complexity_score = Column(Numeric(5, 2), nullable=True)
    maintainability_score = Column(Numeric(5, 2), nullable=True)
    
    # Issue tracking
    total_issues = Column(Integer, nullable=False, default=0)
    critical_issues = Column(Integer, nullable=False, default=0)
    high_issues = Column(Integer, nullable=False, default=0)
    medium_issues = Column(Integer, nullable=False, default=0)
    low_issues = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error_details = Column('error_details', DatabaseModel.metadata.type, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    repository = relationship("Repository")
    project = relationship("Project")
    file_analyses = relationship("FileAnalysis", back_populates="analysis_run", cascade="all, delete-orphan")
    code_element_analyses = relationship("CodeElementAnalysis", back_populates="analysis_run", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="analysis_run", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index('idx_analysis_runs_org', 'organization_id'),
        Index('idx_analysis_runs_repo', 'repository_id'),
        Index('idx_analysis_runs_project', 'project_id'),
        Index('idx_analysis_runs_commit', 'commit_sha'),
        Index('idx_analysis_runs_type', 'analysis_type'),
        Index('idx_analysis_runs_tool', 'tool_name'),
        Index('idx_analysis_runs_started', 'started_at'),
        Index('idx_analysis_runs_status', 'status'),
        Index('idx_analysis_runs_quality', 'quality_score'),
    )
    
    def __init__(self, organization_id: str, repository_id: str, commit_sha: str, 
                 analysis_type: str, tool_name: str, **kwargs):
        """Initialize analysis run with required fields."""
        super().__init__(
            organization_id=organization_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            analysis_type=analysis_type,
            tool_name=tool_name,
            started_at=datetime.utcnow(),
            **kwargs
        )
    
    def complete_analysis(self, results: Dict[str, Any], quality_score: Optional[float] = None) -> None:
        """Mark analysis as completed with results."""
        self.completed_at = datetime.utcnow()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.results = results
        self.status = 'completed'
        
        if quality_score is not None:
            self.quality_score = Decimal(str(quality_score))
        
        # Extract summary metrics
        self._extract_summary_metrics(results)
    
    def fail_analysis(self, error_details: Dict[str, Any]) -> None:
        """Mark analysis as failed with error details."""
        self.completed_at = datetime.utcnow()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.status = 'failed'
        self.error_details = error_details
    
    def _extract_summary_metrics(self, results: Dict[str, Any]) -> None:
        """Extract summary metrics from analysis results."""
        # Extract issue counts
        issues = results.get('issues', [])
        self.total_issues = len(issues)
        
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for issue in issues:
            severity = issue.get('severity', 'low').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        self.critical_issues = severity_counts['critical']
        self.high_issues = severity_counts['high']
        self.medium_issues = severity_counts['medium']
        self.low_issues = severity_counts['low']
        
        # Extract complexity and maintainability scores
        metrics = results.get('metrics', {})
        self.complexity_score = metrics.get('complexity_score')
        self.maintainability_score = metrics.get('maintainability_score')
        
        # Store summary metrics
        self.summary_metrics = {
            'total_files': results.get('total_files', 0),
            'total_lines': results.get('total_lines', 0),
            'total_functions': results.get('total_functions', 0),
            'total_classes': results.get('total_classes', 0),
            'language_distribution': results.get('language_distribution', {}),
            'issue_summary': severity_counts,
        }
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis run summary."""
        return {
            'id': str(self.id),
            'repository_id': str(self.repository_id),
            'project_id': str(self.project_id) if self.project_id else None,
            'branch_name': self.branch_name,
            'commit_sha': self.commit_sha,
            'analysis_type': self.analysis_type,
            'tool_name': self.tool_name,
            'tool_version': self.tool_version,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_ms': self.duration_ms,
            'quality_score': float(self.quality_score) if self.quality_score else None,
            'complexity_score': float(self.complexity_score) if self.complexity_score else None,
            'maintainability_score': float(self.maintainability_score) if self.maintainability_score else None,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'high_issues': self.high_issues,
            'medium_issues': self.medium_issues,
            'low_issues': self.low_issues,
            'summary_metrics': self.summary_metrics,
        }


class FileAnalysis(DatabaseModel, AuditedModel):
    """
    File-level analysis results and metrics.
    
    Stores detailed analysis results for individual files within
    a codebase analysis run.
    """
    __tablename__ = 'file_analyses'
    
    # Analysis run relationship
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False)
    
    # File identification
    file_path = Column(Text, nullable=False, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    language = Column(LANGUAGE_TYPE_ENUM, nullable=True)
    
    # File metrics
    lines_of_code = Column(Integer, nullable=False, default=0)
    blank_lines = Column(Integer, nullable=False, default=0)
    comment_lines = Column(Integer, nullable=False, default=0)
    total_lines = Column(Integer, nullable=False, default=0)
    
    # Complexity metrics
    cyclomatic_complexity = Column(Integer, nullable=False, default=0)
    cognitive_complexity = Column(Integer, nullable=False, default=0)
    halstead_complexity = Column(Numeric(10, 4), nullable=True)
    
    # Code structure
    function_count = Column(Integer, nullable=False, default=0)
    class_count = Column(Integer, nullable=False, default=0)
    import_count = Column(Integer, nullable=False, default=0)
    
    # Quality metrics
    maintainability_index = Column(Numeric(5, 2), nullable=True)
    technical_debt_ratio = Column(Numeric(5, 4), nullable=True)
    
    # Issue tracking
    issue_count = Column(Integer, nullable=False, default=0)
    critical_issue_count = Column(Integer, nullable=False, default=0)
    
    # Detailed results
    analysis_results = Column('analysis_results', DatabaseModel.metadata.type, nullable=False, default=dict)
    issues = Column('issues', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="file_analyses")
    code_elements = relationship("CodeElementAnalysis", back_populates="file_analysis", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('analysis_run_id', 'file_path', name='uq_file_analysis_run_path'),
        Index('idx_file_analyses_run', 'analysis_run_id'),
        Index('idx_file_analyses_path', 'file_path'),
        Index('idx_file_analyses_name', 'file_name'),
        Index('idx_file_analyses_language', 'language'),
        Index('idx_file_analyses_complexity', 'cyclomatic_complexity'),
        Index('idx_file_analyses_maintainability', 'maintainability_index'),
    )
    
    def __init__(self, analysis_run_id: str, file_path: str, **kwargs):
        """Initialize file analysis with required fields."""
        file_name = file_path.split('/')[-1] if '/' in file_path else file_path
        super().__init__(
            analysis_run_id=analysis_run_id,
            file_path=file_path,
            file_name=file_name,
            **kwargs
        )
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update file metrics from analysis results."""
        self.lines_of_code = metrics.get('lines_of_code', self.lines_of_code)
        self.blank_lines = metrics.get('blank_lines', self.blank_lines)
        self.comment_lines = metrics.get('comment_lines', self.comment_lines)
        self.total_lines = metrics.get('total_lines', self.total_lines)
        self.cyclomatic_complexity = metrics.get('cyclomatic_complexity', self.cyclomatic_complexity)
        self.cognitive_complexity = metrics.get('cognitive_complexity', self.cognitive_complexity)
        self.halstead_complexity = metrics.get('halstead_complexity', self.halstead_complexity)
        self.function_count = metrics.get('function_count', self.function_count)
        self.class_count = metrics.get('class_count', self.class_count)
        self.import_count = metrics.get('import_count', self.import_count)
        self.maintainability_index = metrics.get('maintainability_index', self.maintainability_index)
        self.technical_debt_ratio = metrics.get('technical_debt_ratio', self.technical_debt_ratio)
    
    def add_issues(self, issues: List[Dict[str, Any]]) -> None:
        """Add issues found in the file."""
        self.issues = issues
        self.issue_count = len(issues)
        self.critical_issue_count = sum(1 for issue in issues if issue.get('severity') == 'critical')
    
    def get_file_summary(self) -> Dict[str, Any]:
        """Get file analysis summary."""
        return {
            'id': str(self.id),
            'analysis_run_id': str(self.analysis_run_id),
            'file_path': self.file_path,
            'file_name': self.file_name,
            'language': self.language,
            'lines_of_code': self.lines_of_code,
            'total_lines': self.total_lines,
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'cognitive_complexity': self.cognitive_complexity,
            'function_count': self.function_count,
            'class_count': self.class_count,
            'issue_count': self.issue_count,
            'critical_issue_count': self.critical_issue_count,
            'maintainability_index': float(self.maintainability_index) if self.maintainability_index else None,
            'technical_debt_ratio': float(self.technical_debt_ratio) if self.technical_debt_ratio else None,
        }


class CodeElementAnalysis(DatabaseModel, AuditedModel):
    """
    Code element (function, class, method) analysis results.
    
    Stores detailed analysis for individual code elements like functions,
    classes, and methods within files.
    """
    __tablename__ = 'code_element_analyses'
    
    # Relationships
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False)
    file_analysis_id = Column(UUID(as_uuid=True), ForeignKey('file_analyses.id', ondelete='CASCADE'), nullable=False)
    
    # Element identification
    element_type = Column(String(50), nullable=False)  # function, class, method, variable
    element_name = Column(String(255), nullable=False, index=True)
    qualified_name = Column(Text, nullable=False)  # Full qualified name
    
    # Location information
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    start_column = Column(Integer, nullable=True)
    end_column = Column(Integer, nullable=True)
    
    # Element metrics
    lines_of_code = Column(Integer, nullable=False, default=0)
    cyclomatic_complexity = Column(Integer, nullable=False, default=0)
    cognitive_complexity = Column(Integer, nullable=False, default=0)
    parameter_count = Column(Integer, nullable=False, default=0)
    
    # Usage and dependencies
    usage_count = Column(Integer, nullable=False, default=0)
    dependency_count = Column(Integer, nullable=False, default=0)
    is_public = Column(Boolean, nullable=False, default=True)
    is_tested = Column(Boolean, nullable=False, default=False)
    
    # Quality indicators
    has_documentation = Column(Boolean, nullable=False, default=False)
    documentation_coverage = Column(Numeric(5, 2), nullable=True)
    
    # Detailed analysis
    analysis_results = Column('analysis_results', DatabaseModel.metadata.type, nullable=False, default=dict)
    dependencies = Column('dependencies', DatabaseModel.metadata.type, nullable=False, default=list)
    usages = Column('usages', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="code_element_analyses")
    file_analysis = relationship("FileAnalysis", back_populates="code_elements")
    
    # Constraints
    __table_args__ = (
        Index('idx_code_elements_run', 'analysis_run_id'),
        Index('idx_code_elements_file', 'file_analysis_id'),
        Index('idx_code_elements_type', 'element_type'),
        Index('idx_code_elements_name', 'element_name'),
        Index('idx_code_elements_qualified', 'qualified_name'),
        Index('idx_code_elements_complexity', 'cyclomatic_complexity'),
        Index('idx_code_elements_usage', 'usage_count'),
        Index('idx_code_elements_location', 'start_line', 'end_line'),
    )
    
    def __init__(self, analysis_run_id: str, file_analysis_id: str, element_type: str, 
                 element_name: str, qualified_name: str, start_line: int, end_line: int, **kwargs):
        """Initialize code element analysis with required fields."""
        super().__init__(
            analysis_run_id=analysis_run_id,
            file_analysis_id=file_analysis_id,
            element_type=element_type,
            element_name=element_name,
            qualified_name=qualified_name,
            start_line=start_line,
            end_line=end_line,
            **kwargs
        )
    
    def update_complexity_metrics(self, cyclomatic: int, cognitive: int) -> None:
        """Update complexity metrics."""
        self.cyclomatic_complexity = cyclomatic
        self.cognitive_complexity = cognitive
    
    def update_usage_info(self, usage_count: int, dependency_count: int) -> None:
        """Update usage and dependency information."""
        self.usage_count = usage_count
        self.dependency_count = dependency_count
    
    def get_element_summary(self) -> Dict[str, Any]:
        """Get code element summary."""
        return {
            'id': str(self.id),
            'element_type': self.element_type,
            'element_name': self.element_name,
            'qualified_name': self.qualified_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'lines_of_code': self.lines_of_code,
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'cognitive_complexity': self.cognitive_complexity,
            'parameter_count': self.parameter_count,
            'usage_count': self.usage_count,
            'dependency_count': self.dependency_count,
            'is_public': self.is_public,
            'is_tested': self.is_tested,
            'has_documentation': self.has_documentation,
            'documentation_coverage': float(self.documentation_coverage) if self.documentation_coverage else None,
        }


class Metric(DatabaseModel, AuditedModel):
    """
    Flexible metric storage for analysis results.
    
    Stores various metrics and measurements from analysis runs
    with flexible typing and categorization.
    """
    __tablename__ = 'metrics'
    
    # Analysis run relationship
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Metric identification
    metric_name = Column(String(255), nullable=False, index=True)
    metric_category = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # integer, float, string, boolean, json
    
    # Metric values (store as text and convert based on type)
    value_text = Column(Text, nullable=True)
    value_numeric = Column(Numeric(15, 6), nullable=True)
    value_json = Column('value_json', DatabaseModel.metadata.type, nullable=True)
    
    # Metric metadata
    unit = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    # Context and tags
    context = Column('context', DatabaseModel.metadata.type, nullable=False, default=dict)
    tags = Column('tags', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="metrics")
    
    # Constraints
    __table_args__ = (
        Index('idx_metrics_run', 'analysis_run_id'),
        Index('idx_metrics_name', 'metric_name'),
        Index('idx_metrics_category', 'metric_category'),
        Index('idx_metrics_type', 'metric_type'),
        Index('idx_metrics_numeric', 'value_numeric'),
        Index('idx_metrics_context_gin', 'context', postgresql_using='gin'),
        Index('idx_metrics_tags_gin', 'tags', postgresql_using='gin'),
    )
    
    def __init__(self, analysis_run_id: str, metric_name: str, metric_category: str, 
                 metric_type: str, value: Any, **kwargs):
        """Initialize metric with required fields."""
        super().__init__(
            analysis_run_id=analysis_run_id,
            metric_name=metric_name,
            metric_category=metric_category,
            metric_type=metric_type,
            **kwargs
        )
        self.set_value(value)
    
    def set_value(self, value: Any) -> None:
        """Set metric value with appropriate type conversion."""
        if self.metric_type == 'integer':
            self.value_numeric = Decimal(str(int(value)))
            self.value_text = str(int(value))
        elif self.metric_type == 'float':
            self.value_numeric = Decimal(str(float(value)))
            self.value_text = str(float(value))
        elif self.metric_type == 'string':
            self.value_text = str(value)
        elif self.metric_type == 'boolean':
            self.value_text = str(bool(value)).lower()
        elif self.metric_type == 'json':
            self.value_json = value
            self.value_text = str(value)
        else:
            self.value_text = str(value)
    
    def get_value(self) -> Any:
        """Get metric value with appropriate type conversion."""
        if self.metric_type == 'integer':
            return int(self.value_numeric) if self.value_numeric else 0
        elif self.metric_type == 'float':
            return float(self.value_numeric) if self.value_numeric else 0.0
        elif self.metric_type == 'boolean':
            return self.value_text.lower() == 'true' if self.value_text else False
        elif self.metric_type == 'json':
            return self.value_json
        else:
            return self.value_text
    
    def get_metric_info(self) -> Dict[str, Any]:
        """Get metric information."""
        return {
            'id': str(self.id),
            'analysis_run_id': str(self.analysis_run_id),
            'metric_name': self.metric_name,
            'metric_category': self.metric_category,
            'metric_type': self.metric_type,
            'value': self.get_value(),
            'unit': self.unit,
            'description': self.description,
            'context': self.context,
            'tags': self.tags,
        }

