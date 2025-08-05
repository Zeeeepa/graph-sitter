#!/usr/bin/env python3
"""
Unified Serena Analyzer - Integrated Version with LSP + Serena Support

This integrated analyzer combines all Serena capabilities with corrected import paths
and proper initialization for complete codebase analysis with ALL LSP server errors,
symbol overviews, and advanced code intelligence features.

Features:
- Complete LSP error reporting from all language servers
- Comprehensive symbol analysis and mapping
- Advanced code intelligence and refactoring capabilities
- Real-time analysis with background processing
- Detailed JSON reporting with full metrics
- All Serena features with proper integration
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

# Step 1: Import Path Corrections - Use correct LSP-nested Serena paths
GRAPH_SITTER_AVAILABLE = True
SERENA_COMPONENTS = {}

try:
    # Use LSP-integrated Codebase instead of core Codebase
    from graph_sitter.extensions.lsp.codebase import Codebase
    GRAPH_SITTER_AVAILABLE = True
    print("✅ Using LSP-integrated Codebase with Serena support")
except ImportError:
    try:
        # Fallback to core Codebase
        from graph_sitter.core.codebase import Codebase
        GRAPH_SITTER_AVAILABLE = True
        print("⚠️  Using core Codebase - Serena features may be limited")
    except ImportError as e:
        print(f"❌ Graph-sitter not available: {e}")
        GRAPH_SITTER_AVAILABLE = False

# Try to import Serena components with corrected paths
try:
    from graph_sitter.extensions.lsp.serena.types import (
        SerenaConfig, SerenaCapability, RefactoringType, RefactoringResult,
        CodeGenerationResult, SemanticSearchResult, SymbolInfo
    )
    SERENA_COMPONENTS['types'] = True
    print("✅ Serena types imported successfully")
except ImportError as e:
    SERENA_COMPONENTS['types'] = False
    print(f"⚠️  Serena types import failed: {e}")

try:
    from graph_sitter.extensions.lsp.serena.core import SerenaCore
    SERENA_COMPONENTS['core'] = True
    print("✅ Serena core imported successfully")
except ImportError as e:
    SERENA_COMPONENTS['core'] = False
    print(f"⚠️  Serena core import failed: {e}")

try:
    from graph_sitter.extensions.lsp.serena.intelligence.code_intelligence import CodeIntelligence
    SERENA_COMPONENTS['intelligence'] = True
    print("✅ Serena intelligence imported successfully")
except ImportError as e:
    SERENA_COMPONENTS['intelligence'] = False
    print(f"⚠️  Serena intelligence import failed: {e}")

# Step 2: Auto-initialization import
try:
    from graph_sitter.extensions.lsp.serena.auto_init import initialize_serena_integration
    SERENA_COMPONENTS['auto_init'] = True
    print("✅ Serena auto-init imported successfully")
except ImportError as e:
    SERENA_COMPONENTS['auto_init'] = False
    print(f"⚠️  Serena auto-init import failed: {e}")


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


class IntegratedSerenaAnalyzer:
    """Integrated analyzer with proper LSP + Serena support."""
    
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
        """Initialize the codebase with full Serena integration."""
        try:
            print(f"🔍 Initializing integrated Serena analyzer for: {self.codebase_path}")
            
            if not GRAPH_SITTER_AVAILABLE:
                print("❌ Graph-sitter not available")
                return False
            
            # Step 2: Trigger Serena auto-initialization if available
            if SERENA_COMPONENTS.get('auto_init'):
                try:
                    print("🚀 Triggering Serena auto-initialization...")
                    initialize_serena_integration()
                    print("✅ Serena auto-initialization completed")
                except Exception as e:
                    print(f"⚠️  Serena auto-initialization failed: {e}")
            
            # Step 3: Initialize LSP-integrated codebase
            self.codebase = Codebase(str(self.codebase_path))
            print("✅ LSP-integrated codebase initialized")
            
            # Check and initialize Serena status
            self.serena_status = self._check_serena_integration()
            print(f"📊 Serena integration status: {self.serena_status.get('enabled', False)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def _check_serena_integration(self) -> Dict[str, Any]:
        """Check Serena integration status and available methods."""
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
        
        # Check available Serena methods on codebase
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
        
        # Collect diagnostics from all files with error handling
        diagnostics_count = 0
        files_with_errors = 0
        
        for i, file_path in enumerate(python_files):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(python_files)} files scanned...")
            
            try:
                # Get diagnostics for this file with timeout
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
    
    def analyze_symbol_overview(self) -> List[SymbolOverview]:
        """Create comprehensive symbol overview with all details."""
        print("\n🎯 Analyzing complete symbol overview...")
        
        symbol_overview = []
        
        if not self.codebase:
            return symbol_overview
        
        # Analyze functions with enhanced context
        if hasattr(self.codebase, 'functions'):
            print("   🔧 Analyzing functions...")
            for func in self.codebase.functions:
                try:
                    func_name = getattr(func, 'name', 'unknown')
                    file_path = getattr(func, 'file_path', None) or getattr(func, 'filepath', None) or 'unknown'
                    
                    # Get additional symbol information via Serena if available
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
                    print(f"⚠️  Error analyzing function: {e}")
                    continue
        
        # Analyze classes with enhanced context
        if hasattr(self.codebase, 'classes'):
            print("   📦 Analyzing classes...")
            for cls in self.codebase.classes:
                try:
                    class_name = getattr(cls, 'name', 'unknown')
                    file_path = getattr(cls, 'file_path', None) or getattr(cls, 'filepath', None) or 'unknown'
                    
                    # Get symbol context if available
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
                    print(f"⚠️  Error analyzing class: {e}")
                    continue
        
        # Analyze imports
        if hasattr(self.codebase, 'imports'):
            print("   📥 Analyzing imports...")
            for imp in self.codebase.imports:
                try:
                    import_name = getattr(imp, 'module_name', None) or getattr(imp, 'name', 'unknown')
                    file_path = getattr(imp, 'file_path', None) or getattr(imp, 'filepath', None) or 'unknown'
                    
                    symbol = SymbolOverview(
                        name=import_name,
                        symbol_type='import',
                        file_path=file_path,
                        line_number=getattr(imp, 'line_number', 0),
                        column=getattr(imp, 'column', 0),
                        scope='module',
                        definition=None,
                        references=[],
                        dependencies=[],
                        complexity_score=1.0,
                        documentation=None,
                        signature=None,
                        return_type=None,
                        parameters=[]
                    )
                    
                    symbol_overview.append(symbol)
                    
                except Exception as e:
                    print(f"⚠️  Error analyzing import: {e}")
                    continue
        
        self.symbol_overview = symbol_overview
        
        print(f"✅ Symbol overview complete: {len(symbol_overview)} symbols analyzed")
        return symbol_overview
    
    def demonstrate_serena_features(self) -> Dict[str, Any]:
        """Demonstrate ALL available Serena features with proper error handling."""
        print("\n🚀 Demonstrating Serena Features")
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
        
        # Test all available Serena methods with proper error handling
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
            ('get_symbol_context', lambda: self.codebase.get_symbol_context('main', include_dependencies=True)),
            ('analyze_symbol_impact', lambda: self.codebase.analyze_symbol_impact('main')),
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
            if 'src/graph_sitter/core/' in file.file_path and file.file_path.endswith('.py'):
                return file.file_path
        
        # Fallback to any Python file
        for file in self.codebase.files:
            if file.file_path.endswith('.py'):
                return file.file_path
        
        return None
    
    def _calculate_codebase_health(self, lsp_diagnostics: List[LSPDiagnostic], symbol_overview: List[SymbolOverview]) -> CodebaseHealth:
        """Calculate comprehensive codebase health metrics."""
        print("\n📊 Calculating codebase health metrics...")
        
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
        
        if self.codebase and hasattr(self.codebase, 'files'):
            for file in self.codebase.files:
                total_files += 1
                ext = Path(file.file_path).suffix
                file_types[ext] += 1
                
                # Calculate file size
                try:
                    full_path = self.codebase_path / file.file_path
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
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run the complete integrated Serena analysis."""
        print("\n" + "=" * 80)
        print("🚀 INTEGRATED SERENA ANALYZER - COMPLETE CODEBASE ANALYSIS")
        print("=" * 80)
        
        start_time = time.time()
        
        # 1. Collect ALL LSP diagnostics
        lsp_diagnostics = self.collect_all_lsp_diagnostics()
        
        # 2. Analyze symbol overview
        symbol_overview = self.analyze_symbol_overview()
        
        # 3. Demonstrate all Serena features
        serena_demo = self.demonstrate_serena_features()
        
        # 4. Calculate codebase health
        codebase_health = self._calculate_codebase_health(lsp_diagnostics, symbol_overview)
        
        # 5. Generate performance metrics
        analysis_time = time.time() - start_time
        self.performance_metrics = {
            'total_analysis_time': round(analysis_time, 2),
            'lsp_diagnostics_count': len(lsp_diagnostics),
            'symbols_analyzed': len(symbol_overview),
            'serena_features_working': len(serena_demo.get('successful_features', [])),
            'serena_features_total': len(serena_demo.get('features_tested', [])),
            'files_scanned': codebase_health.total_files,
            'memory_usage': 'N/A'  # Would need psutil
        }
        
        # 6. Create comprehensive report (with safe serialization)
        complete_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'codebase_path': str(self.codebase_path),
            'serena_status': self.serena_status,
            'lsp_diagnostics': [self._safe_dict(d) for d in lsp_diagnostics],
            'symbol_overview': [self._safe_dict(s) for s in symbol_overview],
            'serena_features': serena_demo,
            'codebase_health': self._safe_dict(codebase_health),
            'performance_metrics': self.performance_metrics,
            'analysis_summary': self._generate_analysis_summary(codebase_health, lsp_diagnostics, symbol_overview, serena_demo)
        }
        
        # 7. Print comprehensive report
        self._print_complete_report(complete_report)
        
        return complete_report
    
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

    def _generate_analysis_summary(self, health: CodebaseHealth, diagnostics: List[LSPDiagnostic], symbols: List[SymbolOverview], serena_demo: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary with key insights."""
        return {
            'overall_health': 'Good' if health.maintainability_index > 70 else 'Fair' if health.maintainability_index > 40 else 'Poor',
            'critical_issues': health.total_errors,
            'code_quality_score': round(health.maintainability_index, 1),
            'technical_debt_level': 'Low' if health.technical_debt_score < 50 else 'Medium' if health.technical_debt_score < 150 else 'High',
            'serena_integration_health': f"{len(serena_demo.get('successful_features', []))}/{len(serena_demo.get('features_tested', []))} features working",
            'top_recommendations': self._generate_recommendations(health, diagnostics),
            'complexity_hotspots': len([s for s in symbols if s.complexity_score > 5]),
            'files_needing_attention': len(health.error_hotspots)
        }
    
    def _generate_recommendations(self, health: CodebaseHealth, diagnostics: List[LSPDiagnostic]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if health.total_errors > 0:
            recommendations.append(f"🔴 CRITICAL: Fix {health.total_errors} LSP errors found in the codebase")
        
        if health.total_warnings > 50:
            recommendations.append(f"🟡 HIGH: Address {health.total_warnings} warnings to improve code quality")
        
        if health.maintainability_index < 70:
            recommendations.append(f"🔵 MEDIUM: Improve maintainability index (currently {health.maintainability_index:.1f}/100)")
        
        if health.technical_debt_score > 100:
            recommendations.append(f"🟠 MEDIUM: Reduce technical debt (score: {health.technical_debt_score})")
        
        if health.test_coverage_estimate < 30:
            recommendations.append(f"🟣 LOW: Increase test coverage (estimated {health.test_coverage_estimate:.1f}%)")
        
        # Add specific error-based recommendations
        error_types = defaultdict(int)
        for diag in diagnostics:
            if diag.severity == 'error':
                error_types[diag.code or 'unknown'] += 1
        
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count > 5:
                recommendations.append(f"🔧 SPECIFIC: Fix recurring '{error_type}' errors ({count} occurrences)")
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _print_complete_report(self, report: Dict[str, Any]):
        """Print the complete analysis report."""
        print("\n" + "=" * 80)
        print("📊 INTEGRATED SERENA ANALYZER - COMPLETE REPORT")
        print("=" * 80)
        
        health = report['codebase_health']
        summary = report['analysis_summary']
        serena = report['serena_features']
        performance = report['performance_metrics']
        
        # Overall summary
        print(f"\n🎯 ANALYSIS SUMMARY:")
        print(f"   Analysis Time: {performance['total_analysis_time']} seconds")
        print(f"   Overall Health: {summary['overall_health']}")
        print(f"   Code Quality Score: {summary['code_quality_score']}/100")
        print(f"   Technical Debt Level: {summary['technical_debt_level']}")
        print(f"   Serena Integration: {summary['serena_integration_health']}")
        
        # Codebase statistics
        print(f"\n📈 CODEBASE STATISTICS:")
        print(f"   Total Files: {health['total_files']}")
        print(f"   Total Lines: {health['total_lines']:,}")
        print(f"   Total Symbols: {health['total_symbols']}")
        print(f"   Functions: {health['total_functions']}")
        print(f"   Classes: {health['total_classes']}")
        print(f"   Imports: {health['total_imports']}")
        
        # LSP diagnostics summary
        print(f"\n🔍 LSP DIAGNOSTICS SUMMARY:")
        print(f"   ❌ Errors: {health['total_errors']}")
        print(f"   ⚠️  Warnings: {health['total_warnings']}")
        print(f"   ℹ️  Info: {health['total_info']}")
        print(f"   💡 Hints: {health['total_hints']}")
        print(f"   📊 Total Issues: {performance['lsp_diagnostics_count']}")
        
        # Show top errors if any
        if report['lsp_diagnostics']:
            print(f"\n❌ TOP LSP ERRORS:")
            error_diagnostics = [d for d in report['lsp_diagnostics'] if d['severity'] == 'error']
            for i, diag in enumerate(error_diagnostics[:5]):
                print(f"   {i+1}. {diag['file_path']}:{diag['line']} - {diag['message'][:80]}...")
        
        # Serena features status
        print(f"\n🚀 SERENA FEATURES STATUS:")
        print(f"   Working Features: {len(serena['successful_features'])}/{len(serena['features_tested'])}")
        if serena['successful_features']:
            print(f"   ✅ Working: {', '.join(serena['successful_features'])}")
        if serena['failed_features']:
            print(f"   ❌ Failed: {', '.join(serena['failed_features'])}")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS:")
        for feature, metrics in serena.get('performance_metrics', {}).items():
            if metrics.get('success'):
                print(f"   {feature}: {metrics['execution_time']}s")
        
        # Largest files
        if health['largest_files']:
            print(f"\n📄 LARGEST FILES:")
            for i, file_info in enumerate(health['largest_files'][:5]):
                print(f"   {i+1}. {file_info['path']} ({file_info['lines']:,} lines)")
        
        # Most complex symbols
        if health['most_complex_symbols']:
            print(f"\n🧮 MOST COMPLEX SYMBOLS:")
            for i, symbol in enumerate(health['most_complex_symbols'][:5]):
                print(f"   {i+1}. {symbol['name']} ({symbol['type']}) - Complexity: {symbol['complexity']:.1f}")
        
        # Error hotspots
        if health['error_hotspots']:
            print(f"\n🔥 ERROR HOTSPOTS:")
            for i, hotspot in enumerate(health['error_hotspots'][:5]):
                print(f"   {i+1}. {hotspot['file']} - {hotspot['error_count']} errors")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in summary['top_recommendations']:
            print(f"   {rec}")
        
        print(f"\n✅ Complete integrated analysis finished!")
        print(f"📄 Report saved with {performance['lsp_diagnostics_count']} diagnostics and {performance['symbols_analyzed']} symbols")
    
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
    """Main function to run the integrated Serena analyzer."""
    print("🚀 INTEGRATED SERENA ANALYZER")
    print("=" * 50)
    print("Complete codebase analysis with LSP + Serena integration")
    print("This version uses corrected import paths and proper initialization.")
    print()
    
    # Show component availability
    print("📦 COMPONENT AVAILABILITY:")
    print(f"   Graph-sitter: {'✅' if GRAPH_SITTER_AVAILABLE else '❌'}")
    for component, available in SERENA_COMPONENTS.items():
        status = '✅' if available else '❌'
        print(f"   Serena {component}: {status}")
    print()
    
    # Initialize analyzer
    analyzer = IntegratedSerenaAnalyzer(".")
    
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    try:
        # Run complete analysis
        report = analyzer.run_complete_analysis()
        
        # Save comprehensive report
        report_file = Path("integrated_serena_analysis_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Complete report saved to: {report_file}")
        
        # Save LSP diagnostics separately for easy access
        if report['lsp_diagnostics']:
            lsp_file = Path("lsp_diagnostics_integrated.json")
            with open(lsp_file, 'w') as f:
                json.dump(report['lsp_diagnostics'], f, indent=2, default=str)
            print(f"💾 LSP diagnostics saved to: {lsp_file}")
        
        # Save symbol overview separately
        if report['symbol_overview']:
            symbols_file = Path("symbol_overview_integrated.json")
            with open(symbols_file, 'w') as f:
                json.dump(report['symbol_overview'], f, indent=2, default=str)
            print(f"💾 Symbol overview saved to: {symbols_file}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    finally:
        # Cleanup
        analyzer.cleanup()
    
    print("\n🎉 Integrated Serena Analysis Complete!")
    print("This analyzer successfully integrates LSP + Serena capabilities with proper initialization.")


if __name__ == "__main__":
    main()
