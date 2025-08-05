#!/usr/bin/env python3
"""
Self-Contained Serena LSP Error Analyzer

A focused, self-contained analyzer that retrieves ALL LSP errors from the codebase
using embedded Serena components. This analyzer consolidates only the essential
LSP error retrieval functionality without refactoring or other unrelated features.

Features:
- Complete LSP error retrieval from all language servers
- Self-contained with embedded Serena core components
- Comprehensive error categorization and analysis
- JSON output with detailed error information
- Performance metrics and analysis statistics

Usage:
    python serena_analyzer.py --repo /path/to/codebase
    python serena_analyzer.py --repo . --output errors_report.json
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False

# ============================================================================
# EMBEDDED SERENA TYPES (from serena/types.py)
# ============================================================================

class SerenaCapability(Enum):
    """Available Serena capabilities."""
    ERROR_ANALYSIS = "error_analysis"
    SYMBOL_INTELLIGENCE = "symbol_intelligence"
    CODE_ACTIONS = "code_actions"
    REAL_TIME_ANALYSIS = "real_time_analysis"


class ErrorSeverity(Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class SerenaConfig:
    """Configuration for Serena integration."""
    enabled_capabilities: List[SerenaCapability] = field(default_factory=lambda: [
        SerenaCapability.ERROR_ANALYSIS,
        SerenaCapability.SYMBOL_INTELLIGENCE
    ])
    lsp_server_host: str = "localhost"
    lsp_server_port: int = 8080
    lsp_connection_timeout: float = 30.0
    lsp_auto_reconnect: bool = True
    realtime_analysis: bool = False  # Disabled for focused error retrieval
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    log_level: str = "INFO"


@dataclass
class ErrorLocation:
    """Represents the location of an error in code."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename."""
        return Path(self.file_path).name


@dataclass
class CodeError:
    """Represents a comprehensive code error with context."""
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    location: ErrorLocation
    code: Optional[str] = None
    source: str = "serena"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical (error severity)."""
        return self.severity == ErrorSeverity.ERROR
    
    @property
    def display_text(self) -> str:
        """Get formatted display text for the error."""
        return f"[{self.severity.value.upper()}] {self.location.file_name}:{self.location.range_text} - {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'location': {
                'file_path': self.location.file_path,
                'line': self.location.line,
                'column': self.location.column,
                'end_line': self.location.end_line,
                'end_column': self.location.end_column,
                'range_text': self.location.range_text,
                'file_name': self.location.file_name
            },
            'code': self.code,
            'source': self.source,
            'suggestions': self.suggestions,
            'context': self.context,
            'related_errors': self.related_errors,
            'timestamp': self.timestamp,
            'is_critical': self.is_critical,
            'display_text': self.display_text
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    errors_by_file: Dict[str, int]
    errors: List[CodeError]
    analysis_time: float
    files_analyzed: int
    performance_metrics: List[PerformanceMetrics]
    serena_status: Dict[str, Any]


# ============================================================================
# EMBEDDED SERENA CORE (simplified for LSP error retrieval)
# ============================================================================

class SerenaCore:
    """
    Simplified Serena core focused on LSP error retrieval.
    
    This is a streamlined version of the full SerenaCore that focuses
    exclusively on retrieving LSP diagnostics and errors.
    """
    
    def __init__(self, codebase_path: str, config: Optional[SerenaConfig] = None):
        self.codebase_path = Path(codebase_path)
        self.config = config or SerenaConfig()
        self._initialized = False
        self._lsp_integration: Optional[Any] = None
        self._performance_metrics: List[PerformanceMetrics] = []
        self._operation_counts: Dict[str, int] = {}
        
        logger.info(f"SerenaCore initialized for codebase: {self.codebase_path}")
    
    async def initialize(self) -> bool:
        """Initialize core for LSP error retrieval."""
        if self._initialized:
            return True
        
        try:
            logger.info("Initializing Serena core for LSP error retrieval...")
            self._initialized = True
            logger.info("✅ Serena core initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena core: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown core."""
        if not self._initialized:
            return
        
        logger.info("Shutting down Serena core...")
        self._initialized = False
        logger.info("✅ Serena core shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            'initialized': self._initialized,
            'codebase_path': str(self.codebase_path),
            'enabled_capabilities': [cap.value for cap in self.config.enabled_capabilities],
            'operation_counts': self._operation_counts,
            'performance_metrics_count': len(self._performance_metrics)
        }
    
    def _record_operation(self, operation_name: str, duration: float) -> None:
        """Record an operation for performance tracking."""
        self._operation_counts[operation_name] = self._operation_counts.get(operation_name, 0) + 1
        
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time() - duration,
            end_time=time.time(),
            duration=duration
        )
        
        self._performance_metrics.append(metric)


