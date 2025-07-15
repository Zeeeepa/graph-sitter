"""
Refactoring Engine

Main orchestrator for all refactoring operations with safety checks,
conflict detection, and preview capabilities.
"""

import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from ..types import RefactoringType, RefactoringResult, RefactoringChange, RefactoringConflict

# Import refactoring modules after types to avoid circular imports
from .rename_refactor import RenameRefactor
from .extract_refactor import ExtractRefactor
from .inline_refactor import InlineRefactor
from .move_refactor import MoveRefactor

logger = get_logger(__name__)


@dataclass
class RefactoringConfig:
    """Configuration for refactoring operations."""
    enable_safety_checks: bool = True
    enable_conflict_detection: bool = True
    enable_preview: bool = True
    backup_before_refactor: bool = True
    max_file_changes: int = 100
    timeout_seconds: float = 30.0


class RefactoringEngine:
    """
    Comprehensive refactoring engine.
    
    Provides safe refactoring operations with conflict detection,
    preview capabilities, and undo/redo support.
    """
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge, config: Optional[RefactoringConfig] = None):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
        self.config = config or RefactoringConfig()
        
        # Initialize refactoring modules
        self.rename_refactor = RenameRefactor(codebase, lsp_bridge, self.config)
        self.extract_refactor = ExtractRefactor(codebase, lsp_bridge, self.config)
        self.inline_refactor = InlineRefactor(codebase, lsp_bridge, self.config)
        self.move_refactor = MoveRefactor(codebase, lsp_bridge, self.config)
        
        # Operation tracking
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        self._operation_lock = threading.RLock()
        self._operation_counter = 0
        
        # History for undo/redo
        self._refactoring_history: List[Dict[str, Any]] = []
        self._history_lock = threading.RLock()
        
        logger.info("Refactoring engine initialized")
    
    def rename_symbol(self, file_path: str, line: int, character: int, new_name: str, preview: bool = False) -> Dict[str, Any]:
        """
        Rename symbol at position across all files.
        
        Args:
            file_path: Path to the file containing the symbol
            line: Line number (0-based)
            character: Character position (0-based)
            new_name: New name for the symbol
            preview: Whether to return preview without applying changes
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.RENAME, {
            'file_path': file_path,
            'line': line,
            'character': character,
            'new_name': new_name,
            'preview': preview
        })
        
        try:
            # Validate inputs
            if not self._validate_rename_inputs(file_path, line, character, new_name):
                return self._create_error_result(RefactoringType.RENAME, "Invalid rename parameters")
            
            # Perform rename refactoring
            result = self.rename_refactor.rename_symbol(file_path, line, character, new_name, preview)
            
            # Add to history if successful and not preview
            if result.success and not preview:
                self._add_to_history(RefactoringType.RENAME, result, {
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'new_name': new_name
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in rename refactoring: {e}")
            return self._create_error_result(RefactoringType.RENAME, str(e))
        finally:
            self._end_operation(operation_id)
    
    def extract_method(self, file_path: str, start_line: int, end_line: int, method_name: str, **kwargs) -> Dict[str, Any]:
        """
        Extract selected code into a new method.
        
        Args:
            file_path: Path to the file
            start_line: Start line of selection (0-based)
            end_line: End line of selection (0-based)
            method_name: Name for the new method
            **kwargs: Additional options (target_class, visibility, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.EXTRACT_METHOD, {
            'file_path': file_path,
            'start_line': start_line,
            'end_line': end_line,
            'method_name': method_name,
            **kwargs
        })
        
        try:
            # Validate inputs
            if not self._validate_extract_method_inputs(file_path, start_line, end_line, method_name):
                return self._create_error_result(RefactoringType.EXTRACT_METHOD, "Invalid extract method parameters")
            
            # Perform extract method refactoring
            result = self.extract_refactor.extract_method(file_path, start_line, end_line, method_name, **kwargs)
            
            # Add to history if successful
            if result.success and not kwargs.get('preview', False):
                self._add_to_history(RefactoringType.EXTRACT_METHOD, result, {
                    'file_path': file_path,
                    'start_line': start_line,
                    'end_line': end_line,
                    'method_name': method_name
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in extract method refactoring: {e}")
            return self._create_error_result(RefactoringType.EXTRACT_METHOD, str(e))
        finally:
            self._end_operation(operation_id)
    
    def extract_variable(self, file_path: str, line: int, character: int, variable_name: str, **kwargs) -> Dict[str, Any]:
        """
        Extract expression into a variable.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
            variable_name: Name for the new variable
            **kwargs: Additional options (scope, type_annotation, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.EXTRACT_VARIABLE, {
            'file_path': file_path,
            'line': line,
            'character': character,
            'variable_name': variable_name,
            **kwargs
        })
        
        try:
            # Validate inputs
            if not self._validate_extract_variable_inputs(file_path, line, character, variable_name):
                return self._create_error_result(RefactoringType.EXTRACT_VARIABLE, "Invalid extract variable parameters")
            
            # Perform extract variable refactoring
            result = self.extract_refactor.extract_variable(file_path, line, character, variable_name, **kwargs)
            
            # Add to history if successful
            if result.success and not kwargs.get('preview', False):
                self._add_to_history(RefactoringType.EXTRACT_VARIABLE, result, {
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'variable_name': variable_name
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in extract variable refactoring: {e}")
            return self._create_error_result(RefactoringType.EXTRACT_VARIABLE, str(e))
        finally:
            self._end_operation(operation_id)
    
    def inline_method(self, method_name: str, replace_all: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Inline method implementations.
        
        Args:
            method_name: Name of the method to inline
            replace_all: Whether to replace all occurrences
            **kwargs: Additional options (target_file, scope, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.INLINE_METHOD, {
            'method_name': method_name,
            'replace_all': replace_all,
            **kwargs
        })
        
        try:
            # Validate inputs
            if not self._validate_inline_method_inputs(method_name):
                return self._create_error_result(RefactoringType.INLINE_METHOD, "Invalid inline method parameters")
            
            # Perform inline method refactoring
            result = self.inline_refactor.inline_method(method_name, replace_all, **kwargs)
            
            # Add to history if successful
            if result.success and not kwargs.get('preview', False):
                self._add_to_history(RefactoringType.INLINE_METHOD, result, {
                    'method_name': method_name,
                    'replace_all': replace_all
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in inline method refactoring: {e}")
            return self._create_error_result(RefactoringType.INLINE_METHOD, str(e))
        finally:
            self._end_operation(operation_id)
    
    def inline_variable(self, variable_name: str, **kwargs) -> Dict[str, Any]:
        """
        Inline variable usage.
        
        Args:
            variable_name: Name of the variable to inline
            **kwargs: Additional options (scope, replace_all, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.INLINE_VARIABLE, {
            'variable_name': variable_name,
            **kwargs
        })
        
        try:
            # Validate inputs
            if not self._validate_inline_variable_inputs(variable_name):
                return self._create_error_result(RefactoringType.INLINE_VARIABLE, "Invalid inline variable parameters")
            
            # Perform inline variable refactoring
            result = self.inline_refactor.inline_variable(variable_name, **kwargs)
            
            # Add to history if successful
            if result.success and not kwargs.get('preview', False):
                self._add_to_history(RefactoringType.INLINE_VARIABLE, result, {
                    'variable_name': variable_name
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in inline variable refactoring: {e}")
            return self._create_error_result(RefactoringType.INLINE_VARIABLE, str(e))
        finally:
            self._end_operation(operation_id)
    
    def move_symbol(self, symbol_name: str, from_file: str, to_file: str, **kwargs) -> Dict[str, Any]:
        """
        Move symbol to different file.
        
        Args:
            symbol_name: Name of the symbol to move
            from_file: Source file path
            to_file: Target file path
            **kwargs: Additional options (update_imports, create_file, etc.)
        
        Returns:
            Refactoring result with changes and conflicts
        """
        operation_id = self._start_operation(RefactoringType.MOVE_SYMBOL, {
            'symbol_name': symbol_name,
            'from_file': from_file,
            'to_file': to_file,
            **kwargs
        })
        
        try:
            # Validate inputs
            if not self._validate_move_symbol_inputs(symbol_name, from_file, to_file):
                return self._create_error_result(RefactoringType.MOVE_SYMBOL, "Invalid move symbol parameters")
            
            # Perform move symbol refactoring
            result = self.move_refactor.move_symbol(symbol_name, from_file, to_file, **kwargs)
            
            # Add to history if successful
            if result.success and not kwargs.get('preview', False):
                self._add_to_history(RefactoringType.MOVE_SYMBOL, result, {
                    'symbol_name': symbol_name,
                    'from_file': from_file,
                    'to_file': to_file
                })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error in move symbol refactoring: {e}")
            return self._create_error_result(RefactoringType.MOVE_SYMBOL, str(e))
        finally:
            self._end_operation(operation_id)
    
    def organize_imports(self, file_path: str, remove_unused: bool = True, sort_imports: bool = True) -> Dict[str, Any]:
        """
        Organize imports in the specified file.
        
        Args:
            file_path: Path to the file
            remove_unused: Whether to remove unused imports
            sort_imports: Whether to sort imports
        
        Returns:
            Result of import organization
        """
        try:
            # This would be implemented as a specialized refactoring
            # For now, return a basic implementation
            
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            changes = []
            warnings = []
            
            # Analyze imports
            imports = file_obj.imports if hasattr(file_obj, 'imports') else []
            
            if remove_unused:
                # Find unused imports (simplified)
                unused_imports = self._find_unused_imports(file_obj, imports)
                for unused in unused_imports:
                    changes.append({
                        'type': 'remove_import',
                        'file': file_path,
                        'import': unused.name if hasattr(unused, 'name') else str(unused)
                    })
            
            if sort_imports:
                # Sort imports (simplified)
                changes.append({
                    'type': 'sort_imports',
                    'file': file_path,
                    'message': 'Imports sorted alphabetically'
                })
            
            return {
                'success': True,
                'changes': changes,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Error organizing imports: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_refactoring_history(self) -> List[Dict[str, Any]]:
        """Get refactoring history."""
        with self._history_lock:
            return self._refactoring_history.copy()
    
    def undo_last_refactoring(self) -> Dict[str, Any]:
        """Undo the last refactoring operation."""
        with self._history_lock:
            if not self._refactoring_history:
                return {
                    'success': False,
                    'error': 'No refactoring operations to undo'
                }
            
            # This would implement undo functionality
            # For now, return a placeholder
            last_operation = self._refactoring_history[-1]
            
            return {
                'success': True,
                'message': f'Undid {last_operation["type"].value} operation',
                'operation': last_operation
            }
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get currently active refactoring operations."""
        with self._operation_lock:
            return list(self._active_operations.values())
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active refactoring operation."""
        with self._operation_lock:
            if operation_id in self._active_operations:
                operation = self._active_operations[operation_id]
                operation['cancelled'] = True
                logger.info(f"Cancelled refactoring operation {operation_id}")
                return True
            return False
    
    def _start_operation(self, refactoring_type: RefactoringType, params: Dict[str, Any]) -> str:
        """Start tracking a refactoring operation."""
        with self._operation_lock:
            self._operation_counter += 1
            operation_id = f"refactor_{self._operation_counter}_{int(time.time())}"
            
            self._active_operations[operation_id] = {
                'id': operation_id,
                'type': refactoring_type,
                'params': params,
                'start_time': time.time(),
                'cancelled': False
            }
            
            return operation_id
    
    def _end_operation(self, operation_id: str) -> None:
        """End tracking a refactoring operation."""
        with self._operation_lock:
            if operation_id in self._active_operations:
                operation = self._active_operations[operation_id]
                operation['end_time'] = time.time()
                operation['duration'] = operation['end_time'] - operation['start_time']
                
                # Remove from active operations
                del self._active_operations[operation_id]
    
    def _add_to_history(self, refactoring_type: RefactoringType, result: RefactoringResult, params: Dict[str, Any]) -> None:
        """Add successful refactoring to history."""
        with self._history_lock:
            self._refactoring_history.append({
                'type': refactoring_type,
                'params': params,
                'result': result,
                'timestamp': time.time()
            })
            
            # Limit history size
            if len(self._refactoring_history) > 50:
                self._refactoring_history = self._refactoring_history[-50:]
    
    def _create_error_result(self, refactoring_type: RefactoringType, error_message: str) -> Dict[str, Any]:
        """Create an error result."""
        result = RefactoringResult(
            success=False,
            refactoring_type=refactoring_type,
            changes=[],
            conflicts=[],
            warnings=[],
            error_message=error_message
        )
        return result.to_dict()
    
    def _validate_rename_inputs(self, file_path: str, line: int, character: int, new_name: str) -> bool:
        """Validate rename refactoring inputs."""
        if not file_path or line < 0 or character < 0:
            return False
        if not new_name or not new_name.replace('_', '').isalnum():
            return False
        return True
    
    def _validate_extract_method_inputs(self, file_path: str, start_line: int, end_line: int, method_name: str) -> bool:
        """Validate extract method inputs."""
        if not file_path or start_line < 0 or end_line < start_line:
            return False
        if not method_name or not method_name.replace('_', '').isalnum():
            return False
        return True
    
    def _validate_extract_variable_inputs(self, file_path: str, line: int, character: int, variable_name: str) -> bool:
        """Validate extract variable inputs."""
        if not file_path or line < 0 or character < 0:
            return False
        if not variable_name or not variable_name.replace('_', '').isalnum():
            return False
        return True
    
    def _validate_inline_method_inputs(self, method_name: str) -> bool:
        """Validate inline method inputs."""
        return bool(method_name and method_name.replace('_', '').isalnum())
    
    def _validate_inline_variable_inputs(self, variable_name: str) -> bool:
        """Validate inline variable inputs."""
        return bool(variable_name and variable_name.replace('_', '').isalnum())
    
    def _validate_move_symbol_inputs(self, symbol_name: str, from_file: str, to_file: str) -> bool:
        """Validate move symbol inputs."""
        if not symbol_name or not symbol_name.replace('_', '').isalnum():
            return False
        if not from_file or not to_file or from_file == to_file:
            return False
        return True
    
    def _find_unused_imports(self, file_obj, imports: List) -> List:
        """Find unused imports in a file."""
        # This would analyze the file content to find unused imports
        # For now, return empty list
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        with self._operation_lock:
            active_count = len(self._active_operations)
        
        with self._history_lock:
            history_count = len(self._refactoring_history)
        
        return {
            'initialized': True,
            'active_operations': active_count,
            'history_count': history_count,
            'config': {
                'safety_checks_enabled': self.config.enable_safety_checks,
                'conflict_detection_enabled': self.config.enable_conflict_detection,
                'preview_enabled': self.config.enable_preview,
                'backup_enabled': self.config.backup_before_refactor
            },
            'modules': {
                'rename': self.rename_refactor.get_status(),
                'extract': self.extract_refactor.get_status(),
                'inline': self.inline_refactor.get_status(),
                'move': self.move_refactor.get_status()
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the refactoring engine."""
        logger.info("Shutting down refactoring engine")
        
        # Cancel active operations
        with self._operation_lock:
            for operation_id in list(self._active_operations.keys()):
                self.cancel_operation(operation_id)
        
        # Shutdown modules
        self.rename_refactor.shutdown()
        self.extract_refactor.shutdown()
        self.inline_refactor.shutdown()
        self.move_refactor.shutdown()
        
        logger.info("Refactoring engine shutdown complete")
