"""
Error Resolution System

This module provides automatic error resolution capabilities,
applying fixes for common error patterns and integrating with
existing Serena refactoring capabilities.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger
from .unified_error_models import (
    UnifiedError, ErrorFix, FixConfidence, ErrorResolutionResult
)

logger = get_logger(__name__)


class FixApplicator:
    """Applies fixes to source code files."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self._backup_files: Dict[str, str] = {}
    
    def apply_fix(self, fix: ErrorFix, error: UnifiedError) -> ErrorResolutionResult:
        """
        Apply a single fix to resolve an error.
        
        Args:
            fix: The fix to apply
            error: The error being fixed
            
        Returns:
            Result of the fix application
        """
        try:
            # Create backup before applying fix
            self._create_backup(error.location.file_path)
            
            success = False
            applied_changes = []
            
            for change in fix.changes:
                change_result = self._apply_change(change, error)
                if change_result:
                    applied_changes.append(change['type'])
                    success = True
                else:
                    success = False
                    break
            
            if success:
                return ErrorResolutionResult(
                    error_id=error.id,
                    success=True,
                    message=f"Successfully applied fix: {fix.title}",
                    applied_fixes=[fix.id],
                    files_modified=[error.location.file_path]
                )
            else:
                # Restore backup on failure
                self._restore_backup(error.location.file_path)
                return ErrorResolutionResult(
                    error_id=error.id,
                    success=False,
                    message=f"Failed to apply fix: {fix.title}",
                    remaining_issues=[f"Could not apply change: {change['type']}"]
                )
                
        except Exception as e:
            logger.error(f"Error applying fix {fix.id}: {e}")
            self._restore_backup(error.location.file_path)
            return ErrorResolutionResult(
                error_id=error.id,
                success=False,
                message=f"Exception while applying fix: {str(e)}"
            )
    
    def _create_backup(self, file_path: str) -> None:
        """Create backup of file before modification."""
        try:
            full_path = Path(file_path)
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    self._backup_files[file_path] = f.read()
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
    
    def _restore_backup(self, file_path: str) -> None:
        """Restore file from backup."""
        try:
            if file_path in self._backup_files:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._backup_files[file_path])
                del self._backup_files[file_path]
        except Exception as e:
            logger.error(f"Error restoring backup for {file_path}: {e}")
    
    def _apply_change(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Apply a specific change to a file."""
        change_type = change.get('type')
        
        if change_type == 'delete_line':
            return self._delete_line(change, error)
        elif change_type == 'add_import':
            return self._add_import(change, error)
        elif change_type == 'fix_whitespace':
            return self._fix_whitespace(change, error)
        elif change_type == 'replace_text':
            return self._replace_text(change, error)
        elif change_type == 'add_return':
            return self._add_return(change, error)
        elif change_type == 'fix_arguments':
            return self._fix_arguments(change, error)
        else:
            logger.warning(f"Unknown change type: {change_type}")
            return False
    
    def _delete_line(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Delete a specific line from the file."""
        try:
            file_path = change.get('file', error.location.file_path)
            line_number = change.get('line', error.location.line)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if 1 <= line_number <= len(lines):
                # Remove the line (convert to 0-based index)
                del lines[line_number - 1]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting line: {e}")
            return False
    
    def _add_import(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Add an import statement to the file."""
        try:
            file_path = change.get('file', error.location.file_path)
            symbol = change.get('symbol')
            
            if not symbol:
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to find the best place to add the import
            tree = ast.parse(content)
            
            # Find existing imports
            import_line = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_line = max(import_line, node.lineno)
            
            # Generate import statement
            # This is a simplified version - in practice, you'd want more sophisticated logic
            import_statement = f"from {self._guess_module(symbol)} import {symbol}\n"
            
            lines = content.split('\n')
            lines.insert(import_line, import_statement)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding import: {e}")
            return False
    
    def _fix_whitespace(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Fix whitespace issues."""
        try:
            file_path = change.get('file', error.location.file_path)
            line_number = change.get('line', error.location.line)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if 1 <= line_number <= len(lines):
                line_index = line_number - 1
                
                # Common whitespace fixes
                if "expected 2 blank lines" in error.message.lower():
                    # Add blank lines before the current line
                    lines.insert(line_index, '\n')
                    lines.insert(line_index, '\n')
                elif "missing whitespace" in error.message.lower():
                    # Fix common missing whitespace issues
                    line = lines[line_index]
                    # Add space around operators
                    line = re.sub(r'([^=!<>])=([^=])', r'\1 = \2', line)
                    line = re.sub(r'([^=!<>])==([^=])', r'\1 == \2', line)
                    lines[line_index] = line
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error fixing whitespace: {e}")
            return False
    
    def _replace_text(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Replace text in the file."""
        try:
            file_path = change.get('file', error.location.file_path)
            old_text = change.get('old_text')
            new_text = change.get('new_text')
            line_number = change.get('line', error.location.line)
            
            if not old_text or new_text is None:
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if 1 <= line_number <= len(lines):
                line_index = line_number - 1
                lines[line_index] = lines[line_index].replace(old_text, new_text)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error replacing text: {e}")
            return False
    
    def _add_return(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Add a return statement to a function."""
        try:
            file_path = change.get('file', error.location.file_path)
            function_name = change.get('function')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find the function
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Find the end of the function and add return statement
                    lines = content.split('\n')
                    
                    # Simple heuristic: add return None at the end of the function
                    # This would need more sophisticated logic in practice
                    function_end = getattr(node, 'end_lineno', node.lineno + 10)
                    
                    # Find the last non-empty line in the function
                    for i in range(function_end - 1, node.lineno - 1, -1):
                        if i < len(lines) and lines[i].strip():
                            # Add return statement after this line
                            indent = len(lines[i]) - len(lines[i].lstrip())
                            lines.insert(i + 1, ' ' * (indent + 4) + 'return None')
                            break
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding return statement: {e}")
            return False
    
    def _fix_arguments(self, change: Dict[str, Any], error: UnifiedError) -> bool:
        """Fix function call arguments."""
        try:
            file_path = change.get('file', error.location.file_path)
            line_number = change.get('line', error.location.line)
            function_name = change.get('function')
            
            # This would require sophisticated analysis of the function signature
            # and the current call. For now, just return False to indicate
            # this fix type needs manual intervention.
            logger.info(f"Argument fixing for {function_name} requires manual intervention")
            return False
            
        except Exception as e:
            logger.error(f"Error fixing arguments: {e}")
            return False
    
    def _guess_module(self, symbol: str) -> str:
        """Guess the module name for a symbol (simplified)."""
        # This is a very simplified version
        # In practice, you'd want a more sophisticated module resolution system
        common_modules = {
            'os': 'os',
            'sys': 'sys',
            'json': 'json',
            'Path': 'pathlib',
            'datetime': 'datetime',
            'List': 'typing',
            'Dict': 'typing',
            'Optional': 'typing',
        }
        
        return common_modules.get(symbol, 'unknown_module')


class ErrorResolver:
    """
    Main error resolution system that coordinates fix application
    and integrates with existing Serena refactoring capabilities.
    """
    
    def __init__(self, codebase, error_manager, context_engine):
        self.codebase = codebase
        self.error_manager = error_manager
        self.context_engine = context_engine
        self.fix_applicator = FixApplicator(codebase)
        
        # Statistics
        self.resolution_stats = {
            'total_attempts': 0,
            'successful_fixes': 0,
            'failed_fixes': 0,
            'by_fix_type': defaultdict(int),
            'by_error_category': defaultdict(int)
        }
    
    def resolve_error(self, error_id: str) -> ErrorResolutionResult:
        """
        Resolve a specific error by ID.
        
        Args:
            error_id: ID of the error to resolve
            
        Returns:
            Result of the resolution attempt
        """
        error = self.error_manager.get_error_by_id(error_id)
        if not error:
            return ErrorResolutionResult(
                error_id=error_id,
                success=False,
                message=f"Error {error_id} not found"
            )
        
        return self._resolve_single_error(error)
    
    def resolve_errors(self, error_ids: Optional[List[str]] = None) -> List[ErrorResolutionResult]:
        """
        Resolve multiple errors.
        
        Args:
            error_ids: List of error IDs to resolve, or None for all auto-fixable errors
            
        Returns:
            List of resolution results
        """
        if error_ids is None:
            # Get all auto-fixable errors
            all_errors = self.error_manager.get_all_errors()
            errors_to_fix = [e for e in all_errors if e.auto_fixable]
        else:
            errors_to_fix = []
            for error_id in error_ids:
                error = self.error_manager.get_error_by_id(error_id)
                if error:
                    errors_to_fix.append(error)
        
        results = []
        for error in errors_to_fix:
            result = self._resolve_single_error(error)
            results.append(result)
        
        return results
    
    def _resolve_single_error(self, error: UnifiedError) -> ErrorResolutionResult:
        """Resolve a single error."""
        self.resolution_stats['total_attempts'] += 1
        self.resolution_stats['by_error_category'][error.category.value] += 1
        
        try:
            # Get full context for the error
            context = self.context_engine.get_full_error_context(error)
            
            # Find the best fix to apply
            best_fix = self._select_best_fix(error, context)
            
            if not best_fix:
                return ErrorResolutionResult(
                    error_id=error.id,
                    success=False,
                    message="No suitable fix found for this error"
                )
            
            # Check if fix requires user input
            if best_fix.requires_user_input:
                return ErrorResolutionResult(
                    error_id=error.id,
                    success=False,
                    message=f"Fix '{best_fix.title}' requires user input",
                    remaining_issues=["User input required"]
                )
            
            # Apply the fix
            result = self.fix_applicator.apply_fix(best_fix, error)
            
            # Update statistics
            if result.success:
                self.resolution_stats['successful_fixes'] += 1
            else:
                self.resolution_stats['failed_fixes'] += 1
            
            self.resolution_stats['by_fix_type'][best_fix.title] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving {error.id}: {e}")
            self.resolution_stats['failed_fixes'] += 1
            
            return ErrorResolutionResult(
                error_id=error.id,
                success=False,
                message=f"Exception during resolution: {str(e)}"
            )
    
    def _select_best_fix(self, error: UnifiedError, context) -> Optional[ErrorFix]:
        """Select the best fix for an error based on context."""
        available_fixes = context.recommended_fixes or error.fixes
        
        if not available_fixes:
            return None
        
        # Sort fixes by confidence and priority
        def fix_score(fix: ErrorFix) -> int:
            score = 0
            
            # Confidence scoring
            if fix.confidence == FixConfidence.HIGH:
                score += 100
            elif fix.confidence == FixConfidence.MEDIUM:
                score += 50
            elif fix.confidence == FixConfidence.LOW:
                score += 10
            
            # Prefer fixes that don't require user input
            if not fix.requires_user_input:
                score += 20
            
            # Prefer fixes with lower estimated impact
            if fix.estimated_impact == "low":
                score += 10
            elif fix.estimated_impact == "medium":
                score += 5
            
            return score
        
        # Select the highest scoring fix
        best_fix = max(available_fixes, key=fix_score)
        
        # Only return fixes with reasonable confidence
        if best_fix.confidence in [FixConfidence.HIGH, FixConfidence.MEDIUM]:
            return best_fix
        
        return None
    
    def get_resolution_stats(self) -> Dict[str, Any]:
        """Get resolution statistics."""
        stats = dict(self.resolution_stats)
        stats['success_rate'] = (
            self.resolution_stats['successful_fixes'] / 
            max(self.resolution_stats['total_attempts'], 1)
        )
        return stats
    
    def can_resolve_error(self, error: UnifiedError) -> bool:
        """Check if an error can be automatically resolved."""
        return error.auto_fixable and any(
            fix.confidence in [FixConfidence.HIGH, FixConfidence.MEDIUM] 
            and not fix.requires_user_input
            for fix in error.fixes
        )
    
    def preview_resolution(self, error_id: str) -> Dict[str, Any]:
        """Preview what would happen if we tried to resolve an error."""
        error = self.error_manager.get_error_by_id(error_id)
        if not error:
            return {'error': f'Error {error_id} not found'}
        
        context = self.context_engine.get_full_error_context(error)
        best_fix = self._select_best_fix(error, context)
        
        if not best_fix:
            return {
                'can_resolve': False,
                'reason': 'No suitable fix found'
            }
        
        return {
            'can_resolve': True,
            'fix_title': best_fix.title,
            'fix_description': best_fix.description,
            'confidence': best_fix.confidence.value,
            'requires_user_input': best_fix.requires_user_input,
            'estimated_impact': best_fix.estimated_impact,
            'changes': best_fix.changes
        }

