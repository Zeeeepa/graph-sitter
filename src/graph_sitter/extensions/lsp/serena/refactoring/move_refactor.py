"""
Move Refactoring

Provides move symbol and move file refactoring operations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..types import (
    RefactoringType,
    RefactoringResult,
    RefactoringChange,
    ChangeType
)
from .refactoring_engine import create_refactoring_change

logger = logging.getLogger(__name__)


class MoveRefactor:
    """Handles move symbol and move file operations."""
    
    def __init__(self, codebase_path: str, serena_core: Any, config: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        self.config = config
        logger.debug("MoveRefactor initialized")
    
    async def initialize(self) -> None:
        """Initialize the move refactor module."""
        logger.debug("✅ Move refactor initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the move refactor module."""
        logger.debug("✅ Move refactor shutdown")
    
    async def perform_refactoring(
        self,
        dry_run: bool = True,
        operation_id: Optional[str] = None,
        **kwargs
    ) -> RefactoringResult:
        """Perform move refactoring (symbol or file)."""
        try:
            move_type = kwargs.get('move_type', 'symbol')  # 'symbol' or 'file'
            source_path = kwargs.get('source_path')
            target_path = kwargs.get('target_path')
            symbol_name = kwargs.get('symbol_name')  # For symbol moves
            
            if not source_path or not target_path:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.MOVE_SYMBOL if move_type == 'symbol' else RefactoringType.MOVE_FILE,
                    changes=[],
                    conflicts=[],
                    error_message="source_path and target_path are required"
                )
            
            # Generate move changes
            if move_type == 'symbol':
                changes = await self._generate_symbol_move_changes(source_path, target_path, symbol_name)
            else:
                changes = await self._generate_file_move_changes(source_path, target_path)
            
            # Apply changes if not dry run
            if not dry_run and changes:
                await self._apply_move_changes(changes)
            
            refactoring_type = RefactoringType.MOVE_SYMBOL if move_type == 'symbol' else RefactoringType.MOVE_FILE
            
            return RefactoringResult(
                success=len(changes) > 0,
                refactoring_type=refactoring_type,
                changes=changes,
                conflicts=[],
                message=f"Moved {move_type} from {source_path} to {target_path}" if changes else None,
                metadata={
                    'move_type': move_type,
                    'source_path': source_path,
                    'target_path': target_path,
                    'symbol_name': symbol_name,
                    'dry_run': dry_run
                }
            )
            
        except Exception as e:
            logger.error(f"Error in move refactoring: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.MOVE_SYMBOL,
                changes=[],
                conflicts=[],
                error_message=f"Move refactoring failed: {str(e)}"
            )
    
    async def _generate_symbol_move_changes(
        self,
        source_path: str,
        target_path: str,
        symbol_name: str
    ) -> List[RefactoringChange]:
        """Generate changes for moving a symbol."""
        changes = []
        
        try:
            # Read source file
            with open(source_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            
            # Find symbol definition
            symbol_content = ""
            symbol_start = None
            symbol_end = None
            
            for i, line in enumerate(source_lines):
                if f"def {symbol_name}(" in line or f"class {symbol_name}" in line:
                    symbol_start = i + 1
                    symbol_content = line
                    
                    # Find end of symbol (simplified)
                    j = i + 1
                    while j < len(source_lines):
                        if source_lines[j].startswith('def ') or source_lines[j].startswith('class '):
                            break
                        if source_lines[j].strip():
                            symbol_content += source_lines[j]
                        j += 1
                    symbol_end = j
                    break
            
            if symbol_start and symbol_end:
                # Remove from source
                changes.append(create_refactoring_change(
                    file_path=source_path,
                    start_line=symbol_start,
                    start_char=0,
                    end_line=symbol_end,
                    end_char=0,
                    old_text=symbol_content,
                    new_text="",
                    change_type=ChangeType.DELETE,
                    description=f"Remove {symbol_name} from {source_path}"
                ))
                
                # Add to target
                changes.append(create_refactoring_change(
                    file_path=target_path,
                    start_line=1,  # Add at beginning
                    start_char=0,
                    end_line=1,
                    end_char=0,
                    old_text="",
                    new_text=symbol_content + "\n",
                    change_type=ChangeType.INSERT,
                    description=f"Add {symbol_name} to {target_path}"
                ))
            
        except Exception as e:
            logger.error(f"Error generating symbol move changes: {e}")
        
        return changes
    
    async def _generate_file_move_changes(
        self,
        source_path: str,
        target_path: str
    ) -> List[RefactoringChange]:
        """Generate changes for moving a file."""
        changes = []
        
        try:
            # Read entire source file
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create new file
            changes.append(create_refactoring_change(
                file_path=target_path,
                start_line=1,
                start_char=0,
                end_line=1,
                end_char=0,
                old_text="",
                new_text=content,
                change_type=ChangeType.INSERT,
                description=f"Create file {target_path}"
            ))
            
            # Delete source file (mark for deletion)
            changes.append(create_refactoring_change(
                file_path=source_path,
                start_line=1,
                start_char=0,
                end_line=len(content.split('\n')),
                end_char=0,
                old_text=content,
                new_text="",
                change_type=ChangeType.DELETE,
                description=f"Delete file {source_path}"
            ))
            
        except Exception as e:
            logger.error(f"Error generating file move changes: {e}")
        
        return changes
    
    async def _apply_move_changes(self, changes: List[RefactoringChange]) -> None:
        """Apply move changes to files."""
        logger.info(f"Applied {len(changes)} move changes")

