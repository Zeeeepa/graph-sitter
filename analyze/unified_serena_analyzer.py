#!/usr/bin/env python3
"""
Unified Serena Analyzer - Comprehensive Codebase Analysis

This consolidated analyzer combines all Serena capabilities into a single comprehensive tool
that provides complete codebase analysis with ALL LSP server errors, symbol overviews,
and advanced code intelligence features.

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

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False

# Try to import all Serena components
SERENA_COMPONENTS = {}
try:
    from graph_sitter.extensions.serena.types import (
        SerenaConfig, SerenaCapability, RefactoringType, RefactoringResult,
        CodeGenerationResult, SemanticSearchResult, SymbolInfo
    )
    SERENA_COMPONENTS['types'] = True
except ImportError:
    SERENA_COMPONENTS['types'] = False

try:
    from graph_sitter.extensions.serena.core import SerenaCore
    SERENA_COMPONENTS['core'] = True
except ImportError:
    SERENA_COMPONENTS['core'] = False

try:
    from graph_sitter.extensions.serena.intelligence import CodeIntelligence
    SERENA_COMPONENTS['intelligence'] = True
except ImportError:
    SERENA_COMPONENTS['intelligence'] = False

try:
    from graph_sitter.extensions.serena.auto_init import _initialized
    SERENA_COMPONENTS['auto_init'] = _initialized
except ImportError:
    SERENA_COMPONENTS['auto_init'] = False


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


class UnifiedSerenaAnalyzer:
    """Unified analyzer that consolidates all Serena capabilities."""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.lsp_diagnostics: List[LSPDiagnostic] = []
        self.symbol_overview: List[SymbolOverview] = []
        self.analysis_results: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = {}
        self.serena_status: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def initialize_codebase(self) -> bool:
        """Initialize the codebase with full Serena capabilities."""
        try:
            print(f"🔍 Initializing unified Serena analyzer for: {self.codebase_path}")
            
            if not GRAPH_SITTER_AVAILABLE:
                print("❌ Graph-sitter not available")
                return False
                
            self.codebase = Codebase(str(self.codebase_path))
            print("✅ Graph-sitter codebase initialized")
            
            # Check and initialize Serena
            self.serena_status = self._initialize_serena()
            print(f"📊 Serena initialization: {self.serena_status.get('enabled', False)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def _initialize_serena(self) -> Dict[str, Any]:
        """Initialize and check all Serena components."""
        status = {
            'available_components': SERENA_COMPONENTS,
            'integration_active': False,
            'methods_available': [],
            'lsp_servers': [],
            'capabilities': [],
            'enabled': False
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
    
    def collect_all_lsp_diagnostics(self) -> List[LSPDiagnostic]:
        """Collect ALL LSP diagnostics from all language servers."""
        print("\n🔍 Collecting ALL LSP diagnostics from language servers...")
        
        all_diagnostics = []
        
        if not self.codebase:
            print("⚠️  No codebase available")
            return all_diagnostics
        
        # Check if LSP diagnostics method is available
        if not hasattr(self.codebase, 'get_file_diagnostics'):
            print("⚠️  LSP diagnostics method not available")
            print("   Available methods:", [m for m in dir(self.codebase) if 'diagnostic' in m.lower()])
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
        
        print(f"📊 Scanning {len(python_files)} Python files for LSP diagnostics...")
        
        # Collect diagnostics from all files
        diagnostics_count = 0
        files_with_errors = 0
        
        for i, file_path in enumerate(python_files):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(python_files)} files scanned...")
            
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
                            
                            diagnostic = LSPDiagnostic(
                                file_path=file_path,
                                line=start_pos.get('line', 0) + 1,  # Convert to 1-based
                                character=start_pos.get('character', 0),
                                severity=severity,
                                message=diag.get('message', 'No message'),
                                code=diag.get('code'),
                                source=diag.get('source', 'lsp'),
                                range_start=start_pos,
                                range_end=end_pos
                            )
                            
                            all_diagnostics.append(diagnostic)
                            diagnostics_count += 1
                            
                        except Exception as e:
                            print(f"⚠️  Error parsing diagnostic in {file_path}: {e}")
                            continue
                            
            except Exception as e:
                # Don't spam errors for every file
                if i < 10:  # Only show first 10 errors
                    print(f"⚠️  Error getting diagnostics for {file_path}: {e}")
                continue
        
        # Store results
        self.lsp_diagnostics = all_diagnostics
        
        print(f"✅ LSP diagnostics collection complete:")
        print(f"   📊 Total diagnostics: {diagnostics_count}")
        print(f"   📁 Files with issues: {files_with_errors}")
        
        # Count by severity
        severity_counts = defaultdict(int)
        for diag in all_diagnostics:
            severity_counts[diag.severity] += 1
        
        for severity, count in severity_counts.items():
            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
            print(f"   {emoji} {severity.title()}: {count}")
        
        return all_diagnostics
    
    def analyze_file_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of a single file with enhanced Serena features."""
        print(f"📄 Analyzing file comprehensively: {file_path}")
        
        analysis_result = {
            'file_path': file_path,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'symbols': [],
            'dependencies': [],
            'metrics': {},
            'complexity_score': 0.0,
            'maintainability_index': 0.0,
            'serena_features': {}
        }
        
        try:
            # Basic file analysis using graph-sitter
            if self.codebase:
                # Get file content and basic metrics
                full_path = self.codebase_path / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    analysis_result['metrics'] = {
                        'lines_of_code': len(content.splitlines()),
                        'file_size': len(content),
                        'character_count': len(content)
                    }
                    
                    # Try to get functions and classes from the file
                    try:
                        if hasattr(self.codebase, 'functions'):
                            file_functions = [f for f in self.codebase.functions if getattr(f, 'file_path', '') == file_path]
                            analysis_result['symbols'].extend([{
                                'name': getattr(f, 'name', 'unknown'),
                                'type': 'function',
                                'line': getattr(f, 'line_number', 0),
                                'complexity': getattr(f, 'complexity', 1)
                            } for f in file_functions])
                            
                        if hasattr(self.codebase, 'classes'):
                            file_classes = [c for c in self.codebase.classes if getattr(c, 'file_path', '') == file_path]
                            analysis_result['symbols'].extend([{
                                'name': getattr(c, 'name', 'unknown'),
                                'type': 'class',
                                'line': getattr(c, 'line_number', 0),
                                'methods': len(getattr(c, 'methods', []))
                            } for c in file_classes])
                    except Exception as e:
                        analysis_result['warnings'].append({
                            'type': 'symbol_extraction',
                            'message': f"Could not extract symbols: {e}",
                            'line': 0
                        })
                
                # Enhanced analysis with Serena LSP diagnostics
                if hasattr(self.codebase, 'get_file_diagnostics'):
                    try:
                        diagnostics = self.codebase.get_file_diagnostics(file_path)
                        if diagnostics and diagnostics.get('success'):
                            for diag in diagnostics.get('diagnostics', []):
                                severity = diag.get('severity', 'info')
                                if isinstance(severity, int):
                                    severity_map = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}
                                    severity = severity_map.get(severity, 'info')
                                
                                item = {
                                    'type': diag.get('code', 'unknown'),
                                    'message': diag.get('message', ''),
                                    'line': diag.get('range', {}).get('start', {}).get('line', 0),
                                    'character': diag.get('range', {}).get('start', {}).get('character', 0),
                                    'source': diag.get('source', 'lsp')
                                }
                                
                                if severity == 'error':
                                    analysis_result['errors'].append(item)
                                elif severity == 'warning':
                                    analysis_result['warnings'].append(item)
                                else:
                                    analysis_result['suggestions'].append(item)
                    except Exception as e:
                        analysis_result['warnings'].append({
                            'type': 'diagnostics_error',
                            'message': f"Failed to get diagnostics: {e}",
                            'line': 0
                        })
                
                # Enhanced symbol context analysis
                if hasattr(self.codebase, 'get_symbol_context'):
                    try:
                        for symbol in analysis_result['symbols']:
                            context = self.codebase.get_symbol_context(
                                symbol['name'], 
                                include_dependencies=True
                            )
                            if context and context.get('success'):
                                symbol['context'] = context.get('context', {})
                                symbol['dependencies'] = context.get('dependencies', [])
                                analysis_result['dependencies'].extend(context.get('dependencies', []))
                    except Exception as e:
                        analysis_result['warnings'].append({
                            'type': 'symbol_context_error',
                            'message': f"Failed to get symbol context: {e}",
                            'line': 0
                        })
                
                # Test Serena features on this file
                analysis_result['serena_features'] = self._test_serena_features_on_file(file_path)
                
        except Exception as e:
            analysis_result['errors'].append({
                'type': 'analysis_error',
                'message': f"Failed to analyze file: {e}",
                'line': 0,
                'character': 0
            })
        
        # Calculate enhanced complexity and maintainability scores
        analysis_result['complexity_score'] = self._calculate_complexity_enhanced(
            analysis_result['symbols'], 
            analysis_result['metrics']
        )
        analysis_result['maintainability_index'] = self._calculate_maintainability_enhanced(
            analysis_result['metrics'], 
            analysis_result['errors'], 
            analysis_result['warnings']
        )
        
        return analysis_result
    
    def _test_serena_features_on_file(self, file_path: str) -> Dict[str, Any]:
        """Test all available Serena features on a specific file."""
        features_result = {
            'code_intelligence': {},
            'semantic_search': {},
            'refactoring': {},
            'code_generation': {},
            'symbol_intelligence': {}
        }
        
        if not self.codebase:
            return features_result
        
        try:
            # Test code intelligence features
            if hasattr(self.codebase, 'get_completions'):
                try:
                    completions = self.codebase.get_completions(file_path, 10, 0)
                    features_result['code_intelligence']['completions'] = {
                        'available': completions.get('success', False) if completions else False,
                        'count': len(completions.get('completions', [])) if completions else 0
                    }
                except Exception as e:
                    features_result['code_intelligence']['completions'] = {'error': str(e)}
            
            if hasattr(self.codebase, 'get_hover_info'):
                try:
                    hover = self.codebase.get_hover_info(file_path, 20, 10)
                    features_result['code_intelligence']['hover'] = {
                        'available': hover.get('success', False) if hover else False,
                        'has_content': bool(hover.get('contents')) if hover else False
                    }
                except Exception as e:
                    features_result['code_intelligence']['hover'] = {'error': str(e)}
            
            if hasattr(self.codebase, 'get_signature_help'):
                try:
                    signature = self.codebase.get_signature_help(file_path, 30, 15)
                    features_result['code_intelligence']['signature_help'] = {
                        'available': signature.get('success', False) if signature else False
                    }
                except Exception as e:
                    features_result['code_intelligence']['signature_help'] = {'error': str(e)}
            
            # Test refactoring capabilities
            if hasattr(self.codebase, 'rename_symbol'):
                try:
                    rename_result = self.codebase.rename_symbol(
                        file_path, 10, 5, "new_name", preview=True
                    )
                    features_result['refactoring']['rename_symbol'] = {
                        'available': rename_result.get('success', False) if rename_result else False,
                        'changes_count': len(rename_result.get('changes', [])) if rename_result else 0
                    }
                except Exception as e:
                    features_result['refactoring']['rename_symbol'] = {'error': str(e)}
            
            if hasattr(self.codebase, 'extract_method'):
                try:
                    extract_result = self.codebase.extract_method(
                        file_path, 15, 25, "extracted_method", preview=True
                    )
                    features_result['refactoring']['extract_method'] = {
                        'available': extract_result.get('success', False) if extract_result else False
                    }
                except Exception as e:
                    features_result['refactoring']['extract_method'] = {'error': str(e)}
            
            if hasattr(self.codebase, 'organize_imports'):
                try:
                    organize_result = self.codebase.organize_imports(file_path)
                    features_result['refactoring']['organize_imports'] = {
                        'available': organize_result.get('success', False) if organize_result else False
                    }
                except Exception as e:
                    features_result['refactoring']['organize_imports'] = {'error': str(e)}
            
        except Exception as e:
            features_result['error'] = str(e)
        
        return features_result
    
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
        
        # Adjust based on symbol count
        symbol_count = len(symbols)
        if symbol_count > 20:
            base_complexity *= 1.2
        elif symbol_count > 50:
            base_complexity *= 1.5
        
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
        
        # Adjust based on file size vs content ratio
        file_size = metrics.get('file_size', 0)
        if lines > 0:
            avg_line_length = file_size / lines
            if avg_line_length > 120:  # Very long lines
                base_score -= 5
        
        return max(base_score, 0.0)
    
    def demonstrate_serena_features(self) -> Dict[str, Any]:
        """Demonstrate ALL available Serena features comprehensively."""
        print("\n🚀 Demonstrating ALL Serena Features")
        print("=" * 60)
        
        demo_results = {
            'features_tested': [],
            'successful_features': [],
            'failed_features': [],
            'results': {},
            'performance_metrics': {}
        }
        
        if not self.codebase:
            demo_results['error'] = 'No codebase available'
            return demo_results
        
        # Find a sample Python file for testing
        sample_file = self._find_best_sample_file()
        
        # Test all Serena methods comprehensively
        serena_methods = [
            ('get_serena_status', lambda: self.codebase.get_serena_status()),
            ('get_completions', lambda: self.codebase.get_completions(sample_file, 10, 0) if sample_file else None),
            ('get_hover_info', lambda: self.codebase.get_hover_info(sample_file, 20, 10) if sample_file else None),
            ('get_signature_help', lambda: self.codebase.get_signature_help(sample_file, 30, 15) if sample_file else None),
            ('semantic_search', lambda: self.codebase.semantic_search('function', max_results=5)),
            ('rename_symbol', lambda: self.codebase.rename_symbol(sample_file, 10, 5, 'new_name', preview=True) if sample_file else None),
            ('extract_method', lambda: self.codebase.extract_method(sample_file, 15, 25, 'extracted_method', preview=True) if sample_file else None),
            ('generate_boilerplate', lambda: self.codebase.generate_boilerplate('class', {'class_name': 'TestClass'}, 'test.py')),
            ('organize_imports', lambda: self.codebase.organize_imports(sample_file) if sample_file else None),
            ('get_symbol_context', lambda: self.codebase.get_symbol_context('test_symbol', include_dependencies=True)),
            ('analyze_symbol_impact', lambda: self.codebase.analyze_symbol_impact('test_symbol', 'modify')),
            ('enable_realtime_analysis', lambda: self.codebase.enable_realtime_analysis(watch_patterns=["*.py"], auto_refresh=True))
        ]
        
        for method_name, demo_func in serena_methods:
            demo_results['features_tested'].append(method_name)
            
            if hasattr(self.codebase, method_name):
                try:
                    print(f"🧪 Testing {method_name}...")
                    start_time = time.time()
                    result = demo_func()
                    end_time = time.time()
                    
                    demo_results['successful_features'].append(method_name)
                    demo_results['results'][method_name] = {'success': True, 'result': result}
                    demo_results['performance_metrics'][method_name] = {
                        'execution_time': round(end_time - start_time, 3),
                        'success': True
                    }
                    print(f"   ✅ {method_name} - Success ({end_time - start_time:.3f}s)")
                    
                except Exception as e:
                    demo_results['failed_features'].append(method_name)
                    demo_results['results'][method_name] = {'success': False, 'error': str(e)}
                    demo_results['performance_metrics'][method_name] = {
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    }
                    print(f"   ❌ {method_name} - Failed: {e}")
            else:
                demo_results['failed_features'].append(method_name)
                demo_results['results'][method_name] = {'success': False, 'error': 'Method not available'}
                print(f"   ⚠️  {method_name} - Not available")
        
        return demo_results
    
    def _find_best_sample_file(self) -> Optional[str]:
        """Find the best Python file for testing."""
        if not self.codebase or not hasattr(self.codebase, 'files'):
            return None
        
        # Prefer files in src/graph_sitter/core
        for file in self.codebase.files:
            file_path = getattr(file, 'file_path', '') or getattr(file, 'filepath', '')
            if 'src/graph_sitter/core/' in file_path and file_path.endswith('.py'):
                return file_path
        
        # Fallback to any Python file
        for file in self.codebase.files:
            file_path = getattr(file, 'file_path', '') or getattr(file, 'filepath', '')
            if file_path.endswith('.py'):
                return file_path
        
        return None
    
    def analyze_codebase_comprehensive(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of the entire codebase."""
        print("\n🔍 Starting comprehensive codebase analysis...")
        
        # Get all Python files in the codebase
        python_files = []
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.codebase_path)
                    python_files.append(rel_path)
        
        print(f"📊 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file comprehensively
        file_analyses = {}
        total_errors = 0
        total_warnings = 0
        total_suggestions = 0
        complexity_scores = []
        maintainability_scores = []
        
        for i, file_path in enumerate(python_files[:50]):  # Limit to first 50 files for demo
            print(f"Progress: {i+1}/{min(len(python_files), 50)} - {file_path}")
            try:
                result = self.analyze_file_comprehensive(file_path)
                file_analyses[file_path] = result
                total_errors += len(result['errors'])
                total_warnings += len(result['warnings'])
                total_suggestions += len(result['suggestions'])
                complexity_scores.append(result['complexity_score'])
                maintainability_scores.append(result['maintainability_index'])
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
                continue
        
        # Calculate overall health metrics
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0
        
        # Find hotspots (files with most issues)
        hotspots = []
        for file_path, result in file_analyses.items():
            issue_count = len(result['errors']) + len(result['warnings'])
            if issue_count > 0:
                hotspots.append({
                    'file_path': file_path,
                    'issue_count': issue_count,
                    'errors': len(result['errors']),
                    'warnings': len(result['warnings']),
                    'complexity': result['complexity_score']
                })
        
        hotspots.sort(key=lambda x: x['issue_count'], reverse=True)
        
        return {
            'total_files': len(python_files),
            'files_analyzed': len(file_analyses),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'total_suggestions': total_suggestions,
            'average_complexity': avg_complexity,
            'maintainability_score': avg_maintainability,
            'hotspots': hotspots[:10],  # Top 10 hotspots
            'file_analyses': file_analyses,
            'serena_integration_status': self.serena_status
        }
    
    def print_comprehensive_report(self, analysis_results: Dict[str, Any]):
        """Print a comprehensive analysis report with all Serena features."""
        print("\n" + "=" * 80)
        print("📊 UNIFIED SERENA ANALYZER - COMPREHENSIVE REPORT")
        print("=" * 80)
        
        # Overall health summary
        print(f"\n📈 OVERALL HEALTH METRICS:")
        print(f"   Total Files: {analysis_results.get('total_files', 0)}")
        print(f"   Files Analyzed: {analysis_results.get('files_analyzed', 0)}")
        print(f"   Total Errors: {analysis_results.get('total_errors', 0)}")
        print(f"   Total Warnings: {analysis_results.get('total_warnings', 0)}")
        print(f"   Total Suggestions: {analysis_results.get('total_suggestions', 0)}")
        print(f"   Average Complexity: {analysis_results.get('average_complexity', 0):.2f}/10")
        print(f"   Maintainability Score: {analysis_results.get('maintainability_score', 0):.1f}/100")
        
        # Serena integration status
        serena_status = analysis_results.get('serena_integration_status', {})
        print(f"\n🚀 SERENA INTEGRATION STATUS:")
        print(f"   Integration Active: {'✅' if serena_status.get('integration_active') else '❌'}")
        print(f"   Serena Enabled: {'✅' if serena_status.get('enabled') else '❌'}")
        print(f"   Available Methods: {len(serena_status.get('methods_available', []))}")
        print(f"   LSP Servers: {len(serena_status.get('lsp_servers', []))}")
        print(f"   Capabilities: {len(serena_status.get('capabilities', []))}")
        
        if serena_status.get('methods_available'):
            print(f"   Available Serena Methods:")
            for method in serena_status['methods_available'][:10]:  # Show first 10
                print(f"     • {method}")
        
        # LSP diagnostics summary
        if self.lsp_diagnostics:
            print(f"\n🔍 LSP DIAGNOSTICS SUMMARY:")
            severity_counts = defaultdict(int)
            for diag in self.lsp_diagnostics:
                severity_counts[diag.severity] += 1
            
            for severity, count in severity_counts.items():
                emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
                print(f"   {emoji} {severity.title()}: {count}")
            
            # Show top errors
            print(f"\n❌ TOP LSP ERRORS:")
            error_diagnostics = [d for d in self.lsp_diagnostics if d.severity == 'error']
            for i, diag in enumerate(error_diagnostics[:5]):
                print(f"   {i+1}. {diag.file_path}:{diag.line} - {diag.message[:80]}...")
        
        # Hotspots
        hotspots = analysis_results.get('hotspots', [])
        if hotspots:
            print(f"\n🔥 CODE HOTSPOTS (files with most issues):")
            for i, hotspot in enumerate(hotspots[:5]):
                print(f"   {i+1}. {hotspot['file_path']}")
                print(f"      Issues: {hotspot['issue_count']} (Errors: {hotspot['errors']}, Warnings: {hotspot['warnings']})")
                print(f"      Complexity: {hotspot['complexity']:.1f}/10")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in self.performance_metrics.items():
                print(f"   {metric}: {value}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        total_errors = analysis_results.get('total_errors', 0)
        total_warnings = analysis_results.get('total_warnings', 0)
        avg_complexity = analysis_results.get('average_complexity', 0)
        maintainability = analysis_results.get('maintainability_score', 0)
        
        if total_errors > 0:
            print(f"   🔴 HIGH PRIORITY: Fix {total_errors} errors found in the codebase")
        if total_warnings > 10:
            print(f"   🟡 MEDIUM PRIORITY: Address {total_warnings} warnings")
        if avg_complexity > 5:
            print(f"   🟠 REFACTOR: Average complexity is high ({avg_complexity:.1f}/10)")
        if maintainability < 70:
            print(f"   🔵 IMPROVE: Maintainability score is low ({maintainability:.1f}/100)")
        if not serena_status.get('enabled'):
            print(f"   🚀 ENHANCE: Enable Serena integration for advanced code intelligence")
        
        print(f"\n✅ Unified Serena analysis complete!")
    
    def _safe_dict(self, obj) -> Dict[str, Any]:
        """Safely convert dataclass to dict, handling non-serializable objects."""
        if hasattr(obj, "__dict__"):
            result = {}
            for key, value in obj.__dict__.items():
                try:
                    # Handle common non-serializable types
                    if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
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
            if self.codebase and hasattr(self.codebase, 'shutdown_serena'):
                self.codebase.shutdown_serena()
                print("🔄 Serena integration shutdown complete")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
        
        try:
            self.executor.shutdown(wait=True)
        except Exception:
            pass


def main():
    """Main function to run the unified Serena analyzer."""
    print("🚀 UNIFIED SERENA ANALYZER")
    print("=" * 50)
    print("Complete codebase analysis with ALL LSP errors, symbol overviews, and Serena features")
    print("This consolidates all demo capabilities into one comprehensive tool.")
    print()
    
    # Show component availability
    print("📦 COMPONENT AVAILABILITY:")
    print(f"   Graph-sitter: {'✅' if GRAPH_SITTER_AVAILABLE else '❌'}")
    for component, available in SERENA_COMPONENTS.items():
        status = '✅' if available else '❌'
        print(f"   Serena {component}: {status}")
    print()
    
    # Initialize analyzer
    analyzer = UnifiedSerenaAnalyzer(".")
    
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    try:
        # Record start time for performance metrics
        start_time = time.time()
        
        # 1. Collect ALL LSP diagnostics
        lsp_diagnostics = analyzer.collect_all_lsp_diagnostics()
        
        # 2. Demonstrate all Serena features
        serena_demo = analyzer.demonstrate_serena_features()
        
        # 3. Perform comprehensive codebase analysis
        analysis_results = analyzer.analyze_codebase_comprehensive()
        
        # 4. Record performance metrics
        analyzer.performance_metrics = {
            'analysis_time': f"{time.time() - start_time:.2f} seconds",
            'lsp_diagnostics_collected': len(lsp_diagnostics),
            'serena_features_working': len(serena_demo.get('successful_features', [])),
            'serena_features_total': len(serena_demo.get('features_tested', [])),
            'files_analyzed': analysis_results.get('files_analyzed', 0),
            'memory_usage': 'N/A'  # Would need psutil for actual memory usage
        }
        
        # 5. Print comprehensive report
        analyzer.print_comprehensive_report(analysis_results)
        
        # 6. Save comprehensive report
        report_file = Path("unified_serena_analysis_report.json")
        complete_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'codebase_path': str(analyzer.codebase_path),
            'serena_status': analyzer.serena_status,
            'lsp_diagnostics': [analyzer._safe_dict(d) for d in lsp_diagnostics],
            'serena_features': serena_demo,
            'analysis_results': analysis_results,
            'performance_metrics': analyzer.performance_metrics
        }
        
        with open(report_file, 'w') as f:
            json.dump(complete_report, f, indent=2, default=str)
        print(f"\n💾 Complete report saved to: {report_file}")
        
        # Save LSP diagnostics separately for easy access
        if lsp_diagnostics:
            lsp_file = Path("lsp_diagnostics_complete.json")
            with open(lsp_file, 'w') as f:
                json.dump([analyzer._safe_dict(d) for d in lsp_diagnostics], f, indent=2, default=str)
            print(f"💾 LSP diagnostics saved to: {lsp_file}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    finally:
        # Cleanup
        analyzer.cleanup()
    
    print("\n🎉 Unified Serena Analysis Complete!")
    print("This consolidated analyzer provided complete LSP diagnostics, symbol analysis, and Serena feature testing.")


if __name__ == "__main__":
    main()
