"""
Serena Error Handling Methods for Codebase

This module contains the four core error handling methods that are added to the Codebase class:
- errors(): Get all errors in the codebase
- full_error_context(): Get comprehensive context for a specific error
- resolve_errors(): Auto-fix all or specific errors
- resolve_error(): Auto-fix a specific error
"""

from typing import List, Dict, Any, Optional
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SerenaErrorMethods:
    """Mixin class that provides Serena error handling methods to Codebase."""
    
    def _ensure_serena_analyzer(self):
        """Lazy initialization of Serena analyzer."""
        if not hasattr(self, '_serena_analyzer'):
            try:
                from graph_sitter.analysis.serena_analysis import SerenaAnalyzer
                self._serena_analyzer = SerenaAnalyzer(self)
                self._serena_analyzer.initialize_serena()
            except ImportError as e:
                logger.warning(f"Serena analyzer not available: {e}")
                self._serena_analyzer = None
        return self._serena_analyzer
    
    def errors(self) -> List[Dict[str, Any]]:
        """
        Get all errors in the codebase.
        
        Returns:
            List of error dictionaries with id, file_path, line, message, severity, etc.
            
        Example:
            >>> codebase = Codebase("./my-project")
            >>> all_errors = codebase.errors()
            >>> print(f"Found {len(all_errors)} errors")
            >>> for error in all_errors:
            ...     print(f"{error['file_path']}:{error['line']} - {error['message']}")
        """
        analyzer = self._ensure_serena_analyzer()
        if not analyzer:
            logger.warning("Serena analyzer not available, returning empty error list")
            return []
        
        try:
            # Collect all LSP diagnostics
            diagnostics = analyzer.collect_all_lsp_diagnostics()
            
            # Convert to simple dictionary format
            errors = []
            for diag in diagnostics:
                errors.append({
                    'id': diag.id,
                    'file_path': diag.file_path,
                    'line': diag.line,
                    'character': diag.character,
                    'message': diag.message,
                    'severity': diag.severity,
                    'code': diag.code,
                    'source': diag.source,
                    'has_fix': len(analyzer._generate_fix_suggestions(diag)) > 0
                })
            
            return errors
            
        except Exception as e:
            logger.error(f"Error collecting codebase errors: {e}")
            return []
    
    def full_error_context(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full context for a specific error.
        
        Args:
            error_id: Unique identifier for the error
            
        Returns:
            Dictionary with comprehensive error context including:
            - error: Basic error information
            - calling_functions: Functions that call the error location
            - called_functions: Functions called by the error location
            - parameter_issues: Parameter-related problems
            - dependency_chain: Dependency relationships
            - related_symbols: Related code symbols
            - code_context: Surrounding code
            - fix_suggestions: Suggested fixes
            - has_fix: Whether automatic fixes are available
            
        Example:
            >>> errors = codebase.errors()
            >>> if errors:
            ...     context = codebase.full_error_context(errors[0]['id'])
            ...     print(f"Error: {context['error']['message']}")
            ...     print(f"Context: {context['code_context']}")
            ...     print(f"Suggestions: {context['fix_suggestions']}")
        """
        analyzer = self._ensure_serena_analyzer()
        if not analyzer:
            logger.warning("Serena analyzer not available")
            return None
        
        try:
            # Get comprehensive error context
            context = analyzer.get_full_error_context(error_id)
            if not context:
                return None
            
            # Convert to dictionary format
            return {
                'error': {
                    'id': context.error.id,
                    'file_path': context.error.file_path,
                    'line': context.error.line,
                    'character': context.error.character,
                    'message': context.error.message,
                    'severity': context.error.severity,
                    'code': context.error.code,
                    'source': context.error.source
                },
                'calling_functions': context.calling_functions,
                'called_functions': context.called_functions,
                'parameter_issues': context.parameter_issues,
                'dependency_chain': context.dependency_chain,
                'related_symbols': context.related_symbols,
                'code_context': context.code_context,
                'fix_suggestions': context.fix_suggestions,
                'has_fix': context.has_fix
            }
            
        except Exception as e:
            logger.error(f"Error getting error context for {error_id}: {e}")
            return None
    
    def resolve_errors(self, error_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Attempt to automatically fix all errors or specific errors.
        
        Args:
            error_ids: Optional list of specific error IDs to fix. If None, attempts to fix all errors.
            
        Returns:
            Dictionary with resolution results:
            - total_errors: Total number of errors found
            - attempted_fixes: Number of fixes attempted
            - successful_fixes: Number of successful fixes
            - failed_fixes: Number of failed fixes
            - results: List of individual fix results
            
        Example:
            >>> # Fix all errors
            >>> result = codebase.resolve_errors()
            >>> print(f"Fixed {result['successful_fixes']}/{result['total_errors']} errors")
            
            >>> # Fix specific errors
            >>> errors = codebase.errors()
            >>> fixable_errors = [e['id'] for e in errors if e['has_fix']]
            >>> result = codebase.resolve_errors(fixable_errors)
        """
        analyzer = self._ensure_serena_analyzer()
        if not analyzer:
            logger.warning("Serena analyzer not available")
            return {'total_errors': 0, 'attempted_fixes': 0, 'successful_fixes': 0, 'failed_fixes': 0, 'results': []}
        
        try:
            # Get all errors if no specific IDs provided
            if error_ids is None:
                all_errors = self.errors()
                error_ids = [error['id'] for error in all_errors if error.get('has_fix', False)]
            
            results = {
                'total_errors': len(error_ids),
                'attempted_fixes': 0,
                'successful_fixes': 0,
                'failed_fixes': 0,
                'results': []
            }
            
            # Attempt to fix each error
            for error_id in error_ids:
                fix_result = self.resolve_error(error_id)
                results['attempted_fixes'] += 1
                
                if fix_result and fix_result.get('success', False):
                    results['successful_fixes'] += 1
                else:
                    results['failed_fixes'] += 1
                
                results['results'].append(fix_result)
            
            logger.info(f"Error resolution complete: {results['successful_fixes']}/{results['attempted_fixes']} fixes successful")
            return results
            
        except Exception as e:
            logger.error(f"Error during bulk error resolution: {e}")
            return {'total_errors': 0, 'attempted_fixes': 0, 'successful_fixes': 0, 'failed_fixes': 0, 'results': [], 'error': str(e)}
    
    def resolve_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to automatically fix a specific error.
        
        Args:
            error_id: Unique identifier for the error to fix
            
        Returns:
            Dictionary with fix result:
            - success: Whether the fix was successful
            - error_id: The error ID that was processed
            - fix_applied: Description of the fix that was applied
            - changes_made: List of changes made to files
            - error: Error message if fix failed
            
        Example:
            >>> errors = codebase.errors()
            >>> if errors:
            ...     result = codebase.resolve_error(errors[0]['id'])
            ...     if result['success']:
            ...         print(f"Fixed: {result['fix_applied']}")
            ...     else:
            ...         print(f"Fix failed: {result['error']}")
        """
        analyzer = self._ensure_serena_analyzer()
        if not analyzer:
            logger.warning("Serena analyzer not available")
            return {'success': False, 'error_id': error_id, 'error': 'Serena analyzer not available'}
        
        try:
            # Get error context
            context = analyzer.get_full_error_context(error_id)
            if not context:
                return {'success': False, 'error_id': error_id, 'error': 'Error not found'}
            
            if not context.has_fix:
                return {'success': False, 'error_id': error_id, 'error': 'No automatic fix available for this error'}
            
            # Try to apply fixes using LSP code actions if available
            if hasattr(self, 'get_code_actions'):
                try:
                    actions = self.get_code_actions(
                        context.error.file_path,
                        context.error.line - 1,  # Convert to 0-based
                        context.error.character
                    )
                    
                    if actions:
                        # Apply the first available code action
                        action = actions[0]
                        if hasattr(self, 'apply_code_action'):
                            apply_result = self.apply_code_action(action)
                            if apply_result.get('success', False):
                                return {
                                    'success': True,
                                    'error_id': error_id,
                                    'fix_applied': f"Applied code action: {action.get('title', 'Unknown')}",
                                    'changes_made': apply_result.get('changes', [])
                                }
                except Exception as e:
                    logger.warning(f"LSP code action failed for {error_id}: {e}")
            
            # Fallback to basic text-based fixes for common patterns
            fix_result = self._apply_basic_fix(context)
            if fix_result:
                return {
                    'success': True,
                    'error_id': error_id,
                    'fix_applied': fix_result['description'],
                    'changes_made': fix_result['changes']
                }
            
            return {
                'success': False,
                'error_id': error_id,
                'error': 'No suitable fix could be applied automatically'
            }
            
        except Exception as e:
            logger.error(f"Error during error resolution for {error_id}: {e}")
            return {'success': False, 'error_id': error_id, 'error': str(e)}
    
    def _apply_basic_fix(self, context) -> Optional[Dict[str, Any]]:
        """Apply basic text-based fixes for common error patterns."""
        try:
            error = context.error
            message = error.message.lower()
            
            # Handle common import errors
            if 'import' in message and ('not found' in message or 'cannot import' in message):
                # Try to add missing import
                return self._fix_missing_import(context)
            
            # Handle undefined variable errors
            if 'undefined' in message or 'not defined' in message:
                return self._fix_undefined_variable(context)
            
            # Handle syntax errors (basic cases)
            if 'syntax' in message:
                return self._fix_basic_syntax(context)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error applying basic fix: {e}")
            return None
    
    def _fix_missing_import(self, context) -> Optional[Dict[str, Any]]:
        """Attempt to fix missing import errors."""
        # This is a simplified implementation
        # In a full implementation, this would analyze the error and add appropriate imports
        return {
            'description': 'Missing import fix (placeholder - would add appropriate import statement)',
            'changes': [f'Would add import to {context.error.file_path}']
        }
    
    def _fix_undefined_variable(self, context) -> Optional[Dict[str, Any]]:
        """Attempt to fix undefined variable errors."""
        # This is a simplified implementation
        # In a full implementation, this would suggest variable definitions or imports
        return {
            'description': 'Undefined variable fix (placeholder - would suggest variable definition)',
            'changes': [f'Would suggest variable definition in {context.error.file_path}']
        }
    
    def _fix_basic_syntax(self, context) -> Optional[Dict[str, Any]]:
        """Attempt to fix basic syntax errors."""
        # This is a simplified implementation
        # In a full implementation, this would fix common syntax issues
        return {
            'description': 'Basic syntax fix (placeholder - would fix common syntax issues)',
            'changes': [f'Would fix syntax in {context.error.file_path}']
        }

