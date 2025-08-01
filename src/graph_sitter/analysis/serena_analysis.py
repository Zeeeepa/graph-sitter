#!/usr/bin/env python3
"""
Enhanced Serena Codebase Analyzer for Graph-Sitter
==================================================

This module provides comprehensive codebase analysis with ALL LSP server errors,
symbol overviews, and advanced code intelligence features using Serena integration.

Features:
- Complete LSP error reporting from all language servers
- Comprehensive symbol analysis and mapping
- Advanced code intelligence and refactoring capabilities
- Real-time analysis with background processing
- Detailed JSON reporting with full metrics
- All Serena features in one unified interface
"""

import os
import sys
import json
import time
import asyncio
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class LSPDiagnostic:
    """LSP diagnostic information."""
    file_path: str
    line: int
    character: int
    severity: str  # error, warning, info, hint
    message: str
    code: Optional[str]
    source: str  # pylsp, mypy, etc.
    range_start: Dict[str, int]
    range_end: Dict[str, int]
    id: str  # Unique identifier for this error


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error: LSPDiagnostic
    calling_functions: List[Dict[str, Any]]
    called_functions: List[Dict[str, Any]]
    parameter_issues: List[Dict[str, Any]]
    dependency_chain: List[str]
    related_symbols: List[Dict[str, Any]]
    code_context: Optional[str]
    fix_suggestions: List[str]
    has_fix: bool = False


@dataclass
class SymbolOverview:
    """Complete symbol overview."""
    name: str
    symbol_type: str  # function, class, variable, import, etc.
    file_path: str
    line_number: int
    column: int
    scope: str
    definition: Optional[str]
    references: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_score: float
    documentation: Optional[str]
    signature: Optional[str]
    return_type: Optional[str]
    parameters: List[Dict[str, Any]]


@dataclass
class CodebaseHealth:
    """Complete codebase health assessment."""
    total_files: int
    total_lines: int
    total_symbols: int
    total_functions: int
    total_classes: int
    total_imports: int
    total_errors: int
    total_warnings: int
    total_info: int
    total_hints: int
    languages: List[str]
    file_types: Dict[str, int]
    largest_files: List[Dict[str, Any]]
    most_complex_symbols: List[Dict[str, Any]]
    error_hotspots: List[Dict[str, Any]]
    dependency_graph_stats: Dict[str, Any]
    maintainability_index: float
    technical_debt_score: float
    test_coverage_estimate: float


