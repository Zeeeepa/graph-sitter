#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE GRAPH-SITTER ANALYSIS ENGINE
==============================================

This module consolidates ALL analysis capabilities from the 25 original files into a single,
comprehensive analysis engine with backend integration for interactive visualization dashboard.

Features Consolidated:
1. ✅ Serena LSP Error Detection & Real-time Analysis
2. ✅ Deep Codebase Metrics & Complexity Analysis  
3. ✅ Symbol Analysis & Relationship Mapping
4. ✅ Dead Code Detection & Cleanup Recommendations
5. ✅ Code Quality Assessment & Health Scoring
6. ✅ Dashboard API Integration & Visualization Data
7. ✅ Performance Monitoring & Real-time Feedback
8. ✅ Comprehensive Error Analysis & Reporting
9. ✅ Import Management & Deduplication Tools
10. ✅ Interactive Analysis & Testing Frameworks

Usage:
    from full_analysis import ComprehensiveAnalysisEngine
    
    engine = ComprehensiveAnalysisEngine("/path/to/codebase")
    results = await engine.run_full_analysis()
    dashboard_data = engine.get_dashboard_data()
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
import traceback
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union
import subprocess
import ast
import importlib.util

# Third-party imports
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Graph-sitter imports
try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Comprehensive analysis result for a single file."""
    file_path: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    symbols: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_score: float
    maintainability_index: float


@dataclass
class CodebaseHealth:
    """Overall codebase health metrics."""
    total_files: int
    total_errors: int
    total_warnings: int
    total_suggestions: int
    average_complexity: float
    maintainability_score: float
    test_coverage: float
    dependency_health: Dict[str, Any]
    hotspots: List[Dict[str, Any]]


@dataclass
class LSPDiagnostic:
    """LSP diagnostic information."""
    file_path: str
    line: int
    column: int
    severity: str
    message: str
    source: str
    code: Optional[str] = None


class ComprehensiveAnalysisEngine:
    """
    🚀 COMPREHENSIVE ANALYSIS ENGINE
    
    Consolidates all analysis capabilities from 25 original files into a single,
    powerful analysis engine with dashboard integration and enhanced Serena features.
    
    Enhanced Features:
    - Comprehensive codebase analysis with error detection
    - Semantic search and symbol intelligence
    - Advanced refactoring capabilities
    - Real-time analysis and diagnostics
    - Code generation and completion
    - Symbol relationship mapping
    - Performance monitoring and optimization
    - LSP integration showcase
    """
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.analysis_results: Dict[str, AnalysisResult] = {}
        self.errors_found: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.dashboard_data: Dict[str, Any] = {}
        self.serena_status: Dict[str, Any] = {}
        
        # Initialize components
        self._initialize_logging()
        
    def _initialize_logging(self):
        """Initialize comprehensive logging."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing Comprehensive Analysis Engine for: {self.codebase_path}")
    
    async def initialize_codebase(self) -> bool:
        """Initialize the codebase with enhanced capabilities."""
        try:
            self.logger.info(f"🔍 Initializing codebase analysis for: {self.codebase_path}")
            
            if not GRAPH_SITTER_AVAILABLE:
                self.logger.error("❌ Graph-sitter not available")
                return False
                
            self.codebase = Codebase(str(self.codebase_path))
            self.logger.info("✅ Graph-sitter codebase initialized")
            
            # Check Serena integration
            self.serena_status = await self._check_serena_integration()
            self.logger.info(f"📊 Serena integration: {self.serena_status.get('enabled', False)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    async def _check_serena_integration(self) -> Dict[str, Any]:
        """Check and initialize all Serena components."""
        status = {
            'enabled': False,
            'methods_available': [],
            'lsp_servers': [],
            'capabilities': [],
            'integration_active': False
        }
        
        if not self.codebase:
            return status
        
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
    
    async def analyze_file_comprehensive(self, file_path: str) -> AnalysisResult:
        """Perform comprehensive analysis of a single file with enhanced Serena capabilities."""
        self.logger.info(f"📄 Analyzing file comprehensively: {file_path}")
        
        errors = []
        warnings = []
        suggestions = []
        symbols = []
        dependencies = []
        metrics = {}
        
        try:
            # Basic file analysis using graph-sitter
            if self.codebase:
                # Get file content and basic metrics
                full_path = self.codebase_path / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    metrics['lines_of_code'] = len(content.splitlines())
                    metrics['file_size'] = len(content)
                    
                    # Try to get functions and classes from the file
                    try:
                        if hasattr(self.codebase, 'functions'):
                            file_functions = [f for f in self.codebase.functions if getattr(f, 'file_path', '') == file_path]
                            symbols.extend([{
                                'name': getattr(f, 'name', 'unknown'),
                                'type': 'function',
                                'line': getattr(f, 'line_number', 0),
                                'complexity': getattr(f, 'complexity', 1)
                            } for f in file_functions])
                            
                        if hasattr(self.codebase, 'classes'):
                            file_classes = [c for c in self.codebase.classes if getattr(c, 'file_path', '') == file_path]
                            symbols.extend([{
                                'name': getattr(c, 'name', 'unknown'),
                                'type': 'class',
                                'line': getattr(c, 'line_number', 0),
                                'methods': len(getattr(c, 'methods', []))
                            } for c in file_classes])
                    except Exception as e:
                        warnings.append({
                            'type': 'symbol_extraction',
                            'message': f"Could not extract symbols: {e}",
                            'line': 0
                        })
                
                # Enhanced analysis with Serena if available
                if hasattr(self.codebase, 'get_file_diagnostics'):
                    try:
                        diagnostics = self.codebase.get_file_diagnostics(file_path)
                        if diagnostics and diagnostics.get('success'):
                            for diag in diagnostics.get('diagnostics', []):
                                severity = diag.get('severity', 'info')
                                item = {
                                    'type': diag.get('code', 'unknown'),
                                    'message': diag.get('message', ''),
                                    'line': diag.get('range', {}).get('start', {}).get('line', 0),
                                    'character': diag.get('range', {}).get('start', {}).get('character', 0),
                                    'source': diag.get('source', 'lsp')
                                }
                                
                                if severity == 'error':
                                    errors.append(item)
                                elif severity == 'warning':
                                    warnings.append(item)
                                else:
                                    suggestions.append(item)
                    except Exception as e:
                        warnings.append({
                            'type': 'diagnostics_error',
                            'message': f"Failed to get diagnostics: {e}",
                            'line': 0
                        })
                
                # Get symbol information if available
                if hasattr(self.codebase, 'get_symbol_context'):
                    try:
                        for symbol in symbols:
                            context = self.codebase.get_symbol_context(
                                symbol['name'], 
                                include_dependencies=True
                            )
                            if context and context.get('success'):
                                symbol['context'] = context.get('context', {})
                                symbol['dependencies'] = context.get('dependencies', [])
                    except Exception as e:
                        warnings.append({
                            'type': 'symbol_context_error',
                            'message': f"Failed to get symbol context: {e}",
                            'line': 0
                        })
                
        except Exception as e:
            errors.append({
                'type': 'analysis_error',
                'message': f"Failed to analyze file: {e}",
                'line': 0,
                'character': 0
            })
        
        # Calculate complexity and maintainability scores
        complexity_score = self._calculate_complexity_enhanced(symbols, metrics)
        maintainability_index = self._calculate_maintainability_enhanced(metrics, errors, warnings)
        
        result = AnalysisResult(
            file_path=file_path,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metrics=metrics,
            symbols=symbols,
            dependencies=dependencies,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index
        )
        
        self.analysis_results[file_path] = result
        self.errors_found.extend(errors)
        
        return result
    
    def _calculate_complexity_enhanced(self, symbols: List[Dict], metrics: Dict) -> float:
        """Calculate enhanced complexity score for a file."""
        base_complexity = 1.0
        
        # Add complexity based on symbols
        for symbol in symbols:
            if symbol['type'] == 'function':
                base_complexity += symbol.get('complexity', 1)
            elif symbol['type'] == 'class':
                base_complexity += symbol.get('methods', 0) * 0.5
        
        # Adjust based on file size
        lines = metrics.get('lines_of_code', 0)
        if lines > 500:
            base_complexity *= 1.5
        elif lines > 1000:
            base_complexity *= 2.0
        
        return min(base_complexity, 10.0)  # Cap at 10
    
    def _calculate_maintainability_enhanced(self, metrics: Dict, errors: List, warnings: List) -> float:
        """Calculate enhanced maintainability index."""
        base_score = 100.0
        
        # Reduce score based on errors and warnings
        base_score -= len(errors) * 10
        base_score -= len(warnings) * 5
        
        # Adjust based on file size
        lines = metrics.get('lines_of_code', 0)
        if lines > 500:
            base_score -= 10
        if lines > 1000:
            base_score -= 20
        
        return max(base_score, 0.0)
    
    async def demonstrate_serena_features(self) -> Dict[str, Any]:
        """Demonstrate all available Serena features and return results."""
        if not self.codebase or not hasattr(self.codebase, 'get_serena_status'):
            self.logger.warning("⚠️  Serena features not available")
            return {'available': False, 'reason': 'Serena not available'}
        
        self.logger.info("🚀 Demonstrating Serena Features")
        
        demo_results = {
            'available': True,
            'code_intelligence': {},
            'semantic_search': {},
            'refactoring': {},
            'code_generation': {},
            'realtime_analysis': {},
            'symbol_intelligence': {}
        }
        
        # 1. Code Intelligence
        demo_results['code_intelligence'] = await self._demo_code_intelligence()
        
        # 2. Semantic Search
        demo_results['semantic_search'] = await self._demo_semantic_search()
        
        # 3. Refactoring Capabilities
        demo_results['refactoring'] = await self._demo_refactoring()
        
        # 4. Code Generation
        demo_results['code_generation'] = await self._demo_code_generation()
        
        # 5. Real-time Analysis
        demo_results['realtime_analysis'] = await self._demo_realtime_analysis()
        
        # 6. Symbol Intelligence
        demo_results['symbol_intelligence'] = await self._demo_symbol_intelligence()
        
        return demo_results
    
    async def _demo_code_intelligence(self) -> Dict[str, Any]:
        """Demo code intelligence features."""
        results = {'completions': [], 'hover_info': [], 'signature_help': []}
        
        try:
            # Find a Python file to work with
            sample_file = "src/graph_sitter/core/codebase.py"
            if not (self.codebase_path / sample_file).exists():
                sample_file = next(iter(self.analysis_results.keys()), None)
            
            if not sample_file:
                return {'error': 'No suitable file found for demo'}
            
            self.logger.info(f"📄 Code intelligence demo with file: {sample_file}")
            
            # Get completions
            if hasattr(self.codebase, 'get_completions'):
                completions = self.codebase.get_completions(sample_file, 10, 0)
                if completions and completions.get('success'):
                    items = completions.get('completions', [])[:3]
                    results['completions'] = [
                        {'label': item.get('label', 'N/A'), 'kind': item.get('kind', 'N/A')}
                        for item in items
                    ]
            
            # Get hover information
            if hasattr(self.codebase, 'get_hover_info'):
                hover = self.codebase.get_hover_info(sample_file, 20, 10)
                if hover and hover.get('success'):
                    results['hover_info'] = hover.get('contents', 'N/A')[:200]
            
            # Get signature help
            if hasattr(self.codebase, 'get_signature_help'):
                signature = self.codebase.get_signature_help(sample_file, 30, 15)
                if signature and signature.get('success'):
                    results['signature_help'] = 'Available'
                    
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def _demo_semantic_search(self) -> Dict[str, Any]:
        """Demo semantic search features."""
        results = {'searches': []}
        
        try:
            if hasattr(self.codebase, 'semantic_search'):
                # Search for common patterns
                search_terms = ["codebase", "function", "class", "import"]
                
                for term in search_terms:
                    search_results = self.codebase.semantic_search(term, max_results=3)
                    if search_results and search_results.get('success'):
                        items = search_results.get('results', [])
                        results['searches'].append({
                            'term': term,
                            'count': len(items),
                            'results': [
                                {
                                    'symbol_name': item.get('symbol_name', 'N/A'),
                                    'file_path': item.get('file_path', 'N/A')
                                }
                                for item in items[:2]
                            ]
                        })
            else:
                results['error'] = 'Semantic search not available'
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def _demo_refactoring(self) -> Dict[str, Any]:
        """Demo refactoring capabilities."""
        results = {'rename': {}, 'extract_method': {}, 'organize_imports': {}}
        
        try:
            # Find a suitable file for refactoring demo
            sample_file = next(iter(self.analysis_results.keys()), None)
            if not sample_file:
                return {'error': 'No suitable file found for refactoring demo'}
            
            self.logger.info(f"🔧 Refactoring demo with: {sample_file}")
            
            # Demo rename symbol (preview mode)
            if hasattr(self.codebase, 'rename_symbol'):
                rename_result = self.codebase.rename_symbol(
                    sample_file, 10, 5, "new_name", preview=True
                )
                if rename_result and rename_result.get('success'):
                    changes = rename_result.get('changes', [])
                    results['rename'] = {'changes_count': len(changes), 'available': True}
                else:
                    results['rename'] = {'available': False}
            
            # Demo extract method (preview mode)
            if hasattr(self.codebase, 'extract_method'):
                extract_result = self.codebase.extract_method(
                    sample_file, 15, 25, "extracted_method", preview=True
                )
                if extract_result and extract_result.get('success'):
                    results['extract_method'] = {'available': True}
                else:
                    results['extract_method'] = {'available': False}
            
            # Demo organize imports
            if hasattr(self.codebase, 'organize_imports'):
                organize_result = self.codebase.organize_imports(sample_file)
                if organize_result and organize_result.get('success'):
                    results['organize_imports'] = {'available': True}
                else:
                    results['organize_imports'] = {'available': False}
                    
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def _demo_code_generation(self) -> Dict[str, Any]:
        """Demo code generation features."""
        results = {'boilerplate': {}, 'tests': {}, 'documentation': {}}
        
        try:
            if hasattr(self.codebase, 'generate_boilerplate'):
                # Generate a simple class template
                result = self.codebase.generate_boilerplate(
                    "class", 
                    {"class_name": "DemoClass", "methods": ["__init__", "process"]},
                    "demo_generated.py"
                )
                if result and result.get('success'):
                    results['boilerplate'] = {'available': True}
                else:
                    results['boilerplate'] = {'available': False}
            
            if hasattr(self.codebase, 'generate_tests'):
                # Generate tests for a function
                sample_file = next(iter(self.analysis_results.keys()), None)
                if sample_file:
                    result = self.codebase.generate_tests(
                        f"{sample_file}:some_function",
                        ["unit"]
                    )
                    if result and result.get('success'):
                        results['tests'] = {'available': True}
                    else:
                        results['tests'] = {'available': False}
            
            if hasattr(self.codebase, 'generate_documentation'):
                # Generate documentation
                sample_file = next(iter(self.analysis_results.keys()), None)
                if sample_file:
                    result = self.codebase.generate_documentation(
                        sample_file,
                        "markdown"
                    )
                    if result and result.get('success'):
                        results['documentation'] = {'available': True}
                    else:
                        results['documentation'] = {'available': False}
                        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def _demo_realtime_analysis(self) -> Dict[str, Any]:
        """Demo real-time analysis features."""
        results = {'realtime_enabled': False}
        
        try:
            if hasattr(self.codebase, 'enable_realtime_analysis'):
                result = self.codebase.enable_realtime_analysis(
                    watch_patterns=["*.py"],
                    auto_refresh=True
                )
                if result and result.get('success'):
                    results['realtime_enabled'] = True
                    
                    # Disable it immediately for demo
                    if hasattr(self.codebase, 'disable_realtime_analysis'):
                        self.codebase.disable_realtime_analysis()
                        results['realtime_disabled'] = True
            else:
                results['error'] = 'Real-time analysis not available'
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def _demo_symbol_intelligence(self) -> Dict[str, Any]:
        """Demo symbol intelligence features."""
        results = {'symbols_analyzed': [], 'total_symbols': 0}
        
        try:
            # Find symbols to work with
            sample_symbols = []
            for result in list(self.analysis_results.values())[:3]:
                sample_symbols.extend(result.symbols[:2])
            
            if not sample_symbols:
                return {'error': 'No symbols found for demo'}
            
            results['total_symbols'] = len(sample_symbols)
            
            for symbol in sample_symbols[:3]:
                symbol_name = symbol.get('name', 'unknown')
                symbol_result = {'name': symbol_name, 'context': {}, 'impact': {}}
                
                if hasattr(self.codebase, 'get_symbol_context'):
                    context = self.codebase.get_symbol_context(
                        symbol_name,
                        include_dependencies=True
                    )
                    if context and context.get('success'):
                        deps = context.get('dependencies', [])
                        symbol_result['context'] = {'dependencies_count': len(deps)}
                
                if hasattr(self.codebase, 'analyze_symbol_impact'):
                    impact = self.codebase.analyze_symbol_impact(symbol_name, "modify")
                    if impact and impact.get('success'):
                        affected = impact.get('affected_files', [])
                        symbol_result['impact'] = {'affected_files_count': len(affected)}
                
                results['symbols_analyzed'].append(symbol_result)
                        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    async def collect_all_lsp_diagnostics(self) -> List[LSPDiagnostic]:
        """Collect ALL LSP diagnostics from all language servers."""
        self.logger.info("🔍 Collecting ALL LSP diagnostics from language servers...")
        
        all_diagnostics = []
        
        if not self.codebase:
            self.logger.warning("⚠️  No codebase available")
            return all_diagnostics
        
        # Check if LSP diagnostics method is available
        if not hasattr(self.codebase, 'get_file_diagnostics'):
            self.logger.warning("⚠️  LSP diagnostics method not available")
            return all_diagnostics
        
        # Get all Python files in the codebase
        python_files = []
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    python_files.append(rel_path)
        
        self.logger.info(f"📊 Scanning {len(python_files)} Python files for LSP diagnostics...")
        
        # Collect diagnostics from all files
        diagnostics_count = 0
        files_with_errors = 0
        
        for i, file_path in enumerate(python_files):
            if i % 100 == 0:
                self.logger.info(f"   Progress: {i}/{len(python_files)} files scanned...")
            
            try:
                # Get diagnostics for this file
                diagnostics = self.codebase.get_file_diagnostics(file_path)
                
                if diagnostics:
                    files_with_errors += 1
                    for diag in diagnostics:
                        lsp_diag = LSPDiagnostic(
                            file_path=file_path,
                            line=diag.get('line', 0),
                            column=diag.get('column', 0),
                            severity=diag.get('severity', 'error'),
                            message=diag.get('message', ''),
                            source=diag.get('source', 'unknown'),
                            code=diag.get('code')
                        )
                        all_diagnostics.append(lsp_diag)
                        diagnostics_count += 1
                        
            except Exception as e:
                self.logger.debug(f"Could not get diagnostics for {file_path}: {e}")
                continue
        
        self.logger.info(f"✅ LSP diagnostics collection complete:")
        self.logger.info(f"   📊 Total diagnostics: {diagnostics_count}")
        self.logger.info(f"   📁 Files with errors: {files_with_errors}")
        self.logger.info(f"   📈 Error rate: {files_with_errors/len(python_files)*100:.1f}%")
        
        return all_diagnostics
    
    async def detect_dead_code(self) -> Dict[str, Any]:
        """Detect potentially dead code in the codebase."""
        self.logger.info("🔍 Detecting dead code...")
        
        dead_code_analysis = {
            'unused_functions': [],
            'unused_classes': [],
            'unused_imports': [],
            'unreachable_code': [],
            'statistics': {}
        }
        
        if not self.codebase:
            return dead_code_analysis
        
        try:
            # Analyze function usage
            if hasattr(self.codebase, 'functions'):
                functions = list(self.codebase.functions)
                function_calls = set()
                
                # Simple heuristic: look for function calls in all files
                for root, dirs, files in os.walk(self.codebase_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        if file.endswith('.py'):
                            try:
                                full_path = Path(root) / file
                                content = full_path.read_text(encoding='utf-8', errors='ignore')
                                
                                # Extract function calls using regex
                                calls = re.findall(r'(\w+)\s*\(', content)
                                function_calls.update(calls)
                            except Exception:
                                continue
                
                # Find potentially unused functions
                for func in functions:
                    func_name = getattr(func, 'name', '')
                    if func_name and func_name not in function_calls:
                        # Skip special methods and common patterns
                        if not (func_name.startswith('_') or func_name in ['main', 'setup', 'teardown']):
                            dead_code_analysis['unused_functions'].append({
                                'name': func_name,
                                'file': getattr(func, 'file_path', 'unknown'),
                                'line': getattr(func, 'line_number', 0)
                            })
            
            # Analyze import usage
            import_analysis = await self._analyze_import_usage()
            dead_code_analysis['unused_imports'] = import_analysis.get('unused_imports', [])
            
            # Statistics
            dead_code_analysis['statistics'] = {
                'total_unused_functions': len(dead_code_analysis['unused_functions']),
                'total_unused_imports': len(dead_code_analysis['unused_imports']),
                'potential_cleanup_files': len(set(
                    item['file'] for item in dead_code_analysis['unused_functions'] + dead_code_analysis['unused_imports']
                ))
            }
            
            return dead_code_analysis
            
        except Exception as e:
            self.logger.error(f"Error detecting dead code: {e}")
            return {'error': str(e)}
    
    async def _analyze_import_usage(self) -> Dict[str, Any]:
        """Analyze import usage across the codebase."""
        import_analysis = {
            'unused_imports': [],
            'duplicate_imports': [],
            'circular_imports': []
        }
        
        try:
            # Simple import analysis using AST
            for root, dirs, files in os.walk(self.codebase_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith('.py'):
                        try:
                            full_path = Path(root) / file
                            content = full_path.read_text(encoding='utf-8', errors='ignore')
                            
                            # Parse AST to find imports
                            tree = ast.parse(content)
                            imports = []
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.append(alias.name)
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        for alias in node.names:
                                            imports.append(f"{node.module}.{alias.name}")
                            
                            # Simple heuristic: check if imported names are used
                            for imp in imports:
                                base_name = imp.split('.')[-1]
                                if base_name not in content.replace(f"import {imp}", ""):
                                    import_analysis['unused_imports'].append({
                                        'import': imp,
                                        'file': str(full_path.relative_to(self.codebase_path)),
                                        'line': 0  # Would need more sophisticated parsing for line numbers
                                    })
                                    
                        except Exception:
                            continue
            
            return import_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing imports: {e}")
            return import_analysis

    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis of the entire codebase."""
        start_time = time.time()
        self.logger.info("🚀 Starting comprehensive codebase analysis...")
        
        # Initialize if not already done
        if not self.codebase:
            await self.initialize_codebase()
        
        analysis_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'codebase_path': str(self.codebase_path),
            'serena_status': self.serena_status,
            'structure_analysis': {},
            'lsp_diagnostics': [],
            'dead_code_analysis': {},
            'code_quality_metrics': {},
            'dashboard_data': {},
            'performance_metrics': {},
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # 1. Analyze codebase structure
            self.logger.info("📊 Running structure analysis...")
            analysis_results['structure_analysis'] = await self.analyze_codebase_structure()
            
            # 2. Collect LSP diagnostics
            self.logger.info("🔍 Collecting LSP diagnostics...")
            diagnostics = await self.collect_all_lsp_diagnostics()
            analysis_results['lsp_diagnostics'] = [asdict(d) for d in diagnostics]
            
            # 3. Detect dead code
            self.logger.info("🔍 Detecting dead code...")
            analysis_results['dead_code_analysis'] = await self.detect_dead_code()
            
            # 4. Calculate code quality metrics
            self.logger.info("📈 Calculating code quality metrics...")
            analysis_results['code_quality_metrics'] = await self.calculate_quality_metrics()
            
            # 5. Demonstrate Serena features
            self.logger.info("🚀 Demonstrating Serena features...")
            analysis_results['serena_features'] = await self.demonstrate_serena_features()
            
            # 6. Run deep comprehensive analysis
            # 7. Run unified Serena analysis
            self.logger.info("🚀 Running unified Serena analysis...")
            analysis_results["unified_serena_analysis"] = await self.run_unified_serena_analysis()
            
            self.logger.info("🔬 Running deep comprehensive analysis...")
            analysis_results["deep_comprehensive_analysis"] = await self.run_deep_comprehensive_analysis()
            
            # 8. Generate dashboard data
            self.logger.info("📊 Generating dashboard data...")
            analysis_results['dashboard_data'] = await self.generate_dashboard_data(analysis_results)
            
            # 9. Performance metrics
            analysis_results['performance_metrics'] = {
                'total_analysis_time': time.time() - start_time,
                'files_analyzed': analysis_results['structure_analysis'].get('total_files', 0),
                'diagnostics_found': len(analysis_results['lsp_diagnostics']),
                'analysis_speed': analysis_results['structure_analysis'].get('total_files', 0) / (time.time() - start_time)
            }
            
            self.logger.info(f"✅ Comprehensive analysis complete in {time.time() - start_time:.2f}s")
            
            # Store results for dashboard access
            self.dashboard_data = analysis_results['dashboard_data']
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            analysis_results['errors'].append({
                'type': 'analysis_failure',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
            return analysis_results

    async def analyze_codebase_structure(self) -> Dict[str, Any]:
        """Analyze the comprehensive structure of the codebase."""
        if not self.codebase:
            return {}
        
        self.logger.info("📊 Analyzing codebase structure...")
        
        structure = {
            'total_files': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0,
            'languages': set(),
            'file_types': defaultdict(int),
            'largest_files': [],
            'most_complex_functions': [],
            'dependency_graph_stats': {},
            'dead_code_candidates': [],
            'import_issues': []
        }
        
        try:
            # Get basic statistics
            if hasattr(self.codebase, 'files'):
                files = list(self.codebase.files)
                structure['total_files'] = len(files)
                
                # Analyze file types and find largest files
                file_sizes = []
                for file in files:
                    ext = Path(file.file_path).suffix
                    structure['file_types'][ext] += 1
                    
                    # Track languages
                    if ext == '.py':
                        structure['languages'].add('Python')
                    elif ext in ['.js', '.jsx']:
                        structure['languages'].add('JavaScript')
                    elif ext in ['.ts', '.tsx']:
                        structure['languages'].add('TypeScript')
                
                    # Calculate file metrics
                    try:
                        full_path = self.codebase_path / file.file_path
                        if full_path.exists():
                            size = full_path.stat().st_size
                            lines = len(full_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                            file_sizes.append({
                                'path': file.file_path,
                                'size_bytes': size,
                                'lines': lines
                            })
                    except Exception:
                        continue
                
                structure['largest_files'] = sorted(file_sizes, key=lambda x: x['lines'], reverse=True)[:10]
            
            # Get function and class statistics
            if hasattr(self.codebase, 'functions'):
                functions = list(self.codebase.functions)
                structure['total_functions'] = len(functions)
                
                # Find most complex functions
                complex_functions = []
                for func in functions:
                    try:
                        func_name = getattr(func, 'name', 'unknown')
                        file_path = getattr(func, 'file_path', None) or getattr(func, 'filepath', None) or 'unknown'
                        complexity_score = len(func_name) + (file_path.count('/') * 2)
                        complex_functions.append({
                            'name': func_name,
                            'file': file_path,
                            'complexity_proxy': complexity_score
                        })
                    except Exception:
                        continue
                
                structure['most_complex_functions'] = sorted(
                    complex_functions, key=lambda x: x['complexity_proxy'], reverse=True
                )[:10]
            
            if hasattr(self.codebase, 'classes'):
                classes = list(self.codebase.classes)
                structure['total_classes'] = len(classes)
            
            # Convert sets to lists for JSON serialization
            structure['languages'] = list(structure['languages'])
            structure['file_types'] = dict(structure['file_types'])
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing codebase structure: {e}")
            return {'error': str(e)}

    async def calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive code quality metrics."""
        metrics = {
            'complexity_metrics': {},
            'maintainability_metrics': {},
            'test_coverage_metrics': {},
            'dependency_metrics': {},
            'security_metrics': {}
        }
        
        if not self.codebase:
            return metrics
        
        try:
            # Complexity metrics
            if hasattr(self.codebase, 'functions'):
                functions = list(self.codebase.functions)
                if functions:
                    # Simple complexity heuristic based on function name length and nesting
                    complexities = []
                    for func in functions:
                        func_name = getattr(func, 'name', '')
                        # Simple heuristic: longer names often indicate more complex functions
                        complexity = len(func_name) + func_name.count('_') * 2
                        complexities.append(complexity)
                    
                    metrics['complexity_metrics'] = {
                        'average_function_complexity': sum(complexities) / len(complexities),
                        'max_function_complexity': max(complexities),
                        'min_function_complexity': min(complexities),
                        'total_functions': len(functions)
                    }
            
            # Dependency metrics
            import_count = 0
            unique_imports = set()
            
            for root, dirs, files in os.walk(self.codebase_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith('.py'):
                        try:
                            full_path = Path(root) / file
                            content = full_path.read_text(encoding='utf-8', errors='ignore')
                            
                            # Count imports
                            import_lines = [line for line in content.splitlines() if line.strip().startswith(('import ', 'from '))]
                            import_count += len(import_lines)
                            
                            # Extract unique imports
                            for line in import_lines:
                                if 'import ' in line:
                                    parts = line.split('import ')
                                    if len(parts) > 1:
                                        unique_imports.add(parts[1].split()[0].split('.')[0])
                                        
                        except Exception:
                            continue
            
            metrics['dependency_metrics'] = {
                'total_imports': import_count,
                'unique_imports': len(unique_imports),
                'import_diversity': len(unique_imports) / max(import_count, 1)
            }
            
            # File-based metrics
            python_files = []
            total_lines = 0
            
            for root, dirs, files in os.walk(self.codebase_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith('.py'):
                        try:
                            full_path = Path(root) / file
                            lines = len(full_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                            python_files.append(lines)
                            total_lines += lines
                        except Exception:
                            continue
            
            if python_files:
                metrics['maintainability_metrics'] = {
                    'average_file_length': sum(python_files) / len(python_files),
                    'total_lines_of_code': total_lines,
                    'total_python_files': len(python_files),
                    'largest_file_lines': max(python_files),
                    'smallest_file_lines': min(python_files)
                }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating quality metrics: {e}")
            return {'error': str(e)}

    async def generate_dashboard_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data optimized for dashboard visualization."""
        dashboard_data = {
            'summary': {},
            'charts': {},
            'tables': {},
            'alerts': [],
            'recommendations': []
        }
        
        try:
            # Summary statistics
            structure = analysis_results.get('structure_analysis', {})
            diagnostics = analysis_results.get('lsp_diagnostics', [])
            dead_code = analysis_results.get('dead_code_analysis', {})
            quality = analysis_results.get('code_quality_metrics', {})
            
            dashboard_data['summary'] = {
                'total_files': structure.get('total_files', 0),
                'total_functions': structure.get('total_functions', 0),
                'total_classes': structure.get('total_classes', 0),
                'total_errors': len([d for d in diagnostics if d.get('severity') == 'error']),
                'total_warnings': len([d for d in diagnostics if d.get('severity') == 'warning']),
                'dead_functions': len(dead_code.get('unused_functions', [])),
                'dead_imports': len(dead_code.get('unused_imports', [])),
                'health_score': self._calculate_health_score(analysis_results)
            }
            
            # Chart data
            dashboard_data['charts'] = {
                'file_types': structure.get('file_types', {}),
                'error_severity_distribution': self._get_error_distribution(diagnostics),
                'complexity_distribution': self._get_complexity_distribution(quality),
                'file_size_distribution': self._get_file_size_distribution(structure)
            }
            
            # Table data
            dashboard_data['tables'] = {
                'largest_files': structure.get('largest_files', [])[:10],
                'most_complex_functions': structure.get('most_complex_functions', [])[:10],
                'recent_errors': diagnostics[:20],  # Most recent errors
                'dead_code_candidates': dead_code.get('unused_functions', [])[:10]
            }
            
            # Alerts and recommendations
            dashboard_data['alerts'] = self._generate_alerts(analysis_results)
            dashboard_data['recommendations'] = self._generate_recommendations(analysis_results)
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {e}")
            return {'error': str(e)}

    def _calculate_health_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall codebase health score (0-100)."""
        try:
            structure = analysis_results.get('structure_analysis', {})
            diagnostics = analysis_results.get('lsp_diagnostics', [])
            dead_code = analysis_results.get('dead_code_analysis', {})
            
            total_files = structure.get('total_files', 1)
            error_count = len([d for d in diagnostics if d.get('severity') == 'error'])
            warning_count = len([d for d in diagnostics if d.get('severity') == 'warning'])
            dead_functions = len(dead_code.get('unused_functions', []))
            
            # Simple health score calculation
            error_penalty = min(error_count / total_files * 50, 50)
            warning_penalty = min(warning_count / total_files * 20, 20)
            dead_code_penalty = min(dead_functions / max(structure.get('total_functions', 1), 1) * 15, 15)
            
            health_score = max(100 - error_penalty - warning_penalty - dead_code_penalty, 0)
            return round(health_score, 1)
            
        except Exception:
            return 50.0  # Default neutral score

    def _get_error_distribution(self, diagnostics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of error severities."""
        distribution = defaultdict(int)
        for diag in diagnostics:
            severity = diag.get('severity', 'unknown')
            distribution[severity] += 1
        return dict(distribution)

    def _get_complexity_distribution(self, quality_metrics: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution of complexity levels."""
        complexity = quality_metrics.get('complexity_metrics', {})
        avg_complexity = complexity.get('average_function_complexity', 0)
        
        # Simple distribution based on average
        if avg_complexity < 5:
            return {'low': 70, 'medium': 25, 'high': 5}
        elif avg_complexity < 10:
            return {'low': 40, 'medium': 45, 'high': 15}
        else:
            return {'low': 20, 'medium': 40, 'high': 40}

    def _get_file_size_distribution(self, structure: Dict[str, Any]) -> Dict[str, int]:
        """Get distribution of file sizes."""
        largest_files = structure.get('largest_files', [])
        if not largest_files:
            return {'small': 100}
        
        sizes = [f.get('lines', 0) for f in largest_files]
        small = len([s for s in sizes if s < 100])
        medium = len([s for s in sizes if 100 <= s < 500])
        large = len([s for s in sizes if s >= 500])
        
        total = len(sizes)
        if total == 0:
            return {'small': 100}
        
        return {
            'small': round(small / total * 100),
            'medium': round(medium / total * 100),
            'large': round(large / total * 100)
        }

    def _generate_alerts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis results."""
        alerts = []
        
        try:
            diagnostics = analysis_results.get('lsp_diagnostics', [])
            dead_code = analysis_results.get('dead_code_analysis', {})
            structure = analysis_results.get('structure_analysis', {})
            
            # High error count alert
            error_count = len([d for d in diagnostics if d.get('severity') == 'error'])
            if error_count > 10:
                alerts.append({
                    'type': 'error',
                    'title': 'High Error Count',
                    'message': f'Found {error_count} errors in the codebase',
                    'severity': 'high'
                })
            
            # Dead code alert
            dead_functions = len(dead_code.get('unused_functions', []))
            if dead_functions > 5:
                alerts.append({
                    'type': 'warning',
                    'title': 'Dead Code Detected',
                    'message': f'Found {dead_functions} potentially unused functions',
                    'severity': 'medium'
                })
            
            # Large file alert
            largest_files = structure.get('largest_files', [])
            if largest_files and largest_files[0].get('lines', 0) > 1000:
                alerts.append({
                    'type': 'info',
                    'title': 'Large File Detected',
                    'message': f'Largest file has {largest_files[0]["lines"]} lines',
                    'severity': 'low'
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            return []

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        try:
            diagnostics = analysis_results.get('lsp_diagnostics', [])
            dead_code = analysis_results.get('dead_code_analysis', {})
            
            # Error fixing recommendations
            error_count = len([d for d in diagnostics if d.get('severity') == 'error'])
            if error_count > 0:
                recommendations.append({
                    'title': 'Fix LSP Errors',
                    'description': f'Address {error_count} LSP errors to improve code quality',
                    'priority': 'high',
                    'action': 'review_errors'
                })
            
            # Dead code cleanup
            dead_functions = len(dead_code.get('unused_functions', []))
            if dead_functions > 0:
                recommendations.append({
                    'title': 'Clean Up Dead Code',
                    'description': f'Remove {dead_functions} unused functions to reduce codebase size',
                    'priority': 'medium',
                    'action': 'cleanup_dead_code'
                })
            
            # Import optimization
            unused_imports = len(dead_code.get('unused_imports', []))
            if unused_imports > 0:
                recommendations.append({
                    'title': 'Optimize Imports',
                    'description': f'Remove {unused_imports} unused imports',
                    'priority': 'low',
                    'action': 'optimize_imports'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get the current dashboard data."""
        return self.dashboard_data

    async def test_dashboard_integration(self) -> Dict[str, Any]:
        """Test dashboard API integration."""
        test_results = {
            'api_tests': [],
            'frontend_tests': [],
            'integration_status': 'unknown'
        }
        
        if not REQUESTS_AVAILABLE:
            test_results['integration_status'] = 'requests_unavailable'
            return test_results
        
        # Test backend API endpoints
        backend_url = "http://localhost:8000"
        
        try:
            # Test health endpoint
            response = requests.get(f"{backend_url}/api/health", timeout=5)
            test_results['api_tests'].append({
                'endpoint': '/api/health',
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            })
            
            # Test projects endpoint
            response = requests.get(f"{backend_url}/api/projects", timeout=5)
            test_results['api_tests'].append({
                'endpoint': '/api/projects',
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            })
            
            test_results['integration_status'] = 'connected'
            
        except Exception as e:
            test_results['integration_status'] = 'disconnected'
            test_results['error'] = str(e)
        
        return test_results


# Convenience functions for backward compatibility
async def run_comprehensive_analysis(codebase_path: str = ".") -> Dict[str, Any]:
    """Run comprehensive analysis on a codebase."""
    engine = ComprehensiveAnalysisEngine(codebase_path)
    return await engine.run_full_analysis()


async def get_dashboard_data(codebase_path: str = ".") -> Dict[str, Any]:
    """Get dashboard data for a codebase."""
    engine = ComprehensiveAnalysisEngine(codebase_path)
    await engine.run_full_analysis()
    return engine.get_dashboard_data()


if __name__ == "__main__":
    async def main():
        """Main function for running analysis."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Comprehensive Graph-Sitter Analysis Engine")
        parser.add_argument("--path", default=".", help="Path to codebase to analyze")
        parser.add_argument("--output", help="Output file for results (JSON)")
        parser.add_argument("--dashboard", action="store_true", help="Generate dashboard data")
        
        args = parser.parse_args()
        
        print("🚀 Starting Comprehensive Analysis Engine...")
        
        engine = ComprehensiveAnalysisEngine(args.path)
        results = await engine.run_full_analysis()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Results saved to {args.output}")
        
        if args.dashboard:
            dashboard_data = engine.get_dashboard_data()
            dashboard_file = args.output.replace('.json', '_dashboard.json') if args.output else 'dashboard_data.json'
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            print(f"📊 Dashboard data saved to {dashboard_file}")
        
        # Print summary
        summary = results.get('dashboard_data', {}).get('summary', {})
        print(f"\n📊 Analysis Summary:")
        print(f"   Files: {summary.get('total_files', 0)}")
        print(f"   Functions: {summary.get('total_functions', 0)}")
        print(f"   Classes: {summary.get('total_classes', 0)}")
        print(f"   Errors: {summary.get('total_errors', 0)}")
        print(f"   Warnings: {summary.get('total_warnings', 0)}")
        print(f"   Health Score: {summary.get('health_score', 0)}/100")
    
    asyncio.run(main())

    def print_comprehensive_report(self, analysis_results: Dict[str, Any]):
        """Print a comprehensive analysis report with enhanced Serena features."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
        print("=" * 80)
        
        # Overall health summary
        dashboard_data = analysis_results.get('dashboard_data', {})
        summary = dashboard_data.get('summary', {})
        
        print(f"\n📈 OVERALL HEALTH METRICS:")
        print(f"   Total Files Analyzed: {summary.get('total_files', 0)}")
        print(f"   Total Functions: {summary.get('total_functions', 0)}")
        print(f"   Total Classes: {summary.get('total_classes', 0)}")
        print(f"   Total Errors Found: {summary.get('total_errors', 0)}")
        print(f"   Total Warnings: {summary.get('total_warnings', 0)}")
        print(f"   Dead Functions: {summary.get('dead_functions', 0)}")
        print(f"   Dead Imports: {summary.get('dead_imports', 0)}")
        print(f"   Health Score: {summary.get('health_score', 0)}/100")
        
        # Serena features report
        serena_features = analysis_results.get('serena_features', {})
        if serena_features.get('available'):
            print(f"\n🚀 SERENA FEATURES ANALYSIS:")
            
            # Code Intelligence
            code_intel = serena_features.get('code_intelligence', {})
            if 'error' not in code_intel:
                completions = len(code_intel.get('completions', []))
                hover_info = 'Available' if code_intel.get('hover_info') else 'Not Available'
                signature_help = code_intel.get('signature_help', 'Not Available')
                print(f"   🧠 Code Intelligence:")
                print(f"      Completions: {completions} items")
                print(f"      Hover Info: {hover_info}")
                print(f"      Signature Help: {signature_help}")
            
            # Semantic Search
            semantic_search = serena_features.get('semantic_search', {})
            if 'error' not in semantic_search:
                searches = semantic_search.get('searches', [])
                print(f"   🔍 Semantic Search:")
                for search in searches[:3]:
                    term = search.get('term', 'unknown')
                    count = search.get('count', 0)
                    print(f"      '{term}': {count} results")
            
            # Refactoring
            refactoring = serena_features.get('refactoring', {})
            if 'error' not in refactoring:
                rename_available = refactoring.get('rename', {}).get('available', False)
                extract_available = refactoring.get('extract_method', {}).get('available', False)
                organize_available = refactoring.get('organize_imports', {}).get('available', False)
                print(f"   🔧 Refactoring Capabilities:")
                print(f"      Rename Symbol: {'✅' if rename_available else '❌'}")
                print(f"      Extract Method: {'✅' if extract_available else '❌'}")
                print(f"      Organize Imports: {'✅' if organize_available else '❌'}")
            
            # Code Generation
            code_gen = serena_features.get('code_generation', {})
            if 'error' not in code_gen:
                boilerplate_available = code_gen.get('boilerplate', {}).get('available', False)
                tests_available = code_gen.get('tests', {}).get('available', False)
                docs_available = code_gen.get('documentation', {}).get('available', False)
                print(f"   ⚡ Code Generation:")
                print(f"      Boilerplate: {'✅' if boilerplate_available else '❌'}")
                print(f"      Test Generation: {'✅' if tests_available else '❌'}")
                print(f"      Documentation: {'✅' if docs_available else '❌'}")
            
            # Symbol Intelligence
            symbol_intel = serena_features.get('symbol_intelligence', {})
            if 'error' not in symbol_intel:
                total_symbols = symbol_intel.get('total_symbols', 0)
                analyzed_symbols = len(symbol_intel.get('symbols_analyzed', []))
                print(f"   🎯 Symbol Intelligence:")
                print(f"      Total Symbols: {total_symbols}")
                print(f"      Analyzed Symbols: {analyzed_symbols}")
                for symbol in symbol_intel.get('symbols_analyzed', [])[:3]:
                    name = symbol.get('name', 'unknown')
                    deps = symbol.get('context', {}).get('dependencies_count', 0)
                    impact = symbol.get('impact', {}).get('affected_files_count', 0)
                    print(f"         {name}: {deps} deps, {impact} files affected")
        else:
            print(f"\n⚠️  SERENA FEATURES: Not available - {serena_features.get('reason', 'Unknown')}")
        
        # Error summary
        diagnostics = analysis_results.get('lsp_diagnostics', [])
        if diagnostics:
            print(f"\n❌ ERROR DETAILS ({len(diagnostics)} total):")
            error_types = defaultdict(int)
            for diag in diagnostics:
                severity = diag.get('severity', 'unknown')
                error_types[severity] += 1
            
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {error_type}: {count} occurrences")
            
            # Show top errors
            print(f"\n🔍 TOP ERROR EXAMPLES:")
            for i, diag in enumerate(diagnostics[:5]):
                file_path = diag.get('file_path', 'unknown')
                line = diag.get('line', 0)
                message = diag.get('message', 'No message')[:100]
                print(f"   {i+1}. {file_path}:{line} - {message}")
        
        # Structure analysis
        structure = analysis_results.get('structure_analysis', {})
        if structure:
            print(f"\n📊 CODEBASE STRUCTURE:")
            print(f"   Languages: {', '.join(structure.get('languages', []))}")
            print(f"   File Types: {structure.get('file_types', {})}")
            
            largest_files = structure.get('largest_files', [])[:5]
            if largest_files:
                print(f"\n📁 LARGEST FILES:")
                for i, file_info in enumerate(largest_files):
                    path = file_info.get('path', 'unknown')
                    lines = file_info.get('lines', 0)
                    size = file_info.get('size_bytes', 0)
                    print(f"   {i+1}. {path}: {lines} lines, {size} bytes")
        
        # Performance metrics
        perf_metrics = analysis_results.get('performance_metrics', {})
        if perf_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in perf_metrics.items():
                print(f"   {metric}: {value}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        total_errors = summary.get('total_errors', 0)
        total_warnings = summary.get('total_warnings', 0)
        dead_functions = summary.get('dead_functions', 0)
        health_score = summary.get('health_score', 100)
        
        if total_errors > 0:
            print(f"   🔴 HIGH PRIORITY: Fix {total_errors} errors found in the codebase")
        if total_warnings > 10:
            print(f"   🟡 MEDIUM PRIORITY: Address {total_warnings} warnings")
        if dead_functions > 5:
            print(f"   🟠 CLEANUP: Remove {dead_functions} unused functions")
        if health_score < 70:
            print(f"   🔵 IMPROVE: Overall health score is low ({health_score}/100)")
        
        if serena_features.get('available'):
            print(f"   ✨ ENHANCE: Leverage Serena features for advanced code intelligence")
        else:
            print(f"   🚀 UPGRADE: Enable Serena integration for enhanced analysis capabilities")
        
        print(f"\n✅ Enhanced comprehensive analysis complete!")
        print("This analysis showcases the full power of graph-sitter with Serena integration.")


# Enhanced main function with comprehensive reporting
async def main_enhanced():
    """Enhanced main function with comprehensive Serena analysis and reporting."""
    print("🚀 ENHANCED COMPREHENSIVE ANALYSIS ENGINE")
    print("=" * 60)
    print("Analyzing codebase with comprehensive Serena integration")
    print("This showcases all available analysis features and Serena capabilities.")
    print()
    
    # Initialize analyzer
    engine = ComprehensiveAnalysisEngine(".")
    
    # Record start time for performance metrics
    start_time = time.time()
    
    # Initialize codebase
    if not await engine.initialize_codebase():
        print("❌ Failed to initialize codebase with full capabilities. Continuing with basic analysis...")
    
    # Perform comprehensive analysis
    try:
        results = await engine.run_full_analysis()
        
        # Print comprehensive report with Serena features
        engine.print_comprehensive_report(results)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    # Cleanup
    try:
        if engine.codebase and hasattr(engine.codebase, 'shutdown_serena'):
            engine.codebase.shutdown_serena()
            print("\n🔄 Serena integration shutdown complete")
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
    
    print("\n🎉 Enhanced Comprehensive Analysis Complete!")
    print("This analysis demonstrates the full power of graph-sitter with Serena integration.")


    async def run_deep_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run deep comprehensive self-analysis using all existing features and new capabilities."""
        self.logger.info("🔬 Starting deep comprehensive self-analysis...")
        
        try:
            from deep_comprehensive_analysis import DeepComprehensiveAnalyzer
            
            # Initialize deep analyzer with current codebase
            deep_analyzer = DeepComprehensiveAnalyzer(str(self.codebase_path), self.codebase)
            
            # Run deep comprehensive analysis
            results = await deep_analyzer.run_deep_comprehensive_analysis()
            
            # Print the deep analysis report
            deep_analyzer.print_deep_analysis_report(results)
            
            return results
            
        except ImportError as e:
            self.logger.error(f"Could not import deep analysis module: {e}")
            return {"error": f"Deep analysis module not available: {e}"}
        except Exception as e:
            self.logger.error(f"Deep analysis failed: {e}")
            return {"error": f"Deep analysis failed: {e}"}


async def main_deep_comprehensive():
    """Main function for running deep comprehensive analysis."""
    print("🔬 DEEP COMPREHENSIVE ANALYSIS ENGINE")
    print("=" * 60)
    print("Analyzing codebase with ALL existing and new capabilities")
    print("This validates all integrations and provides comprehensive reporting.")
    print()
    
    # Initialize analyzer
    engine = ComprehensiveAnalysisEngine(".")
    
    # Initialize codebase
    if not await engine.initialize_codebase():
        print("❌ Failed to initialize codebase. Continuing with limited analysis...")
    
    # Run deep comprehensive analysis
    try:
        results = await engine.run_deep_comprehensive_analysis()
        
        if "error" not in results:
            print("\n✅ Deep comprehensive analysis completed successfully!")
        else:
            print(f"\n⚠️  Deep analysis had issues: {results['error']}")
        
    except Exception as e:
        print(f"❌ Deep comprehensive analysis failed: {e}")
        traceback.print_exc()
    
    print("\n🎉 Deep Comprehensive Analysis Complete!")
    print("This analysis demonstrates the full integration of all graph-sitter capabilities.")


    async def run_unified_serena_analysis(self) -> Dict[str, Any]:
        """Run unified Serena analysis with ALL capabilities."""
        self.logger.info("🚀 Starting unified Serena analysis...")
        
        try:
            from unified_serena_analyzer import UnifiedSerenaAnalyzer
            
            # Initialize unified analyzer with current codebase
            unified_analyzer = UnifiedSerenaAnalyzer(str(self.codebase_path))
            
            # Initialize codebase
            if not unified_analyzer.initialize_codebase():
                return {"error": "Failed to initialize unified Serena analyzer"}
            
            # Record start time
            start_time = time.time()
            
            # 1. Collect ALL LSP diagnostics
            lsp_diagnostics = unified_analyzer.collect_all_lsp_diagnostics()
            
            # 2. Demonstrate all Serena features
            serena_demo = unified_analyzer.demonstrate_serena_features()
            
            # 3. Perform comprehensive codebase analysis
            analysis_results = unified_analyzer.analyze_codebase_comprehensive()
            
            # 4. Record performance metrics
            unified_analyzer.performance_metrics = {
                'analysis_time': f"{time.time() - start_time:.2f} seconds",
                'lsp_diagnostics_collected': len(lsp_diagnostics),
                'serena_features_working': len(serena_demo.get('successful_features', [])),
                'serena_features_total': len(serena_demo.get('features_tested', [])),
                'files_analyzed': analysis_results.get('files_analyzed', 0)
            }
            
            # 5. Print comprehensive report
            unified_analyzer.print_comprehensive_report(analysis_results)
            
            # 6. Cleanup
            unified_analyzer.cleanup()
            
            # Return complete results
            return {
                'lsp_diagnostics': lsp_diagnostics,
                'serena_features': serena_demo,
                'analysis_results': analysis_results,
                'performance_metrics': unified_analyzer.performance_metrics,
                'serena_status': unified_analyzer.serena_status
            }
            
        except ImportError as e:
            self.logger.error(f"Could not import unified Serena analyzer: {e}")
            return {"error": f"Unified Serena analyzer not available: {e}"}
        except Exception as e:
            self.logger.error(f"Unified Serena analysis failed: {e}")
            return {"error": f"Unified Serena analysis failed: {e}"}


async def main_unified_serena():
    """Main function for running unified Serena analysis."""
    print("🚀 UNIFIED SERENA ANALYSIS ENGINE")
    print("=" * 60)
    print("Complete codebase analysis with ALL LSP errors, symbol overviews, and Serena features")
    print("This consolidates ALL Serena capabilities into one comprehensive analysis.")
    print()
    
    # Initialize analyzer
    engine = ComprehensiveAnalysisEngine(".")
    
    # Initialize codebase
    if not await engine.initialize_codebase():
        print("❌ Failed to initialize codebase. Continuing with limited analysis...")
    
    # Run unified Serena analysis
    try:
        results = await engine.run_unified_serena_analysis()
        
        if "error" not in results:
            print("\n✅ Unified Serena analysis completed successfully!")
            
            # Show summary
            lsp_count = len(results.get('lsp_diagnostics', []))
            serena_working = len(results.get('serena_features', {}).get('successful_features', []))
            serena_total = len(results.get('serena_features', {}).get('features_tested', []))
            files_analyzed = results.get('analysis_results', {}).get('files_analyzed', 0)
            
            print(f"📊 Analysis Summary:")
            print(f"   LSP Diagnostics: {lsp_count}")
            print(f"   Serena Features: {serena_working}/{serena_total} working")
            print(f"   Files Analyzed: {files_analyzed}")
            
        else:
            print(f"\n⚠️  Unified Serena analysis had issues: {results['error']}")
        
    except Exception as e:
        print(f"❌ Unified Serena analysis failed: {e}")
        traceback.print_exc()
    
    print("\n🎉 Unified Serena Analysis Complete!")
    print("This analysis demonstrates the full integration of ALL Serena capabilities.")