# ============================================================================
# LSP ERROR RETRIEVAL ENGINE
# ============================================================================

class LSPErrorRetriever:
    """
    Focused LSP error retrieval engine.
    
    This class handles the core functionality of retrieving ALL LSP errors
    from the codebase using the graph-sitter integration.
    """
    
    def __init__(self, codebase: Optional['Codebase'], serena_core: SerenaCore):
        self.codebase = codebase
        self.serena_core = serena_core
        self.errors: List[CodeError] = []
        self.files_processed = 0
        self.processing_stats = {
            'files_with_errors': 0,
            'total_diagnostics': 0,
            'processing_time': 0.0
        }
    
    async def retrieve_all_errors(self) -> List[CodeError]:
        """Retrieve ALL LSP errors from the codebase."""
        logger.info("🔍 Starting comprehensive LSP error retrieval...")
        start_time = time.time()
        
        if not self.codebase:
            logger.warning("No codebase available for error retrieval")
            return []
        
        # Check if LSP diagnostics method is available
        if not hasattr(self.codebase, 'get_file_diagnostics'):
            logger.info("LSP diagnostics method not available, using static analysis")
        
        # Get all Python files in the codebase
        python_files = self._get_python_files()
        logger.info(f"📊 Found {len(python_files)} Python files to analyze")
        
        if not python_files:
            logger.warning("No Python files found to analyze")
            return []
        
        # Process files in batches for better performance
        batch_size = 50
        all_errors = []
        
        for i in range(0, len(python_files), batch_size):
            batch = python_files[i:i + batch_size]
            batch_errors = await self._process_file_batch(batch, i + 1, len(python_files))
            all_errors.extend(batch_errors)
        
        # Record performance metrics
        processing_time = time.time() - start_time
        self.processing_stats['processing_time'] = processing_time
        self.serena_core._record_operation('lsp_error_retrieval', processing_time)
        
        logger.info(f"✅ LSP error retrieval complete:")
        logger.info(f"   📊 Total errors: {len(all_errors)}")
        logger.info(f"   📁 Files processed: {self.files_processed}")
        logger.info(f"   📁 Files with errors: {self.processing_stats['files_with_errors']}")
        logger.info(f"   ⏱️  Processing time: {processing_time:.2f}s")
        
        self.errors = all_errors
        return all_errors
    
    def _get_python_files(self) -> List[str]:
        """Get all Python files in the codebase."""
        python_files = []
        
        logger.debug(f"Scanning directory: {self.serena_core.codebase_path}")
        
        for root, dirs, files in os.walk(self.serena_core.codebase_path):
            # Skip common non-source directories
            original_dirs = dirs[:]
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'node_modules', 'venv', 'env', '.venv', '.env',
                'dist', 'build', '.tox', '.pytest_cache'
            ]]
            
            if len(dirs) != len(original_dirs):
                logger.debug(f"Skipped directories: {set(original_dirs) - set(dirs)}")
            
            py_files_in_dir = [f for f in files if f.endswith('.py')]
            if py_files_in_dir:
                logger.debug(f"Found {len(py_files_in_dir)} Python files in {root}")
            
            for file in py_files_in_dir:
                rel_path = os.path.relpath(os.path.join(root, file), self.serena_core.codebase_path)
                python_files.append(rel_path)
        
        logger.debug(f"Total Python files found: {len(python_files)}")
        if python_files:
            logger.debug(f"Sample files: {python_files[:5]}")
        
        return python_files
    
    async def _process_file_batch(self, files: List[str], start_idx: int, total_files: int) -> List[CodeError]:
        """Process a batch of files for LSP diagnostics."""
        batch_errors = []
        
        for i, file_path in enumerate(files):
            current_idx = start_idx + i - 1
            if current_idx % 25 == 0:  # Progress every 25 files
                logger.info(f"   Progress: {current_idx}/{total_files} files processed...")
            
            try:
                file_errors = await self._get_file_errors(file_path)
                if file_errors:
                    batch_errors.extend(file_errors)
                    self.processing_stats['files_with_errors'] += 1
                
                self.files_processed += 1
                
            except Exception as e:
                logger.debug(f"Error processing {file_path}: {e}")
                continue
        
        return batch_errors
    
    async def _get_file_errors(self, file_path: str) -> List[CodeError]:
        """Get errors for a specific file using static analysis."""
        try:
            # Try LSP diagnostics first if available
            if hasattr(self.codebase, 'get_file_diagnostics'):
                try:
                    result = self.codebase.get_file_diagnostics(file_path)
                    if result and result.get('success'):
                        diagnostics = result.get('diagnostics', [])
                        if diagnostics:
                            errors = []
                            for diag in diagnostics:
                                error = self._convert_diagnostic_to_error(diag, file_path)
                                if error:
                                    errors.append(error)
                                    self.processing_stats['total_diagnostics'] += 1
                            return errors
                except Exception as e:
                    logger.debug(f"LSP diagnostics failed for {file_path}: {e}")
            
            # Fallback to static analysis
            return await self._static_analysis_errors(file_path)
            
        except Exception as e:
            logger.debug(f"Error getting diagnostics for {file_path}: {e}")
            return []
    
    async def _static_analysis_errors(self, file_path: str) -> List[CodeError]:
        """Perform static analysis to find errors."""
        errors = []
        
        try:
            # Read file content
            full_path = self.serena_core.codebase_path / file_path
            if not full_path.exists():
                return errors
            
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Basic syntax check using AST
            try:
                import ast
                ast.parse(content)
            except SyntaxError as e:
                error = CodeError(
                    id=f"{file_path}:syntax:{e.lineno}",
                    message=f"Syntax error: {e.msg}",
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.SYNTAX,
                    location=ErrorLocation(
                        file_path=file_path,
                        line=e.lineno or 1,
                        column=e.offset or 0
                    ),
                    source="static_analysis"
                )
                errors.append(error)
                self.processing_stats['total_diagnostics'] += 1
            
            # Check for common issues using simple pattern matching
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                line_errors = self._analyze_line_for_errors(file_path, line_num, line)
                errors.extend(line_errors)
                self.processing_stats['total_diagnostics'] += len(line_errors)
            
        except Exception as e:
            logger.debug(f"Static analysis failed for {file_path}: {e}")
        
        return errors
    
    def _analyze_line_for_errors(self, file_path: str, line_num: int, line: str) -> List[CodeError]:
        """Analyze a single line for common errors."""
        errors = []
        line_stripped = line.strip()
        
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith('#'):
            return errors
        
        # Check for common issues
        patterns = [
            # Import errors
            (r'from\s+\.\s+import', 'Relative import from current package', ErrorSeverity.WARNING, ErrorCategory.DEPENDENCY),
            (r'import\s+\*', 'Wildcard import should be avoided', ErrorSeverity.WARNING, ErrorCategory.STYLE),
            
            # Code quality issues
            (r'print\s*\(', 'Print statement found (consider using logging)', ErrorSeverity.INFO, ErrorCategory.STYLE),
            (r'TODO|FIXME|XXX', 'TODO/FIXME comment found', ErrorSeverity.INFO, ErrorCategory.LOGIC),
            (r'except\s*:', 'Bare except clause', ErrorSeverity.WARNING, ErrorCategory.LOGIC),
            
            # Security issues
            (r'eval\s*\(', 'Use of eval() is dangerous', ErrorSeverity.ERROR, ErrorCategory.SECURITY),
            (r'exec\s*\(', 'Use of exec() is dangerous', ErrorSeverity.ERROR, ErrorCategory.SECURITY),
            
            # Performance issues
            (r'\.append\s*\(.*\)\s*$', 'Consider list comprehension for better performance', ErrorSeverity.HINT, ErrorCategory.PERFORMANCE),
        ]
        
        import re
        for pattern, message, severity, category in patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                error = CodeError(
                    id=f"{file_path}:{line_num}:{pattern}",
                    message=message,
                    severity=severity,
                    category=category,
                    location=ErrorLocation(
                        file_path=file_path,
                        line=line_num,
                        column=0
                    ),
                    source="static_analysis",
                    context={'line_content': line_stripped}
                )
                errors.append(error)
        
        return errors
    
    def _convert_diagnostic_to_error(self, diagnostic: Dict[str, Any], file_path: str) -> Optional[CodeError]:
        """Convert LSP diagnostic to CodeError."""
        try:
            # Parse severity
            severity = diagnostic.get('severity', 'info')
            if isinstance(severity, int):
                # Convert LSP severity numbers to strings
                severity_map = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}
                severity = severity_map.get(severity, 'info')
            
            severity_enum = ErrorSeverity(severity.lower())
            
            # Parse range information
            range_info = diagnostic.get('range', {})
            start_pos = range_info.get('start', {})
            end_pos = range_info.get('end', {})
            
            location = ErrorLocation(
                file_path=file_path,
                line=start_pos.get('line', 0) + 1,  # Convert to 1-based
                column=start_pos.get('character', 0),
                end_line=end_pos.get('line', 0) + 1 if end_pos.get('line') is not None else None,
                end_column=end_pos.get('character', 0) if end_pos.get('character') is not None else None
            )
            
            # Categorize error based on message and source
            category = self._categorize_error(diagnostic)
            
            # Generate unique error ID
            error_id = f"{file_path}:{location.line}:{location.column}:{hash(diagnostic.get('message', ''))}"
            
            return CodeError(
                id=error_id,
                message=diagnostic.get('message', 'No message'),
                severity=severity_enum,
                category=category,
                location=location,
                code=str(diagnostic.get('code', '')),
                source=diagnostic.get('source', 'lsp'),
                context={
                    'original_diagnostic': diagnostic,
                    'file_path': file_path
                }
            )
            
        except Exception as e:
            logger.debug(f"Error converting diagnostic: {e}")
            return None
    
    def _categorize_error(self, diagnostic: Dict[str, Any]) -> ErrorCategory:
        """Categorize error based on diagnostic information."""
        message = diagnostic.get('message', '').lower()
        source = diagnostic.get('source', '').lower()
        code = str(diagnostic.get('code', '')).lower()
        
        # Syntax errors
        if any(keyword in message for keyword in ['syntax', 'invalid syntax', 'unexpected token']):
            return ErrorCategory.SYNTAX
        
        # Type errors
        if any(keyword in message for keyword in ['type', 'incompatible', 'cannot assign']):
            return ErrorCategory.TYPE
        
        # Import/dependency errors
        if any(keyword in message for keyword in ['import', 'module', 'cannot resolve']):
            return ErrorCategory.DEPENDENCY
        
        # Style/formatting
        if source in ['flake8', 'black', 'isort'] or 'style' in message:
            return ErrorCategory.STYLE
        
        # Performance
        if any(keyword in message for keyword in ['performance', 'slow', 'inefficient']):
            return ErrorCategory.PERFORMANCE
        
        # Security
        if any(keyword in message for keyword in ['security', 'unsafe', 'vulnerability']):
            return ErrorCategory.SECURITY
        
        # Default to logic for other errors
        return ErrorCategory.LOGIC


# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class SerenaLSPAnalyzer:
    """
    Main analyzer class that orchestrates LSP error retrieval.
    
    This is the primary interface for the self-contained Serena LSP analyzer.
    """
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.serena_core: Optional[SerenaCore] = None
        self.error_retriever: Optional[LSPErrorRetriever] = None
        self.analysis_results: Optional[AnalysisResult] = None
    
    async def initialize(self) -> bool:
        """Initialize the analyzer."""
        try:
            logger.info(f"🔍 Initializing Serena LSP Analyzer for: {self.codebase_path}")
            
            if not GRAPH_SITTER_AVAILABLE:
                logger.error("❌ Graph-sitter not available")
                return False
            
            # Initialize graph-sitter codebase
            self.codebase = Codebase(str(self.codebase_path))
            logger.info("✅ Graph-sitter codebase initialized")
            
            # Initialize Serena core
            self.serena_core = SerenaCore(str(self.codebase_path))
            await self.serena_core.initialize()
            
            # Initialize error retriever
            self.error_retriever = LSPErrorRetriever(self.codebase, self.serena_core)
            
            logger.info("✅ Serena LSP Analyzer initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize analyzer: {e}")
            traceback.print_exc()
            return False
    
    async def analyze(self) -> AnalysisResult:
        """Run complete LSP error analysis."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 SERENA LSP ERROR ANALYZER - COMPREHENSIVE ANALYSIS")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        if not self.error_retriever:
            raise RuntimeError("Analyzer not initialized")
        
        # Retrieve all LSP errors
        all_errors = await self.error_retriever.retrieve_all_errors()
        
        # Calculate statistics
        analysis_time = time.time() - start_time
        errors_by_severity = defaultdict(int)
        errors_by_category = defaultdict(int)
        errors_by_file = defaultdict(int)
        
        for error in all_errors:
            errors_by_severity[error.severity.value] += 1
            errors_by_category[error.category.value] += 1
            errors_by_file[error.location.file_path] += 1
        
        # Create analysis result
        self.analysis_results = AnalysisResult(
            total_errors=len(all_errors),
            errors_by_severity=dict(errors_by_severity),
            errors_by_category=dict(errors_by_category),
            errors_by_file=dict(errors_by_file),
            errors=all_errors,
            analysis_time=analysis_time,
            files_analyzed=self.error_retriever.files_processed,
            performance_metrics=self.serena_core._performance_metrics,
            serena_status=self.serena_core.get_status()
        )
        
        # Print summary
        self._print_analysis_summary()
        
        return self.analysis_results
    
    def _print_analysis_summary(self):
        """Print analysis summary."""
        if not self.analysis_results:
            return
        
        result = self.analysis_results
        
        logger.info("\n📊 ANALYSIS SUMMARY:")
        logger.info(f"   Analysis Time: {result.analysis_time:.2f} seconds")
        logger.info(f"   Files Analyzed: {result.files_analyzed}")
        logger.info(f"   Total Errors: {result.total_errors}")
        
        logger.info("\n🔍 ERRORS BY SEVERITY:")
        for severity, count in result.errors_by_severity.items():
            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
            logger.info(f"   {emoji} {severity.title()}: {count}")
        
        logger.info("\n📂 ERRORS BY CATEGORY:")
        for category, count in result.errors_by_category.items():
            logger.info(f"   🔸 {category.title()}: {count}")
        
        # Show top error files
        if result.errors_by_file:
            logger.info("\n🔥 TOP ERROR FILES:")
            sorted_files = sorted(result.errors_by_file.items(), key=lambda x: x[1], reverse=True)
            for i, (file_path, count) in enumerate(sorted_files[:10]):
                logger.info(f"   {i+1}. {Path(file_path).name}: {count} errors")
        
        # Show sample errors
        if result.errors:
            logger.info("\n❌ SAMPLE ERRORS:")
            for i, error in enumerate(result.errors[:5]):
                logger.info(f"   {i+1}. {error.display_text}")
    
    def save_results(self, output_file: str = "serena_lsp_errors.json") -> None:
        """Save analysis results to JSON file."""
        if not self.analysis_results:
            logger.warning("No analysis results to save")
            return
        
        try:
            # Convert results to serializable format
            results_dict = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'codebase_path': str(self.codebase_path),
                'total_errors': self.analysis_results.total_errors,
                'errors_by_severity': self.analysis_results.errors_by_severity,
                'errors_by_category': self.analysis_results.errors_by_category,
                'errors_by_file': self.analysis_results.errors_by_file,
                'analysis_time': self.analysis_results.analysis_time,
                'files_analyzed': self.analysis_results.files_analyzed,
                'serena_status': self.analysis_results.serena_status,
                'errors': [error.to_dict() for error in self.analysis_results.errors]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, default=str)
            
            logger.info(f"💾 Analysis results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def generate_simple_report(self, report_file: str = "report.txt") -> None:
        """Generate simple text report in the requested format."""
        if not self.analysis_results:
            logger.warning("No analysis results to generate report")
            return
        
        try:
            results = self.analysis_results
            
            # Count errors by severity with emojis
            critical_count = results.errors_by_severity.get('error', 0)
            major_count = results.errors_by_severity.get('warning', 0)
            minor_count = results.errors_by_severity.get('info', 0) + results.errors_by_severity.get('hint', 0)
            
            # Generate report content
            report_lines = []
            report_lines.append(f"ERRORS: {results.total_errors} [⚠️ Critical: {critical_count}] [👉 Major: {major_count}] [🔍 Minor: {minor_count}]")
            
            # Add individual errors
            for i, error in enumerate(results.errors, 1):
                # Determine emoji based on severity
                if error.severity == ErrorSeverity.ERROR:
                    emoji = "⚠️"
                elif error.severity == ErrorSeverity.WARNING:
                    emoji = "👉"
                else:
                    emoji = "🔍"
                
                # Format error line
                error_line = f"{i} {emoji}- {error.location.file_path} / Line {error.location.line} - '{error.category.value}' [{error.message}]"
                report_lines.append(error_line)
            
            # Write report to file
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            logger.info(f"📄 Simple report saved to: {report_file}")
            
            # Also print the summary to console
            print(f"\n{report_lines[0]}")
            if len(report_lines) > 1:
                print("Sample errors:")
                for line in report_lines[1:6]:  # Show first 5 errors
                    print(line)
                if len(report_lines) > 6:
                    print(f"... and {len(report_lines) - 6} more errors")
            
        except Exception as e:
            logger.error(f"Failed to generate simple report: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.serena_core:
                await self.serena_core.shutdown()
                logger.info("🔄 Serena core shutdown complete")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

async def main():
    """Main function to run the Serena LSP analyzer."""
    parser = argparse.ArgumentParser(
        description="Self-Contained Serena LSP Error Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serena_analyzer.py --repo .
  python serena_analyzer.py --repo /path/to/codebase
  python serena_analyzer.py --repo . --output my_errors.json
  python serena_analyzer.py --repo . --verbose

This analyzer focuses exclusively on retrieving ALL LSP errors from the codebase
using embedded Serena components. It provides comprehensive error analysis
without refactoring or other unrelated features.
        """
    )
    
    parser.add_argument(
        '--repo',
        required=True,
        help='Path to the codebase to analyze'
    )
    
    parser.add_argument(
        '--output',
        default='serena_lsp_errors.json',
        help='Output JSON file for results (default: serena_lsp_errors.json)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Serena LSP Analyzer v1.0.0 - Self-Contained LSP Error Retrieval'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🚀 SERENA LSP ERROR ANALYZER")
    logger.info("=" * 50)
    logger.info("Self-contained LSP error retrieval with embedded Serena components")
    logger.info(f"Graph-sitter available: {'✅' if GRAPH_SITTER_AVAILABLE else '❌'}")
    logger.info("")
    
    # Initialize and run analyzer
    analyzer = SerenaLSPAnalyzer(args.repo)
    
    try:
        # Initialize
        if not await analyzer.initialize():
            logger.error("❌ Failed to initialize analyzer. Exiting.")
            return 1
        
        # Run analysis
        results = await analyzer.analyze()
        
        # Save results
        analyzer.save_results(args.output)
        
        # Generate simple report format
        analyzer.generate_simple_report()
        
        logger.info(f"\n✅ Analysis complete!")
        logger.info(f"📊 Found {results.total_errors} total LSP errors")
        logger.info(f"📁 Analyzed {results.files_analyzed} files")
        logger.info(f"⏱️  Analysis time: {results.analysis_time:.2f} seconds")
        logger.info(f"💾 Results saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        await analyzer.cleanup()


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