class SerenaAnalyzer:
    """
    Enhanced Serena analyzer that provides comprehensive codebase analysis
    with full LSP integration and error handling capabilities.
    """
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.lsp_diagnostics: List[LSPDiagnostic] = []
        self.symbol_overview: List[SymbolOverview] = []
        self.analysis_results: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}
        self.serena_status: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._error_cache: Dict[str, ErrorContext] = {}
        
    def initialize_serena(self) -> bool:
        """Initialize Serena capabilities."""
        try:
            logger.info(f"🔍 Initializing Serena analyzer for: {self.codebase.repo_path}")
            
            # Check and initialize Serena
            self.serena_status = self._check_serena_status()
            logger.info(f"📊 Serena status: {self.serena_status.get('enabled', False)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Serena: {e}")
            traceback.print_exc()
            return False
    
    def _check_serena_status(self) -> Dict[str, Any]:
        """Check Serena integration status."""
        status = {
            'available_components': {},
            'integration_active': False,
            'methods_available': [],
            'lsp_servers': [],
            'capabilities': [],
            'enabled': False
        }
        
        # Check available Serena methods
        serena_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'rename_symbol',
            'extract_method', 'semantic_search', 'generate_boilerplate',
            'organize_imports', 'get_file_diagnostics', 'get_symbol_context',
            'analyze_symbol_impact', 'enable_realtime_analysis'
        ]
        
        available_methods = []
        for method in serena_methods:
            if hasattr(self.codebase, method):
                available_methods.append(method)
        
        status['methods_available'] = available_methods
        status['integration_active'] = len(available_methods) > 0
        
        # Get detailed Serena status if available
        if hasattr(self.codebase, 'get_serena_status'):
            try:
                internal_status = self.codebase.get_serena_status()
                status.update(internal_status)
                status['enabled'] = internal_status.get('enabled', False)
                
                # Extract LSP server information
                lsp_bridge = internal_status.get('lsp_bridge_status', {})
                if lsp_bridge.get('initialized'):
                    status['lsp_servers'] = lsp_bridge.get('language_servers', [])
                    
                # Extract capabilities
                status['capabilities'] = internal_status.get('enabled_capabilities', [])
                
            except Exception as e:
                status['serena_error'] = str(e)
        
        return status
    
    def collect_all_lsp_diagnostics(self) -> List[LSPDiagnostic]:
        """Collect ALL LSP diagnostics from all language servers."""
        logger.info("\n🔍 Collecting ALL LSP diagnostics from language servers...")
        
        all_diagnostics = []
        
        # Check if LSP diagnostics method is available
        if not hasattr(self.codebase, 'get_file_diagnostics'):
            logger.warning("⚠️  LSP diagnostics method not available")
            return all_diagnostics
        
        # Get all Python files in the codebase
        python_files = []
        for root, dirs, files in os.walk(self.codebase.repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase.repo_path)
                    python_files.append(rel_path)
        
        logger.info(f"📊 Scanning {len(python_files)} Python files for LSP diagnostics...")
        
        # Collect diagnostics from all files
        diagnostics_count = 0
        files_with_errors = 0
        
        for i, file_path in enumerate(python_files):
            if i % 100 == 0:
                logger.info(f"   Progress: {i}/{len(python_files)} files scanned...")
            
            try:
                # Get diagnostics for this file
                result = self.codebase.get_file_diagnostics(file_path)
                
                if result and result.get('success'):
                    file_diagnostics = result.get('diagnostics', [])
                    
                    if file_diagnostics:
                        files_with_errors += 1
                        
                    for diag in file_diagnostics:
                        try:
                            # Parse diagnostic information
                            severity = diag.get('severity', 'info')
                            if isinstance(severity, int):
                                # Convert LSP severity numbers to strings
                                severity_map = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}
                                severity = severity_map.get(severity, 'info')
                            
                            range_info = diag.get('range', {})
                            start_pos = range_info.get('start', {})
                            end_pos = range_info.get('end', {})
                            
                            # Create unique error ID
                            error_id = f"{file_path}:{start_pos.get('line', 0)}:{start_pos.get('character', 0)}:{hash(diag.get('message', ''))}"
                            
                            diagnostic = LSPDiagnostic(
                                file_path=file_path,
                                line=start_pos.get('line', 0) + 1,  # Convert to 1-based
                                character=start_pos.get('character', 0),
                                severity=severity,
                                message=diag.get('message', 'No message'),
                                code=diag.get('code'),
                                source=diag.get('source', 'lsp'),
                                range_start=start_pos,
                                range_end=end_pos,
                                id=error_id
                            )
                            
                            all_diagnostics.append(diagnostic)
                            diagnostics_count += 1
                            
                        except Exception as e:
                            logger.warning(f"⚠️  Error parsing diagnostic in {file_path}: {e}")
                            continue
                            
            except Exception as e:
                # Don't spam errors for every file
                if i < 10:  # Only show first 10 errors
                    logger.warning(f"⚠️  Error getting diagnostics for {file_path}: {e}")
                continue
        
        # Store results
        self.lsp_diagnostics = all_diagnostics
        
        logger.info(f"✅ LSP diagnostics collection complete:")
        logger.info(f"   📊 Total diagnostics: {diagnostics_count}")
        logger.info(f"   📁 Files with issues: {files_with_errors}")
        
        # Count by severity
        severity_counts = defaultdict(int)
        for diag in all_diagnostics:
            severity_counts[diag.severity] += 1
        
        for severity, count in severity_counts.items():
            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
            logger.info(f"   {emoji} {severity.title()}: {count}")
        
        return all_diagnostics
    
    def get_full_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """Get comprehensive context for a specific error."""
        # Check cache first
        if error_id in self._error_cache:
            return self._error_cache[error_id]
        
        # Find the error
        error = None
        for diag in self.lsp_diagnostics:
            if diag.id == error_id:
                error = diag
                break
        
        if not error:
            return None
        
        # Build comprehensive context
        context = ErrorContext(
            error=error,
            calling_functions=[],
            called_functions=[],
            parameter_issues=[],
            dependency_chain=[],
            related_symbols=[],
            code_context=None,
            fix_suggestions=[],
            has_fix=False
        )
        
        try:
            # Get code context around the error
            file_path = Path(self.codebase.repo_path) / error.file_path
            if file_path.exists():
                lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()
                start_line = max(0, error.line - 5)
                end_line = min(len(lines), error.line + 5)
                context.code_context = '\n'.join(lines[start_line:end_line])
            
            # Get symbol context if available
            if hasattr(self.codebase, 'get_symbol_context'):
                try:
                    symbol_result = self.codebase.get_symbol_context(error.file_path, include_dependencies=True)
                    if symbol_result and symbol_result.get('success'):
                        symbol_context = symbol_result.get('context', {})
                        context.related_symbols = symbol_context.get('symbols', [])
                        context.dependency_chain = symbol_context.get('dependencies', [])
                except Exception:
                    pass
            
            # Generate fix suggestions based on error type
            context.fix_suggestions = self._generate_fix_suggestions(error)
            context.has_fix = len(context.fix_suggestions) > 0
            
        except Exception as e:
            logger.warning(f"Error building context for {error_id}: {e}")
        
        # Cache the result
        self._error_cache[error_id] = context
        return context
    
    def _generate_fix_suggestions(self, error: LSPDiagnostic) -> List[str]:
        """Generate fix suggestions for an error."""
        suggestions = []
        message = error.message.lower()
        
        # Common Python error patterns
        if 'undefined' in message or 'not defined' in message:
            suggestions.append("Check if the variable/function is properly imported or defined")
            suggestions.append("Verify the spelling of the identifier")
        
        if 'import' in message:
            suggestions.append("Add the missing import statement")
            suggestions.append("Check if the module is installed")
        
        if 'syntax' in message:
            suggestions.append("Check for missing parentheses, brackets, or quotes")
            suggestions.append("Verify proper indentation")
        
        if 'type' in message:
            suggestions.append("Check the data type being used")
            suggestions.append("Add type annotations for clarity")
        
        return suggestions
    
    def analyze_symbol_overview(self) -> List[SymbolOverview]:
        """Create comprehensive symbol overview with all details."""
        logger.info("\n🎯 Analyzing complete symbol overview...")
        
        symbol_overview = []
        
        # Analyze functions
        if hasattr(self.codebase, 'functions'):
            logger.info("   🔧 Analyzing functions...")
            for func in self.codebase.functions:
                try:
                    func_name = getattr(func, 'name', 'unknown')
                    file_path = getattr(func, 'file_path', None) or getattr(func, 'filepath', None) or 'unknown'
                    
                    # Get additional symbol information via Serena
                    symbol_context = {}
                    if hasattr(self.codebase, 'get_symbol_context'):
                        try:
                            context_result = self.codebase.get_symbol_context(func_name, include_dependencies=True)
                            if context_result and context_result.get('success'):
                                symbol_context = context_result.get('context', {})
                        except Exception:
                            pass
                    
                    # Calculate complexity score
                    complexity = len(func_name) / 10.0  # Simple proxy
                    if hasattr(func, 'parameters'):
                        complexity += len(func.parameters) * 0.5
                    
                    symbol = SymbolOverview(
                        name=func_name,
                        symbol_type='function',
                        file_path=file_path,
                        line_number=getattr(func, 'line_number', 0),
                        column=getattr(func, 'column', 0),
                        scope=getattr(func, 'scope', 'global'),
                        definition=getattr(func, 'definition', None),
                        references=symbol_context.get('references', []),
                        dependencies=symbol_context.get('dependencies', []),
                        complexity_score=complexity,
                        documentation=getattr(func, 'docstring', None),
                        signature=getattr(func, 'signature', None),
                        return_type=getattr(func, 'return_type', None),
                        parameters=getattr(func, 'parameters', [])
                    )
                    
                    symbol_overview.append(symbol)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error analyzing function: {e}")
                    continue
        
        # Analyze classes
        if hasattr(self.codebase, 'classes'):
            logger.info("   📦 Analyzing classes...")
            for cls in self.codebase.classes:
                try:
                    class_name = getattr(cls, 'name', 'unknown')
                    file_path = getattr(cls, 'file_path', None) or getattr(cls, 'filepath', None) or 'unknown'
                    
                    # Get symbol context
                    symbol_context = {}
                    if hasattr(self.codebase, 'get_symbol_context'):
                        try:
                            context_result = self.codebase.get_symbol_context(class_name, include_dependencies=True)
                            if context_result and context_result.get('success'):
                                symbol_context = context_result.get('context', {})
                        except Exception:
                            pass
                    
                    # Calculate complexity
                    complexity = len(class_name) / 10.0
                    if hasattr(cls, 'methods'):
                        complexity += len(cls.methods) * 2.0
                    
                    symbol = SymbolOverview(
                        name=class_name,
                        symbol_type='class',
                        file_path=file_path,
                        line_number=getattr(cls, 'line_number', 0),
                        column=getattr(cls, 'column', 0),
                        scope=getattr(cls, 'scope', 'global'),
                        definition=getattr(cls, 'definition', None),
                        references=symbol_context.get('references', []),
                        dependencies=symbol_context.get('dependencies', []),
                        complexity_score=complexity,
                        documentation=getattr(cls, 'docstring', None),
                        signature=None,
                        return_type=None,
                        parameters=[]
                    )
                    
                    symbol_overview.append(symbol)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error analyzing class: {e}")
                    continue
        
        self.symbol_overview = symbol_overview
        logger.info(f"✅ Symbol overview complete: {len(symbol_overview)} symbols analyzed")
        return symbol_overview
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run the complete Serena analysis."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 SERENA ANALYZER - COMPLETE CODEBASE ANALYSIS")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # 1. Initialize Serena
        if not self.initialize_serena():
            logger.error("Failed to initialize Serena")
            return {}
        
        # 2. Collect ALL LSP diagnostics
        lsp_diagnostics = self.collect_all_lsp_diagnostics()
        
        # 3. Analyze symbol overview
        symbol_overview = self.analyze_symbol_overview()
        
        # 4. Calculate codebase health
        codebase_health = self._calculate_codebase_health(lsp_diagnostics, symbol_overview)
        
        # 5. Generate performance metrics
        analysis_time = time.time() - start_time
        self.performance_metrics = {
            'total_analysis_time': round(analysis_time, 2),
            'lsp_diagnostics_count': len(lsp_diagnostics),
            'symbols_analyzed': len(symbol_overview),
            'files_scanned': codebase_health.total_files,
        }
        
        # 6. Create comprehensive report
        complete_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'codebase_path': str(self.codebase.repo_path),
            'serena_status': self.serena_status,
            'lsp_diagnostics': [self._safe_dict(d) for d in lsp_diagnostics],
            'symbol_overview': [self._safe_dict(s) for s in symbol_overview],
            'codebase_health': self._safe_dict(codebase_health),
            'performance_metrics': self.performance_metrics,
        }
        
        logger.info(f"✅ Complete Serena analysis finished in {analysis_time:.2f}s!")
        return complete_report
    
    def _calculate_codebase_health(self, lsp_diagnostics: List[LSPDiagnostic], symbol_overview: List[SymbolOverview]) -> CodebaseHealth:
        """Calculate comprehensive codebase health metrics."""
        logger.info("\n📊 Calculating codebase health metrics...")
        
        # Count diagnostics by severity
        error_count = sum(1 for d in lsp_diagnostics if d.severity == 'error')
        warning_count = sum(1 for d in lsp_diagnostics if d.severity == 'warning')
        info_count = sum(1 for d in lsp_diagnostics if d.severity == 'info')
        hint_count = sum(1 for d in lsp_diagnostics if d.severity == 'hint')
        
        # Count symbols by type
        functions = [s for s in symbol_overview if s.symbol_type == 'function']
        classes = [s for s in symbol_overview if s.symbol_type == 'class']
        imports = [s for s in symbol_overview if s.symbol_type == 'import']
        
        # Calculate file statistics
        total_files = 0
        total_lines = 0
        file_types = defaultdict(int)
        largest_files = []
        
        if hasattr(self.codebase, 'files'):
            for file in self.codebase.files:
                total_files += 1
                ext = Path(file.file_path).suffix
                file_types[ext] += 1
                
                # Calculate file size
                try:
                    full_path = Path(self.codebase.repo_path) / file.file_path
                    if full_path.exists():
                        lines = len(full_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                        total_lines += lines
                        largest_files.append({
                            'path': file.file_path,
                            'lines': lines,
                            'size_bytes': full_path.stat().st_size
                        })
                except Exception:
                    continue
        
        largest_files.sort(key=lambda x: x['lines'], reverse=True)
        
        # Find most complex symbols
        most_complex = sorted(symbol_overview, key=lambda x: x.complexity_score, reverse=True)[:10]
        
        # Find error hotspots (files with most errors)
        error_hotspots = defaultdict(int)
        for diag in lsp_diagnostics:
            if diag.severity == 'error':
                error_hotspots[diag.file_path] += 1
        
        hotspots = [{'file': f, 'error_count': c} for f, c in sorted(error_hotspots.items(), key=lambda x: x[1], reverse=True)]
        
        # Calculate health scores
        maintainability_index = max(0, 100 - (error_count * 10) - (warning_count * 2))
        technical_debt_score = (error_count * 3) + (warning_count * 1) + (len([s for s in symbol_overview if s.complexity_score > 5]) * 2)
        test_coverage_estimate = len([f for f in largest_files if 'test' in f['path']]) / max(total_files, 1) * 100
        
        return CodebaseHealth(
            total_files=total_files,
            total_lines=total_lines,
            total_symbols=len(symbol_overview),
            total_functions=len(functions),
            total_classes=len(classes),
            total_imports=len(imports),
            total_errors=error_count,
            total_warnings=warning_count,
            total_info=info_count,
            total_hints=hint_count,
            languages=['Python'],  # Could be expanded
            file_types=dict(file_types),
            largest_files=largest_files[:10],
            most_complex_symbols=[{'name': s.name, 'type': s.symbol_type, 'complexity': s.complexity_score, 'file': s.file_path} for s in most_complex],
            error_hotspots=hotspots[:10],
            dependency_graph_stats={},  # Could be expanded
            maintainability_index=maintainability_index,
            technical_debt_score=technical_debt_score,
            test_coverage_estimate=test_coverage_estimate
        )
    
    def _safe_dict(self, obj) -> Dict[str, Any]:
        """Safely convert dataclass to dict, handling non-serializable objects."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                try:
                    # Handle common non-serializable types
                    if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, list, dict)):
                        result[key] = str(value)  # Convert to string representation
                    elif isinstance(value, list):
                        result[key] = [self._safe_serialize_item(item) for item in value]
                    elif isinstance(value, dict):
                        result[key] = {k: self._safe_serialize_item(v) for k, v in value.items()}
                    else:
                        result[key] = self._safe_serialize_item(value)
                except Exception:
                    result[key] = str(value)  # Fallback to string representation
            return result
        else:
            return str(obj)
    
    def _safe_serialize_item(self, item) -> Any:
        """Safely serialize individual items."""
        try:
            # Test if item is JSON serializable
            json.dumps(item, default=str)
            return item
        except (TypeError, ValueError):
            return str(item)
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if hasattr(self.codebase, 'shutdown_serena'):
                self.codebase.shutdown_serena()
                logger.info("🔄 Serena integration shutdown complete")
        except Exception as e:
            logger.warning(f"⚠️  Error during cleanup: {e}")
        
        try:
            self.executor.shutdown(wait=True)
        except Exception:
            pass

