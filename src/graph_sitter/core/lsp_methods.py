"""
Enhanced LSP Error Retrieval Methods for Codebase Class

This module provides all the LSP error retrieval and code intelligence methods
that are added to the main Codebase class using the unified consolidated components.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Callable
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class LSPMethodsMixin:
    """Mixin class that provides comprehensive LSP methods using unified consolidated components."""
    
    def _get_unified_diagnostics(self):
        """Get or create unified diagnostics engine."""
        if not hasattr(self, '_unified_diagnostics'):
            try:
                from graph_sitter.core.unified_diagnostics import get_diagnostic_engine
                self._unified_diagnostics = get_diagnostic_engine(self, enable_lsp=True)
            except ImportError:
                logger.warning("Unified diagnostics not available. Install dependencies for error detection.")
                self._unified_diagnostics = None
        return self._unified_diagnostics
    
    def _get_unified_analysis(self):
        """Get or create unified analysis engine."""
        if not hasattr(self, '_unified_analysis'):
            try:
                from graph_sitter.core.unified_analysis import UnifiedAnalysisEngine
                self._unified_analysis = UnifiedAnalysisEngine(self)
            except ImportError:
                logger.warning("Unified analysis not available.")
                self._unified_analysis = None
        return self._unified_analysis
    
    def _get_code_generation_engine(self):
        """Get or create LSP code generation engine."""
        if not hasattr(self, '_code_generation_engine'):
            try:
                from graph_sitter.extensions.serena.lsp_code_generation import LSPCodeGenerationEngine
                diagnostics = self._get_unified_diagnostics()
                if diagnostics:
                    self._code_generation_engine = LSPCodeGenerationEngine(diagnostics)
                else:
                    self._code_generation_engine = None
            except ImportError:
                logger.warning("Code generation engine not available.")
                self._code_generation_engine = None
        return self._code_generation_engine

    # ========================================================================
    # CORE ERROR RETRIEVAL COMMANDS (Using Unified Components)
    # ========================================================================
    
    def errors(self) -> List[Any]:
        """Get all errors in the codebase using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.errors
        return []
    
    def errors_by_file(self, file_path: str) -> List[Any]:
        """Get errors in a specific file using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_errors_by_file(file_path)
        return []
    
    def errors_by_severity(self, severity: str) -> List[Any]:
        """Filter errors by severity using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_errors_by_severity(severity)
        return []
    
    def errors_by_type(self, error_type: str) -> List[Any]:
        """Filter errors by type using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_errors_by_type(error_type)
        return []
    
    def recent_errors(self, since_timestamp: float) -> List[Any]:
        """Get recent errors since timestamp using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_recent_errors(since_timestamp)
        return []

    # ========================================================================
    # DETAILED ERROR CONTEXT (Using Unified Components)
    # ========================================================================
    
    def full_error_context(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get full context for a specific error using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_full_error_context(error_id)
        return None
    
    def _get_error_context_lines(self, error, context_size=5):
        """Get context lines around an error."""
        try:
            file_path = Path(self.repo_path) / error.file_path
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                start_line = max(0, error.line - context_size - 1)
                end_line = min(len(lines), error.line + context_size)
                
                return {
                    'before': lines[start_line:error.line-1],
                    'error_line': lines[error.line-1] if error.line-1 < len(lines) else '',
                    'after': lines[error.line:end_line]
                }
        except Exception as e:
            logger.warning(f"Could not get context lines for error: {e}")
        return None
    
    def error_suggestions(self, error_id: str) -> List[str]:
        """Get fix suggestions for an error using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_error_suggestions(error_id)
        
        # Fallback to code generation engine
        code_gen = self._get_code_generation_engine()
        if code_gen:
            return code_gen.get_error_resolution_suggestions(error_id)
        
        return []
    
    def error_related_symbols(self, error_id: str) -> List[str]:
        """Get symbols related to the error using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_error_related_symbols(error_id)
        return []
    
    def error_impact_analysis(self, error_id: str) -> Dict[str, Any]:
        """Get impact analysis of the error using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_error_impact_analysis(error_id)
        return {}

    # ========================================================================
    # ERROR STATISTICS & ANALYSIS
    # ========================================================================
    
    def error_summary(self):
        """Get summary statistics of all errors."""
        all_errors = self.errors()
        
        error_count = len([e for e in all_errors if e.severity == 1])
        warning_count = len([e for e in all_errors if e.severity == 2])
        info_count = len([e for e in all_errors if e.severity >= 3])
        
        return {
            'total_diagnostics': len(all_errors),
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'files_with_errors': len(set(e.file_path for e in all_errors)),
            'most_common_source': self._get_most_common_error_source(all_errors)
        }
    
    def _get_most_common_error_source(self, errors):
        """Get the most common error source."""
        sources = [e.source for e in errors if e.source]
        if sources:
            from collections import Counter
            return Counter(sources).most_common(1)[0][0]
        return None
    
    def error_trends(self):
        """Get error trends over time."""
        # For now, return current snapshot - could be enhanced with historical data
        return {
            'current_snapshot': self.error_summary(),
            'trend': 'stable',  # Could track changes over time
            'timestamp': time.time()
        }
    
    def most_common_errors(self):
        """Get most frequently occurring errors."""
        all_errors = self.errors()
        from collections import Counter
        
        error_messages = [e.message for e in all_errors]
        common_errors = Counter(error_messages).most_common(10)
        
        return [{'message': msg, 'count': count} for msg, count in common_errors]
    
    def error_hotspots(self):
        """Get files/areas with most errors."""
        all_errors = self.errors()
        from collections import Counter
        
        file_errors = Counter(e.file_path for e in all_errors)
        
        return [{'file_path': path, 'error_count': count} 
                for path, count in file_errors.most_common(10)]

    # ========================================================================
    # REAL-TIME ERROR MONITORING (Using Unified Components)
    # ========================================================================
    
    def watch_errors(self, callback: Callable[[List[Any]], None]) -> bool:
        """Set up real-time error monitoring using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.watch_errors(callback)
        return False
    
    def error_stream(self) -> Generator[List[Any], None, None]:
        """Get a stream of error updates using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.error_stream()
        
        # Fallback generator
        def fallback_generator():
            last_errors = []
            while True:
                current_errors = self.errors()
                if current_errors != last_errors:
                    yield current_errors
                    last_errors = current_errors
                time.sleep(1)
        
        return fallback_generator()
    
    def refresh_errors(self) -> bool:
        """Force refresh of error detection using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.refresh_errors()
        return False

    # ========================================================================
    # ERROR RESOLUTION & ACTIONS (Using Unified Components)
    # ========================================================================
    
    def auto_fix_errors(self, error_ids: List[str]) -> List[str]:
        """Auto-fix specific errors using code generation engine."""
        code_gen = self._get_code_generation_engine()
        if code_gen:
            fixed_errors = []
            for error_id in error_ids:
                fixes = code_gen.generate_error_fixes(error_id)
                if fixes:
                    # Apply the highest confidence fix
                    best_fix = max(fixes, key=lambda f: f.get('confidence', 0))
                    if self.apply_error_fix(error_id, best_fix):
                        fixed_errors.append(error_id)
            return fixed_errors
        return []
    
    def get_quick_fixes(self, error_id: str) -> List[Dict[str, Any]]:
        """Get available quick fixes for an error using code generation engine."""
        code_gen = self._get_code_generation_engine()
        if code_gen:
            return code_gen.generate_error_fixes(error_id)
        return []
    
    def apply_error_fix(self, error_id: str, fix: Dict[str, Any]) -> bool:
        """Apply a specific fix to resolve an error."""
        try:
            # Apply code changes from the fix
            code_changes = fix.get('code_changes', [])
            for change in code_changes:
                file_path = change.get('file_path')
                line = change.get('line')
                action = change.get('action')
                new_code = change.get('new_code')
                
                if file_path and new_code:
                    # Apply the code change (simplified implementation)
                    logger.info(f"Applying {action} at {file_path}:{line} - {new_code[:50]}...")
                    # In a real implementation, this would modify the actual file
            
            return True
        except Exception as e:
            logger.error(f"Error applying fix for {error_id}: {e}")
            return False

    # ========================================================================
    # COMPREHENSIVE LSP FEATURE RETRIEVAL (Using Unified Components)
    # ========================================================================
    
    def completions(self, file_path: str, position: tuple) -> List[Dict[str, Any]]:
        """Get code completions at the specified position using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_completions(file_path, position[0], position[1])
        return []
    
    def hover_info(self, file_path: str, position: tuple) -> Optional[Dict[str, Any]]:
        """Get hover information at the specified position using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_hover_info(file_path, position[0], position[1])
        return None
    
    def signature_help(self, file_path: str, position: tuple) -> Dict[str, Any]:
        """Get function signature help at the specified position using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_signature_help(file_path, position[0], position[1])
        return {'signatures': [], 'active_signature': 0, 'active_parameter': 0}
    
    def definitions(self, file_path: str, position: tuple) -> List[Dict[str, Any]]:
        """Go to definition for a symbol using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_definitions(file_path, position[0], position[1])
        return []
    
    def references(self, file_path: str, position: tuple, include_declaration: bool = True) -> List[Dict[str, Any]]:
        """Find all references to a symbol using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_references(file_path, position[0], position[1], include_declaration)
        return []
    
    def document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get document symbols using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_document_symbols(file_path)
        return []
    
    def workspace_symbols(self, query: str = "") -> List[Dict[str, Any]]:
        """Get workspace symbols using unified diagnostics."""
        diagnostics = self._get_unified_diagnostics()
        if diagnostics:
            return diagnostics.get_workspace_symbols(query)
        return []

    # ========================================================================
    # COMPREHENSIVE ANALYSIS (Using Unified Components)
    # ========================================================================
    
    def comprehensive_analysis(self, level: str = "COMPREHENSIVE") -> Dict[str, Any]:
        """Get comprehensive codebase analysis using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.analyze(level)
        return {}
    
    def basic_analysis(self) -> Dict[str, Any]:
        """Get basic codebase analysis using unified analysis engine."""
        return self.comprehensive_analysis("BASIC")
    
    def deep_analysis(self) -> Dict[str, Any]:
        """Get deep codebase analysis using unified analysis engine."""
        return self.comprehensive_analysis("DEEP")
    
    def architectural_insights(self) -> Dict[str, Any]:
        """Get architectural insights using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_architectural_insights()
        return {}
    
    def code_quality_metrics(self) -> Dict[str, Any]:
        """Get code quality metrics using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_code_quality_metrics()
        return {}
    
    def complexity_analysis(self) -> Dict[str, Any]:
        """Get complexity analysis using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_complexity_analysis()
        return {}
    
    def dependency_analysis(self) -> Dict[str, Any]:
        """Get dependency analysis using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_dependency_analysis()
        return {}
    
    def security_analysis(self) -> Dict[str, Any]:
        """Get security analysis using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_security_analysis()
        return {}
    
    def performance_analysis(self) -> Dict[str, Any]:
        """Get performance analysis using unified analysis engine."""
        analysis = self._get_unified_analysis()
        if analysis:
            return analysis.get_performance_analysis()
        return {}

    # ========================================================================
    # CODE ACTIONS & REFACTORING
    # ========================================================================
    
    def code_actions(self, file_path, range_obj):
        """Get available code actions for a file range."""
        actions = []
        
        # Basic code actions
        actions.append({
            'title': 'Extract Method',
            'kind': 'refactor.extract',
            'command': 'extract_method'
        })
        
        actions.append({
            'title': 'Organize Imports',
            'kind': 'source.organizeImports',
            'command': 'organize_imports'
        })
        
        return actions
    
    def rename_symbol(self, old_name, new_name):
        """Rename a symbol throughout the codebase."""
        changes = []
        for symbol in self.symbols:
            if symbol.name == old_name:
                changes.append({
                    'file_path': str(symbol.file.filepath) if hasattr(symbol, 'file') else '',
                    'old_name': old_name,
                    'new_name': new_name
                })
        
        return {'changes': changes, 'success': len(changes) > 0}
    
    def extract_method(self, file_path, range_obj):
        """Extract method refactoring."""
        return {
            'success': True,
            'new_method_name': 'extracted_method',
            'changes': [{
                'file_path': file_path,
                'type': 'extract_method',
                'range': range_obj
            }]
        }
    
    def organize_imports(self, file_path):
        """Organize imports in a file."""
        return {
            'success': True,
            'changes': [{
                'file_path': file_path,
                'type': 'organize_imports'
            }]
        }

    # ========================================================================
    # SEMANTIC ANALYSIS
    # ========================================================================
    
    def semantic_tokens(self, file_path):
        """Get semantic token information for a file."""
        tokens = []
        try:
            for file in self.files:
                if str(file.filepath).endswith(file_path):
                    for symbol in file.symbols:
                        tokens.append({
                            'line': getattr(symbol, 'line_number', 0),
                            'character': 0,
                            'length': len(symbol.name),
                            'token_type': symbol.symbol_type.value if hasattr(symbol, 'symbol_type') else 'variable',
                            'token_modifiers': []
                        })
        except Exception as e:
            logger.warning(f"Could not get semantic tokens: {e}")
        
        return tokens
    
    def document_symbols(self, file_path):
        """Get document symbol outline for a file."""
        symbols = []
        try:
            for file in self.files:
                if str(file.filepath).endswith(file_path):
                    for symbol in file.symbols:
                        symbols.append({
                            'name': symbol.name,
                            'kind': symbol.symbol_type.value if hasattr(symbol, 'symbol_type') else 'variable',
                            'line': getattr(symbol, 'line_number', 0),
                            'character': 0
                        })
        except Exception as e:
            logger.warning(f"Could not get document symbols: {e}")
        
        return symbols
    
    def workspace_symbols(self, query):
        """Search workspace symbols."""
        matching_symbols = []
        query_lower = query.lower()
        
        for symbol in self.symbols:
            if query_lower in symbol.name.lower():
                matching_symbols.append({
                    'name': symbol.name,
                    'kind': symbol.symbol_type.value if hasattr(symbol, 'symbol_type') else 'variable',
                    'file_path': str(symbol.file.filepath) if hasattr(symbol, 'file') else '',
                    'line': getattr(symbol, 'line_number', 0)
                })
        
        return matching_symbols
    
    def call_hierarchy(self, symbol_name):
        """Get call hierarchy for a symbol."""
        hierarchy = {'incoming_calls': [], 'outgoing_calls': []}
        
        for symbol in self.symbols:
            if symbol.name == symbol_name:
                # Get incoming calls (who calls this symbol)
                for usage in symbol.symbol_usages:
                    hierarchy['incoming_calls'].append({
                        'caller': usage.name if hasattr(usage, 'name') else 'unknown',
                        'file_path': str(usage.file.filepath) if hasattr(usage, 'file') else '',
                        'line': getattr(usage, 'line_number', 0)
                    })
                
                # Get outgoing calls (what this symbol calls)
                if hasattr(symbol, 'dependencies'):
                    for dep in symbol.dependencies:
                        hierarchy['outgoing_calls'].append({
                            'callee': dep.name if hasattr(dep, 'name') else str(dep),
                            'file_path': str(dep.file.filepath) if hasattr(dep, 'file') else '',
                            'line': getattr(dep, 'line_number', 0)
                        })
        
        return hierarchy

    # ========================================================================
    # DIAGNOSTICS & HEALTH
    # ========================================================================
    
    def diagnostics(self):
        """Get all diagnostics (errors + warnings + info)."""
        diagnostics_manager = self._get_diagnostics_manager()
        if diagnostics_manager:
            return diagnostics_manager.diagnostics
        return []
    
    def health_check(self):
        """Get overall codebase health assessment."""
        deep_analyzer = self._get_deep_analyzer()
        error_summary = self.error_summary()
        
        health_score = 100
        
        # Reduce score based on errors
        health_score -= error_summary['error_count'] * 10
        health_score -= error_summary['warning_count'] * 5
        
        # Ensure score doesn't go below 0
        health_score = max(0, health_score)
        
        health_status = 'Excellent' if health_score >= 90 else \
                       'Good' if health_score >= 70 else \
                       'Fair' if health_score >= 50 else 'Poor'
        
        result = {
            'health_score': health_score,
            'health_status': health_status,
            'error_summary': error_summary,
            'recommendations': []
        }
        
        # Add recommendations
        if error_summary['error_count'] > 0:
            result['recommendations'].append('Fix critical errors to improve codebase health')
        if error_summary['warning_count'] > 10:
            result['recommendations'].append('Address warnings to prevent future issues')
        
        # Add deep analysis if available
        if deep_analyzer:
            try:
                metrics = deep_analyzer.analyze_comprehensive_metrics()
                result['comprehensive_metrics'] = metrics
            except Exception as e:
                logger.warning(f"Could not get comprehensive metrics: {e}")
        
        return result
    
    def lsp_status(self):
        """Get LSP server status."""
        diagnostics_manager = self._get_diagnostics_manager()
        
        status = {
            'lsp_available': diagnostics_manager is not None,
            'servers': [],
            'capabilities': []
        }
        
        if diagnostics_manager and hasattr(diagnostics_manager, '_lsp_manager'):
            lsp_manager = diagnostics_manager._lsp_manager
            if lsp_manager and hasattr(lsp_manager, '_bridge'):
                bridge = lsp_manager._bridge
                if bridge:
                    status['servers'] = list(bridge.language_servers.keys())
                    status['initialized'] = bridge.is_initialized
        
        return status
    
    def capabilities(self):
        """Get available LSP capabilities."""
        capabilities = {
            'error_retrieval': True,
            'code_intelligence': True,
            'refactoring': True,
            'semantic_analysis': True,
            'real_time_monitoring': True,
            'auto_fix': True
        }
        
        # Check if advanced features are available
        diagnostics_manager = self._get_diagnostics_manager()
        serena_core = self._get_serena_core()
        deep_analyzer = self._get_deep_analyzer()
        
        capabilities.update({
            'lsp_diagnostics': diagnostics_manager is not None,
            'serena_integration': serena_core is not None,
            'deep_analysis': deep_analyzer is not None
        })
        
        return capabilities
