"""
Rename Refactor

Provides safe symbol renaming across all files with conflict detection.
"""

from typing import Dict, List, Optional, Any
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from ..serena_types import RefactoringResult, RefactoringType, RefactoringChange, RefactoringConflict

logger = get_logger(__name__)


class RenameRefactor:
    """Handles symbol renaming operations."""
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge, config):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
        self.config = config
    
    def rename_symbol(self, file_path: str, line: int, character: int, new_name: str, preview: bool = False) -> RefactoringResult:
        """Rename a symbol and all its references."""
        try:
            # Get the file from the codebase
            file = self.codebase.get_file(file_path, optional=True)
            if not file:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=[],
                    warnings=[],
                    preview_available=preview,
                    message=f"File not found: {file_path}"
                )
            
            # Find the symbol at the specified position
            symbol = self._find_symbol_at_position(file, line, character)
            if not symbol:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=[],
                    warnings=[],
                    preview_available=preview,
                    message="No symbol found at the specified position"
                )
            
            # Check for conflicts
            conflicts = self._check_rename_conflicts(symbol, new_name)
            warnings = self._check_rename_warnings(symbol, new_name)
            
            if conflicts and not preview:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=conflicts,
                    warnings=warnings,
                    preview_available=preview,
                    message=f"Rename conflicts detected for '{new_name}'"
                )
            
            # Collect all changes that would be made
            changes = []
            
            # Add change for the symbol definition
            changes.append({
                'type': 'rename_definition',
                'file': file_path,
                'line': symbol.line_number,
                'character': symbol.column_number,
                'old_name': symbol.name,
                'new_name': new_name,
                'length': len(symbol.name)
            })
            
            # Add changes for all usages
            try:
                usages = symbol.usages()
                for usage in usages:
                    usage_symbol = usage.usage_symbol
                    changes.append({
                        'type': 'rename_usage',
                        'file': usage_symbol.filepath,
                        'line': usage_symbol.line_number,
                        'character': usage_symbol.column_number,
                        'old_name': symbol.name,
                        'new_name': new_name,
                        'length': len(symbol.name)
                    })
            except Exception as e:
                logger.warning(f"Error getting symbol usages: {e}")
                warnings.append(f"Could not find all usages: {e}")
            
            # If not preview, apply the changes
            if not preview:
                try:
                    # Use graph-sitter's built-in rename functionality
                    old_name = symbol.name
                    symbol.rename(new_name)
                    self.codebase.commit()
                    
                    logger.info(f"Successfully renamed symbol '{old_name}' to '{new_name}'")
                    
                except Exception as e:
                    logger.error(f"Error applying rename: {e}")
                    return RefactoringResult(
                        success=False,
                        refactoring_type=RefactoringType.RENAME,
                        changes=changes,
                        conflicts=conflicts,
                        warnings=warnings,
                        preview_available=preview,
                        message=f"Failed to apply rename: {e}"
                    )
            
            return RefactoringResult(
                success=True,
                refactoring_type=RefactoringType.RENAME,
                changes=changes,
                conflicts=conflicts,
                warnings=warnings,
                preview_available=preview,
                message=f"{'Preview: ' if preview else ''}Renamed symbol '{symbol.name}' to '{new_name}' ({len(changes)} changes)"
            )
            
        except Exception as e:
            logger.error(f"Error renaming symbol: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.RENAME,
                changes=[],
                conflicts=[],
                warnings=[],
                preview_available=preview,
                message=f"Failed to rename symbol: {e}"
            )
    
    def _find_symbol_at_position(self, file, line: int, character: int):
        """Find symbol at the specified position in the file."""
        try:
            # Use graph-sitter's existing capabilities to find symbols
            for symbol in file.symbols:
                if hasattr(symbol, 'line_number') and hasattr(symbol, 'column_number'):
                    if symbol.line_number == line:
                        return symbol
                # Check if position is within symbol range
                if (hasattr(symbol, 'start_line') and hasattr(symbol, 'end_line') and
                    symbol.start_line <= line <= symbol.end_line):
                    return symbol
            return None
        except Exception as e:
            logger.debug(f"Error finding symbol at position: {e}")
            return None
    
    def _check_rename_conflicts(self, symbol, new_name: str) -> List[RefactoringConflict]:
        """Check for potential conflicts when renaming a symbol."""
        conflicts = []
        
        try:
            # Check if new name already exists in the same scope
            file = symbol.file
            for existing_symbol in file.symbols:
                if existing_symbol.name == new_name and existing_symbol != symbol:
                    conflicts.append(RefactoringConflict(
                        conflict_type="name_collision",
                        description=f"Symbol '{new_name}' already exists in {file.filepath}",
                        file_path=file.filepath,
                        line_number=existing_symbol.line_number,
                        severity="error"
                    ))
            
            # Check for reserved keywords
            reserved_keywords = ['def', 'class', 'if', 'else', 'for', 'while', 'import', 'from', 'return', 'try', 'except']
            if new_name in reserved_keywords:
                conflicts.append(RefactoringConflict(
                    conflict_type="reserved_keyword",
                    description=f"'{new_name}' is a reserved keyword",
                    file_path=symbol.filepath,
                    line_number=symbol.line_number,
                    severity="error"
                ))
            
            # Check naming conventions
            if not new_name.isidentifier():
                conflicts.append(RefactoringConflict(
                    conflict_type="invalid_identifier",
                    description=f"'{new_name}' is not a valid identifier",
                    file_path=symbol.filepath,
                    line_number=symbol.line_number,
                    severity="error"
                ))
                
        except Exception as e:
            logger.warning(f"Error checking rename conflicts: {e}")
        
        return conflicts
    
    def _check_rename_warnings(self, symbol, new_name: str) -> List[str]:
        """Check for potential warnings when renaming a symbol."""
        warnings = []
        
        try:
            # Check naming conventions
            if hasattr(symbol, 'symbol_type'):
                symbol_type = str(symbol.symbol_type).lower()
                
                if 'class' in symbol_type:
                    if not new_name[0].isupper():
                        warnings.append(f"Class names should start with uppercase: '{new_name}'")
                elif 'function' in symbol_type:
                    if not new_name.islower() and '_' not in new_name:
                        warnings.append(f"Function names should be lowercase with underscores: '{new_name}'")
                elif 'constant' in symbol_type:
                    if not new_name.isupper():
                        warnings.append(f"Constants should be uppercase: '{new_name}'")
            
            # Check for potential confusion with built-ins
            builtins = ['list', 'dict', 'str', 'int', 'float', 'bool', 'set', 'tuple']
            if new_name in builtins:
                warnings.append(f"'{new_name}' shadows a built-in type")
                
        except Exception as e:
            logger.debug(f"Error checking rename warnings: {e}")
        
        return warnings

    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        return {'initialized': True}
    
    def shutdown(self) -> None:
        """Shutdown the rename refactor."""
        pass
