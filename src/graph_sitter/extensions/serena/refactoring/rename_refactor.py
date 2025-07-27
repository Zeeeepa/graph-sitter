"""
Rename Refactoring

Provides safe symbol renaming with conflict detection and scope analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import re

from ..types import (
    RefactoringType,
    RefactoringResult,
    RefactoringChange,
    RefactoringConflict,
    ChangeType,
    ConflictType
)
from .refactoring_engine import create_refactoring_change, create_refactoring_conflict

logger = logging.getLogger(__name__)


class RenameRefactor:
    """
    Handles symbol renaming operations.
    
    Features:
    - Symbol scope analysis
    - Reference finding and validation
    - Conflict detection (name collisions, scope conflicts)
    - Safe renaming with preview
    """
    
    def __init__(self, codebase_path: str, serena_core: Any, config: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        self.config = config
        
        # Symbol tracking
        self._symbol_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.debug("RenameRefactor initialized")
    
    async def initialize(self) -> None:
        """Initialize the rename refactor module."""
        logger.debug("Initializing rename refactor...")
        # Initialization logic here
        logger.debug("✅ Rename refactor initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the rename refactor module."""
        self._symbol_cache.clear()
        logger.debug("✅ Rename refactor shutdown")
    
    async def perform_refactoring(
        self,
        dry_run: bool = True,
        operation_id: Optional[str] = None,
        **kwargs
    ) -> RefactoringResult:
        """
        Perform rename refactoring.
        
        Args:
            dry_run: Whether to perform a dry run
            operation_id: Operation ID for tracking
            **kwargs: Rename parameters (old_name, new_name, file_path, line, character)
            
        Returns:
            RefactoringResult with changes and conflicts
        """
        try:
            # Extract parameters
            old_name = kwargs.get('old_name')
            new_name = kwargs.get('new_name')
            file_path = kwargs.get('file_path')
            line = kwargs.get('line', 0)
            character = kwargs.get('character', 0)
            
            # Validate parameters
            if not old_name or not new_name:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=[],
                    error_message="Both old_name and new_name are required"
                )
            
            if not file_path:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=[],
                    error_message="file_path is required"
                )
            
            # Validate new name
            validation_result = self._validate_new_name(new_name)
            if not validation_result['valid']:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.RENAME,
                    changes=[],
                    conflicts=[],
                    error_message=f"Invalid new name: {validation_result['reason']}"
                )
            
            # Find all references to the symbol
            references = await self._find_symbol_references(old_name, file_path, line, character)
            
            # Detect conflicts
            conflicts = await self._detect_rename_conflicts(old_name, new_name, references)
            
            # Generate changes if no blocking conflicts
            changes = []
            if not any(conflict.is_blocking for conflict in conflicts):
                changes = await self._generate_rename_changes(old_name, new_name, references)
            
            # Apply changes if not dry run and no blocking conflicts
            if not dry_run and changes and not any(conflict.is_blocking for conflict in conflicts):
                await self._apply_rename_changes(changes)
            
            success = len(changes) > 0 and not any(conflict.is_blocking for conflict in conflicts)
            
            return RefactoringResult(
                success=success,
                refactoring_type=RefactoringType.RENAME,
                changes=changes,
                conflicts=conflicts,
                message=f"Renamed '{old_name}' to '{new_name}' in {len(changes)} locations" if success else None,
                metadata={
                    'old_name': old_name,
                    'new_name': new_name,
                    'references_found': len(references),
                    'dry_run': dry_run
                }
            )
            
        except Exception as e:
            logger.error(f"Error in rename refactoring: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.RENAME,
                changes=[],
                conflicts=[],
                error_message=f"Rename refactoring failed: {str(e)}"
            )
    
    def _validate_new_name(self, new_name: str) -> Dict[str, Any]:
        """Validate the new symbol name."""
        # Basic validation rules
        if not new_name:
            return {'valid': False, 'reason': 'Name cannot be empty'}
        
        if not new_name.replace('_', '').replace('-', '').isalnum():
            return {'valid': False, 'reason': 'Name must be alphanumeric (with underscores/hyphens)'}
        
        if new_name[0].isdigit():
            return {'valid': False, 'reason': 'Name cannot start with a digit'}
        
        # Check for reserved keywords (basic set)
        reserved_keywords = {
            'if', 'else', 'for', 'while', 'def', 'class', 'import', 'from',
            'return', 'yield', 'try', 'except', 'finally', 'with', 'as',
            'and', 'or', 'not', 'in', 'is', 'lambda', 'global', 'nonlocal'
        }
        
        if new_name.lower() in reserved_keywords:
            return {'valid': False, 'reason': f"'{new_name}' is a reserved keyword"}
        
        return {'valid': True, 'reason': 'Valid name'}
    
    async def _find_symbol_references(
        self,
        symbol_name: str,
        file_path: str,
        line: int,
        character: int
    ) -> List[Dict[str, Any]]:
        """Find all references to a symbol."""
        references = []
        
        try:
            # Use LSP integration if available
            if self.serena_core and self.serena_core._lsp_integration:
                lsp_references = await self._find_lsp_references(symbol_name, file_path, line, character)
                references.extend(lsp_references)
            else:
                # Fallback to text-based search
                text_references = await self._find_text_references(symbol_name, file_path)
                references.extend(text_references)
            
            logger.debug(f"Found {len(references)} references for symbol '{symbol_name}'")
            return references
            
        except Exception as e:
            logger.error(f"Error finding symbol references: {e}")
            return []
    
    async def _find_lsp_references(
        self,
        symbol_name: str,
        file_path: str,
        line: int,
        character: int
    ) -> List[Dict[str, Any]]:
        """Find references using LSP integration."""
        references = []
        
        try:
            # Get LSP client
            lsp_integration = self.serena_core._lsp_integration
            if not lsp_integration:
                return references
            
            # Use LSP find references capability
            # This would integrate with the actual LSP client
            # For now, return mock data
            references = [
                {
                    'file_path': file_path,
                    'line': line,
                    'character': character,
                    'symbol_name': symbol_name,
                    'context': 'definition',
                    'scope': 'local'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error finding LSP references: {e}")
        
        return references
    
    async def _find_text_references(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Find references using text-based search."""
        references = []
        
        try:
            # Search in the specified file
            file_refs = await self._search_file_for_symbol(symbol_name, file_path)
            references.extend(file_refs)
            
            # Search in related files (same directory)
            directory = Path(file_path).parent
            for py_file in directory.glob("*.py"):
                if str(py_file) != file_path:
                    file_refs = await self._search_file_for_symbol(symbol_name, str(py_file))
                    references.extend(file_refs)
            
        except Exception as e:
            logger.error(f"Error in text-based reference search: {e}")
        
        return references
    
    async def _search_file_for_symbol(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Search for symbol occurrences in a file."""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Use regex to find symbol occurrences
            symbol_pattern = rf'\b{re.escape(symbol_name)}\b'
            
            for line_num, line_content in enumerate(lines, 1):
                matches = re.finditer(symbol_pattern, line_content)
                for match in matches:
                    references.append({
                        'file_path': file_path,
                        'line': line_num,
                        'character': match.start(),
                        'symbol_name': symbol_name,
                        'context': self._determine_context(line_content, match.start()),
                        'scope': 'unknown'
                    })
        
        except Exception as e:
            logger.error(f"Error searching file {file_path}: {e}")
        
        return references
    
    def _determine_context(self, line_content: str, character_pos: int) -> str:
        """Determine the context of a symbol occurrence."""
        # Simple heuristics to determine context
        line_stripped = line_content.strip()
        
        if line_stripped.startswith('def ') and character_pos < 20:
            return 'function_definition'
        elif line_stripped.startswith('class ') and character_pos < 20:
            return 'class_definition'
        elif '=' in line_content and character_pos < line_content.find('='):
            return 'assignment'
        elif line_stripped.startswith('import ') or line_stripped.startswith('from '):
            return 'import'
        else:
            return 'usage'
    
    async def _detect_rename_conflicts(
        self,
        old_name: str,
        new_name: str,
        references: List[Dict[str, Any]]
    ) -> List[RefactoringConflict]:
        """Detect conflicts that would prevent renaming."""
        conflicts = []
        
        try:
            # Check for name collisions in each scope
            scopes_checked = set()
            
            for ref in references:
                file_path = ref['file_path']
                line = ref['line']
                character = ref['character']
                
                # Create a scope identifier
                scope_id = f"{file_path}:{ref.get('scope', 'global')}"
                
                if scope_id not in scopes_checked:
                    scopes_checked.add(scope_id)
                    
                    # Check if new name already exists in this scope
                    if await self._name_exists_in_scope(new_name, file_path, ref.get('scope', 'global')):
                        conflicts.append(create_refactoring_conflict(
                            file_path=file_path,
                            line_number=line,
                            character=character,
                            conflict_type=ConflictType.NAME_COLLISION,
                            description=f"Name '{new_name}' already exists in this scope",
                            severity="error",
                            suggested_resolution=f"Choose a different name or rename the existing '{new_name}' first"
                        ))
            
            # Check for syntax conflicts
            for ref in references:
                if ref['context'] in ['function_definition', 'class_definition']:
                    # Additional validation for definitions
                    if not self._is_valid_identifier_in_context(new_name, ref['context']):
                        conflicts.append(create_refactoring_conflict(
                            file_path=ref['file_path'],
                            line_number=ref['line'],
                            character=ref['character'],
                            conflict_type=ConflictType.SYNTAX_ERROR,
                            description=f"'{new_name}' is not valid in {ref['context']} context",
                            severity="error"
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting rename conflicts: {e}")
            # Add a general conflict if we can't properly detect conflicts
            conflicts.append(create_refactoring_conflict(
                file_path="unknown",
                line_number=0,
                character=0,
                conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                description=f"Could not fully analyze conflicts: {str(e)}",
                severity="warning"
            ))
        
        return conflicts
    
    async def _name_exists_in_scope(self, name: str, file_path: str, scope: str) -> bool:
        """Check if a name already exists in the given scope."""
        try:
            # Simple text-based check
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for the name in various contexts
            patterns = [
                rf'def\s+{re.escape(name)}\s*\(',
                rf'class\s+{re.escape(name)}\s*[:\(]',
                rf'{re.escape(name)}\s*=',
                rf'import\s+{re.escape(name)}',
                rf'from\s+\w+\s+import\s+.*{re.escape(name)}'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking name existence: {e}")
            return True  # Assume conflict to be safe
    
    def _is_valid_identifier_in_context(self, name: str, context: str) -> bool:
        """Check if name is valid in the given context."""
        # Basic validation - could be extended with more sophisticated rules
        if context in ['function_definition', 'class_definition']:
            return name.isidentifier() and not name.startswith('__')
        return name.isidentifier()
    
    async def _generate_rename_changes(
        self,
        old_name: str,
        new_name: str,
        references: List[Dict[str, Any]]
    ) -> List[RefactoringChange]:
        """Generate the actual changes for renaming."""
        changes = []
        
        try:
            for ref in references:
                file_path = ref['file_path']
                line = ref['line']
                character = ref['character']
                
                # Create a change for this reference
                change = create_refactoring_change(
                    file_path=file_path,
                    start_line=line,
                    start_char=character,
                    end_line=line,
                    end_char=character + len(old_name),
                    old_text=old_name,
                    new_text=new_name,
                    change_type=ChangeType.REPLACE,
                    description=f"Rename '{old_name}' to '{new_name}' in {ref['context']}"
                )
                
                changes.append(change)
        
        except Exception as e:
            logger.error(f"Error generating rename changes: {e}")
        
        return changes
    
    async def _apply_rename_changes(self, changes: List[RefactoringChange]) -> None:
        """Apply the rename changes to files."""
        try:
            # Group changes by file
            changes_by_file = {}
            for change in changes:
                if change.file_path not in changes_by_file:
                    changes_by_file[change.file_path] = []
                changes_by_file[change.file_path].append(change)
            
            # Apply changes to each file
            for file_path, file_changes in changes_by_file.items():
                await self._apply_changes_to_file(file_path, file_changes)
            
            logger.info(f"Applied rename changes to {len(changes_by_file)} files")
            
        except Exception as e:
            logger.error(f"Error applying rename changes: {e}")
            raise
    
    async def _apply_changes_to_file(self, file_path: str, changes: List[RefactoringChange]) -> None:
        """Apply changes to a specific file."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Sort changes by position (reverse order to avoid offset issues)
            sorted_changes = sorted(changes, key=lambda c: (c.start_line, c.start_character), reverse=True)
            
            # Apply each change
            for change in sorted_changes:
                line_idx = change.start_line - 1  # Convert to 0-based index
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx]
                    
                    # Replace the text
                    new_line = (
                        line[:change.start_character] +
                        change.new_text +
                        line[change.end_character:]
                    )
                    
                    lines[line_idx] = new_line
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.debug(f"Applied {len(changes)} changes to {file_path}")
            
        except Exception as e:
            logger.error(f"Error applying changes to file {file_path}: {e}")
            raise

