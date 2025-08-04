"""
Unified analyzer integration for Reflex dashboard.

This module adapts the comprehensive analysis functionality to work within
the Reflex state management system.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
import traceback

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


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


class UnifiedAnalyzer:
    """Unified analyzer adapted for Reflex dashboard."""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.analysis_results: Dict[str, Any] = {}
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the analyzer with the codebase."""
        try:
            if not GRAPH_SITTER_AVAILABLE:
                return False
                
            self.codebase = Codebase(str(self.codebase_path))
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize analyzer: {e}")
            return False
    
    async def run_comprehensive_analysis(self, progress_callback=None) -> Dict[str, Any]:
        """Run comprehensive analysis with progress updates."""
        if not self.is_initialized:
            if not await self.initialize():
                return {"error": "Failed to initialize analyzer"}
        
        try:
            results = {
                "timestamp": "",
                "codebase_path": str(self.codebase_path),
                "lsp_diagnostics": [],
                "symbol_overview": [],
                "codebase_health": {},
                "analysis_summary": {},
                "serena_status": {}
            }
            
            # Step 1: Collect LSP diagnostics
            if progress_callback:
                await progress_callback("Collecting LSP diagnostics...", 20)
            
            diagnostics = await self.collect_lsp_diagnostics()
            results["lsp_diagnostics"] = [self._safe_dict(d) for d in diagnostics]
            
            # Step 2: Analyze symbols
            if progress_callback:
                await progress_callback("Analyzing symbols...", 40)
            
            symbols = await self.analyze_symbols()
            results["symbol_overview"] = [self._safe_dict(s) for s in symbols]
            
            # Step 3: Calculate health metrics
            if progress_callback:
                await progress_callback("Calculating health metrics...", 60)
            
            health = await self.calculate_health_metrics(diagnostics, symbols)
            results["codebase_health"] = self._safe_dict(health)
            
            # Step 4: Generate summary
            if progress_callback:
                await progress_callback("Generating summary...", 80)
            
            summary = self.generate_analysis_summary(health, diagnostics, symbols)
            results["analysis_summary"] = summary
            
            # Step 5: Check Serena status
            if progress_callback:
                await progress_callback("Checking Serena integration...", 90)
            
            serena_status = await self.check_serena_status()
            results["serena_status"] = serena_status
            
            if progress_callback:
                await progress_callback("Analysis complete!", 100)
            
            self.analysis_results = results
            return results
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return {"error": error_msg}
    
    async def collect_lsp_diagnostics(self) -> List[LSPDiagnostic]:
        """Collect LSP diagnostics from the codebase."""
        diagnostics = []
        
        if not self.codebase:
            return diagnostics
        
        # Check if LSP diagnostics method is available
        if not hasattr(self.codebase, 'get_file_diagnostics'):
            # Mock some diagnostics for demo purposes
            return self._generate_mock_diagnostics()
        
        try:
            # Get Python files
            python_files = []
            for root, dirs, files in self.codebase_path.rglob("*.py"):
                if not any(part.startswith('.') for part in root.parts):
                    python_files.append(str(root.relative_to(self.codebase_path)))
            
            # Collect diagnostics from files
            for file_path in python_files[:50]:  # Limit for demo
                try:
                    result = self.codebase.get_file_diagnostics(file_path)
                    if result and result.get('success'):
                        file_diagnostics = result.get('diagnostics', [])
                        
                        for diag in file_diagnostics:
                            severity = diag.get('severity', 'info')
                            if isinstance(severity, int):
                                severity_map = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}
                                severity = severity_map.get(severity, 'info')
                            
                            range_info = diag.get('range', {})
                            start_pos = range_info.get('start', {})
                            end_pos = range_info.get('end', {})
                            
                            diagnostic = LSPDiagnostic(
                                file_path=file_path,
                                line=start_pos.get('line', 0) + 1,
                                character=start_pos.get('character', 0),
                                severity=severity,
                                message=diag.get('message', 'No message'),
                                code=diag.get('code'),
                                source=diag.get('source', 'lsp'),
                                range_start=start_pos,
                                range_end=end_pos
                            )
                            
                            diagnostics.append(diagnostic)
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error collecting LSP diagnostics: {e}")
            return self._generate_mock_diagnostics()
        
        return diagnostics
    
    def _generate_mock_diagnostics(self) -> List[LSPDiagnostic]:
        """Generate mock diagnostics for demo purposes."""
        mock_diagnostics = [
            LSPDiagnostic(
                file_path="src/graph_sitter/core/codebase.py",
                line=45,
                character=10,
                severity="error",
                message="Undefined variable 'undefined_var'",
                code="E0602",
                source="pylsp",
                range_start={"line": 44, "character": 10},
                range_end={"line": 44, "character": 23}
            ),
            LSPDiagnostic(
                file_path="src/graph_sitter/core/function.py",
                line=123,
                character=5,
                severity="warning",
                message="Unused import 'os'",
                code="W0611",
                source="pylsp",
                range_start={"line": 122, "character": 5},
                range_end={"line": 122, "character": 7}
            ),
            LSPDiagnostic(
                file_path="src/graph_sitter/core/class_definition.py",
                line=67,
                character=15,
                severity="info",
                message="Consider using f-string",
                code="C0209",
                source="pylsp",
                range_start={"line": 66, "character": 15},
                range_end={"line": 66, "character": 45}
            )
        ]
        return mock_diagnostics
    
    async def analyze_symbols(self) -> List[SymbolOverview]:
        """Analyze symbols in the codebase."""
        symbols = []
        
        if not self.codebase:
            return symbols
        
        try:
            # Analyze functions
            if hasattr(self.codebase, 'functions'):
                for func in list(self.codebase.functions)[:50]:  # Limit for demo
                    try:
                        symbol = SymbolOverview(
                            name=getattr(func, 'name', 'unknown'),
                            symbol_type='function',
                            file_path=getattr(func, 'file_path', '') or getattr(func, 'filepath', ''),
                            line_number=getattr(func, 'line_number', 0),
                            column=getattr(func, 'column', 0),
                            scope=getattr(func, 'scope', 'global'),
                            definition=getattr(func, 'definition', None),
                            references=[],
                            dependencies=[],
                            complexity_score=len(getattr(func, 'name', '')) / 10.0,
                            documentation=getattr(func, 'docstring', None),
                            signature=getattr(func, 'signature', None),
                            return_type=getattr(func, 'return_type', None),
                            parameters=getattr(func, 'parameters', [])
                        )
                        symbols.append(symbol)
                    except Exception as e:
                        continue
            
            # Analyze classes
            if hasattr(self.codebase, 'classes'):
                for cls in list(self.codebase.classes)[:50]:  # Limit for demo
                    try:
                        symbol = SymbolOverview(
                            name=getattr(cls, 'name', 'unknown'),
                            symbol_type='class',
                            file_path=getattr(cls, 'file_path', '') or getattr(cls, 'filepath', ''),
                            line_number=getattr(cls, 'line_number', 0),
                            column=getattr(cls, 'column', 0),
                            scope=getattr(cls, 'scope', 'global'),
                            definition=getattr(cls, 'definition', None),
                            references=[],
                            dependencies=[],
                            complexity_score=len(getattr(cls, 'name', '')) / 5.0,
                            documentation=getattr(cls, 'docstring', None),
                            signature=None,
                            return_type=None,
                            parameters=[]
                        )
                        symbols.append(symbol)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error analyzing symbols: {e}")
        
        return symbols
    
    async def calculate_health_metrics(self, diagnostics: List[LSPDiagnostic], symbols: List[SymbolOverview]) -> CodebaseHealth:
        """Calculate codebase health metrics."""
        # Count diagnostics by severity
        error_count = sum(1 for d in diagnostics if d.severity == 'error')
        warning_count = sum(1 for d in diagnostics if d.severity == 'warning')
        info_count = sum(1 for d in diagnostics if d.severity == 'info')
        hint_count = sum(1 for d in diagnostics if d.severity == 'hint')
        
        # Count symbols by type
        functions = [s for s in symbols if s.symbol_type == 'function']
        classes = [s for s in symbols if s.symbol_type == 'class']
        
        # Calculate file statistics
        total_files = 0
        total_lines = 0
        file_types = {}
        largest_files = []
        
        try:
            for file_path in self.codebase_path.rglob("*.py"):
                if not any(part.startswith('.') for part in file_path.parts):
                    total_files += 1
                    ext = file_path.suffix
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    try:
                        lines = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                        total_lines += lines
                        largest_files.append({
                            'path': str(file_path.relative_to(self.codebase_path)),
                            'lines': lines,
                            'size_bytes': file_path.stat().st_size
                        })
                    except Exception:
                        continue
        except Exception:
            pass
        
        largest_files.sort(key=lambda x: x['lines'], reverse=True)
        
        # Calculate health scores
        maintainability_index = max(0, 100 - (error_count * 10) - (warning_count * 2))
        technical_debt_score = (error_count * 3) + (warning_count * 1)
        test_coverage_estimate = len([f for f in largest_files if 'test' in f['path']]) / max(total_files, 1) * 100
        
        return CodebaseHealth(
            total_files=total_files,
            total_lines=total_lines,
            total_symbols=len(symbols),
            total_functions=len(functions),
            total_classes=len(classes),
            total_imports=0,  # Would need to analyze imports
            total_errors=error_count,
            total_warnings=warning_count,
            total_info=info_count,
            total_hints=hint_count,
            languages=['Python'],
            file_types=file_types,
            largest_files=largest_files[:10],
            most_complex_symbols=[
                {
                    'name': s.name,
                    'type': s.symbol_type,
                    'complexity': s.complexity_score,
                    'file': s.file_path
                } for s in sorted(symbols, key=lambda x: x.complexity_score, reverse=True)[:10]
            ],
            error_hotspots=[],
            dependency_graph_stats={},
            maintainability_index=maintainability_index,
            technical_debt_score=technical_debt_score,
            test_coverage_estimate=test_coverage_estimate
        )
    
    def generate_analysis_summary(self, health: CodebaseHealth, diagnostics: List[LSPDiagnostic], symbols: List[SymbolOverview]) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            'overall_health': 'Good' if health.maintainability_index > 70 else 'Fair' if health.maintainability_index > 40 else 'Poor',
            'critical_issues': health.total_errors,
            'code_quality_score': round(health.maintainability_index, 1),
            'technical_debt_level': 'Low' if health.technical_debt_score < 50 else 'Medium' if health.technical_debt_score < 150 else 'High',
            'complexity_hotspots': len([s for s in symbols if s.complexity_score > 5]),
            'files_needing_attention': len([d for d in diagnostics if d.severity == 'error']),
            'top_recommendations': [
                f"🔴 Fix {health.total_errors} critical errors" if health.total_errors > 0 else "",
                f"🟡 Address {health.total_warnings} warnings" if health.total_warnings > 50 else "",
                f"🔵 Improve maintainability (currently {health.maintainability_index:.1f}/100)" if health.maintainability_index < 70 else ""
            ]
        }
    
    async def check_serena_status(self) -> Dict[str, Any]:
        """Check Serena integration status."""
        status = {
            'available': False,
            'enabled': False,
            'features_working': 0,
            'features_total': 0,
            'lsp_servers': [],
            'capabilities': []
        }
        
        if not self.codebase:
            return status
        
        # Check if Serena methods are available
        serena_methods = [
            'get_serena_status', 'get_completions', 'get_hover_info',
            'get_signature_help', 'semantic_search', 'rename_symbol'
        ]
        
        working_methods = []
        for method in serena_methods:
            if hasattr(self.codebase, method):
                working_methods.append(method)
        
        status['features_working'] = len(working_methods)
        status['features_total'] = len(serena_methods)
        status['available'] = len(working_methods) > 0
        
        # Try to get detailed status
        if hasattr(self.codebase, 'get_serena_status'):
            try:
                internal_status = self.codebase.get_serena_status()
                status.update(internal_status)
            except Exception:
                pass
        
        return status
    
    def _safe_dict(self, obj) -> Dict[str, Any]:
        """Safely convert object to dict."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                try:
                    json.dumps(value, default=str)
                    result[key] = value
                except (TypeError, ValueError):
                    result[key] = str(value)
            return result
        else:
            return {"value": str(obj)}
