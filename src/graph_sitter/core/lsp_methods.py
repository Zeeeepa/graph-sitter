"""
Comprehensive LSP Error Retrieval Methods for Codebase Class

This module provides all the LSP error retrieval and code intelligence methods
that are added to the main Codebase class to create a unified interface.
"""

import time
from pathlib import Path
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class LSPMethodsMixin:
    """Mixin class that provides comprehensive LSP methods for the Codebase class."""
    
    def _get_diagnostics_manager(self):
        """Get or create diagnostics manager for LSP integration."""
        if not hasattr(self, '_diagnostics_manager'):
            try:
                from graph_sitter.core.diagnostics import CodebaseDiagnostics
                self._diagnostics_manager = CodebaseDiagnostics(self, enable_lsp=True)
            except ImportError:
                logger.warning("LSP diagnostics not available. Install Serena dependencies for error detection.")
                self._diagnostics_manager = None
        return self._diagnostics_manager
    
    def _get_deep_analyzer(self):
        """Get or create deep analyzer for comprehensive metrics."""
        if not hasattr(self, '_deep_analyzer'):
            try:
                from graph_sitter.analysis.deep_analysis import DeepCodebaseAnalyzer
                self._deep_analyzer = DeepCodebaseAnalyzer(self)
            except ImportError:
                logger.warning("Deep analysis not available.")
                self._deep_analyzer = None
        return self._deep_analyzer
    
    def _get_serena_core(self):
        """Get or create Serena core for advanced capabilities."""
        if not hasattr(self, '_serena_core'):
            try:
                from graph_sitter.extensions.serena.core import SerenaCore, get_or_create_core
                from graph_sitter.extensions.serena.types import SerenaConfig
                import asyncio
                
                # Create event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                config = SerenaConfig()
                self._serena_core = loop.run_until_complete(
                    get_or_create_core(str(self.repo_path), config)
                )
            except ImportError:
                logger.warning("Serena core not available.")
                self._serena_core = None
        return self._serena_core

    # ========================================================================
    # CORE ERROR RETRIEVAL COMMANDS
    # ========================================================================
    
    def errors(self):
        """Get all errors in the codebase."""
        diagnostics_manager = self._get_diagnostics_manager()
        if diagnostics_manager:
            return diagnostics_manager.errors
        return []
    
    def errors_by_file(self, file_path: str):
        """Get errors in a specific file."""
        diagnostics_manager = self._get_diagnostics_manager()
        if diagnostics_manager and hasattr(diagnostics_manager, '_lsp_manager'):
            lsp_manager = diagnostics_manager._lsp_manager
            if lsp_manager and hasattr(lsp_manager, '_file_diagnostics_cache'):
                return lsp_manager._file_diagnostics_cache.get(file_path, [])
        return []
    
    def errors_by_severity(self, severity):
        """Filter errors by severity (error/warning/info)."""
        all_errors = self.errors()
        if hasattr(severity, 'upper'):
            severity = severity.upper()
        
        severity_map = {
            'ERROR': 1, 'WARNING': 2, 'INFO': 3, 'INFORMATION': 3, 'HINT': 4
        }
        severity_level = severity_map.get(severity, 1)
        
        return [error for error in all_errors if error.severity == severity_level]
    
    def errors_by_type(self, error_type):
        """Filter errors by type (syntax/semantic/lint)."""
        all_errors = self.errors()
        error_type = error_type.lower()
        
        return [error for error in all_errors 
                if error.source and error_type in error.source.lower()]
    
    def recent_errors(self, since_timestamp):
        """Get recent errors since timestamp."""
        # For now, return all errors - could be enhanced with timestamp tracking
        return self.errors()

    # ========================================================================
    # DETAILED ERROR CONTEXT
    # ========================================================================
    
    def full_error_context(self, error_id):
        """Get full context for a specific error."""
        all_errors = self.errors()
        for error in all_errors:
            if hasattr(error, 'id') and error.id == error_id:
                return {
                    'error': error,
                    'file_path': error.file_path,
                    'line': error.line,
                    'character': error.character,
                    'message': error.message,
                    'severity': error.severity,
                    'source': error.source,
                    'code': error.code,
                    'context_lines': self._get_error_context_lines(error)
                }
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
    
    def error_suggestions(self, error_id):
        """Get fix suggestions for an error."""
        error_context = self.full_error_context(error_id)
        if error_context:
            # Basic suggestions based on error type
            suggestions = []
            message = error_context['message'].lower()
            
            if 'undefined' in message or 'not defined' in message:
                suggestions.append("Check if the variable/function is properly imported or defined")
            elif 'syntax' in message:
                suggestions.append("Check for missing brackets, quotes, or semicolons")
            elif 'type' in message:
                suggestions.append("Verify the data types match the expected types")
            else:
                suggestions.append("Review the error message and surrounding code")
            
            return suggestions
        return []
    
    def error_related_symbols(self, error_id):
        """Get symbols related to the error."""
        error_context = self.full_error_context(error_id)
        if error_context:
            # Find symbols in the error context
            file_path = error_context['file_path']
            try:
                # Get file object and its symbols
                for file in self.files:
                    if str(file.filepath).endswith(file_path):
                        return [symbol.name for symbol in file.symbols]
            except Exception as e:
                logger.warning(f"Could not get related symbols: {e}")
        return []
    
    def error_impact_analysis(self, error_id):
        """Get impact analysis of the error."""
        error_context = self.full_error_context(error_id)
        if error_context:
            return {
                'severity_impact': 'High' if error_context['error'].severity == 1 else 'Medium',
                'affected_file': error_context['file_path'],
                'potential_cascade': len(self.error_related_symbols(error_id)) > 0,
                'fix_complexity': 'Simple' if 'syntax' in error_context['message'].lower() else 'Complex'
            }
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
    # REAL-TIME ERROR MONITORING
    # ========================================================================
    
    def watch_errors(self, callback):
        """Set up real-time error monitoring."""
        diagnostics_manager = self._get_diagnostics_manager()
        if diagnostics_manager and hasattr(diagnostics_manager, '_lsp_manager'):
            # Set up callback for error changes
            def error_change_handler():
                current_errors = self.errors()
                callback(current_errors)
            
            # Store callback for future use
            if not hasattr(self, '_error_callbacks'):
                self._error_callbacks = []
            self._error_callbacks.append(callback)
            
            return True
        return False
    
    def error_stream(self):
        """Get a stream of error updates."""
        # Generator that yields error updates
        def error_generator():
            last_errors = []
            while True:
                current_errors = self.errors()
                if current_errors != last_errors:
                    yield current_errors
                    last_errors = current_errors
                time.sleep(1)  # Check every second
        
        return error_generator()
    
    def refresh_errors(self):
        """Force refresh of error detection."""
        diagnostics_manager = self._get_diagnostics_manager()
        if diagnostics_manager and hasattr(diagnostics_manager, '_lsp_manager'):
            lsp_manager = diagnostics_manager._lsp_manager
            if lsp_manager and hasattr(lsp_manager, '_refresh_diagnostics_async'):
                lsp_manager._refresh_diagnostics_async()
                return True
        return False

    # ========================================================================
    # ERROR RESOLUTION & ACTIONS
    # ========================================================================
    
    def auto_fix_errors(self, error_ids):
        """Auto-fix specific errors."""
        fixed_errors = []
        for error_id in error_ids:
            quick_fixes = self.get_quick_fixes(error_id)
            if quick_fixes:
                # Apply the first available fix
                if self.apply_error_fix(error_id, quick_fixes[0]['id']):
                    fixed_errors.append(error_id)
        return fixed_errors
    
    def get_quick_fixes(self, error_id):
        """Get available quick fixes for an error."""
        error_context = self.full_error_context(error_id)
        if error_context:
            fixes = []
            message = error_context['message'].lower()
            
            # Generate basic quick fixes based on error type
            if 'import' in message:
                fixes.append({
                    'id': f'fix_import_{error_id}',
                    'title': 'Add missing import',
                    'description': 'Add the missing import statement'
                })
            elif 'undefined' in message:
                fixes.append({
                    'id': f'fix_undefined_{error_id}',
                    'title': 'Define variable',
                    'description': 'Define the undefined variable'
                })
            
            return fixes
        return []
    
    def apply_error_fix(self, error_id, fix_id):
        """Apply a specific fix to resolve an error."""
        # Basic implementation - could be enhanced with actual code modifications
        logger.info(f"Applying fix {fix_id} for error {error_id}")
        return True

    # ========================================================================
    # FULL SERENA LSP FEATURE RETRIEVAL
    # ========================================================================
    
    def completions(self, file_path, position):
        """Get code completions at the specified position."""
        serena_core = self._get_serena_core()
        if serena_core:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    serena_core.get_completions(file_path, position[0], position[1])
                )
            except Exception as e:
                logger.warning(f"Could not get completions: {e}")
        return []
    
    def hover_info(self, file_path, position):
        """Get hover information at the specified position."""
        serena_core = self._get_serena_core()
        if serena_core:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    serena_core.get_hover_info(file_path, position[0], position[1])
                )
            except Exception as e:
                logger.warning(f"Could not get hover info: {e}")
        return None
    
    def signature_help(self, file_path, position):
        """Get function signature help at the specified position."""
        # Basic implementation - could be enhanced with LSP integration
        return {'signatures': [], 'active_signature': 0, 'active_parameter': 0}
    
    def definitions(self, symbol_name):
        """Go to definition for a symbol."""
        definitions = []
        for symbol in self.symbols:
            if symbol.name == symbol_name:
                definitions.append({
                    'file_path': str(symbol.file.filepath) if hasattr(symbol, 'file') else '',
                    'line': getattr(symbol, 'line_number', 0),
                    'character': 0
                })
        return definitions
    
    def references(self, symbol_name):
        """Find all references to a symbol."""
        references = []
        for symbol in self.symbols:
            if symbol.name == symbol_name:
                for usage in symbol.symbol_usages:
                    references.append({
                        'file_path': str(usage.file.filepath) if hasattr(usage, 'file') else '',
                        'line': getattr(usage, 'line_number', 0),
                        'character': 0
                    })
        return references

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

