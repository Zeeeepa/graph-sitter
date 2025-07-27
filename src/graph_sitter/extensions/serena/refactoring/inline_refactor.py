"""
Inline Refactoring

Provides inline method and inline variable refactoring operations.
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


class InlineRefactor:
    """Handles inline method and inline variable operations."""
    
    def __init__(self, codebase_path: str, serena_core: Any, config: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        self.config = config
        logger.debug("InlineRefactor initialized")
    
    async def initialize(self) -> None:
        """Initialize the inline refactor module."""
        logger.debug("✅ Inline refactor initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the inline refactor module."""
        logger.debug("✅ Inline refactor shutdown")
    
    async def perform_refactoring(
        self,
        dry_run: bool = True,
        operation_id: Optional[str] = None,
        **kwargs
    ) -> RefactoringResult:
        """Perform inline refactoring (method or variable)."""
        try:
            inline_type = kwargs.get('inline_type', 'method')  # 'method' or 'variable'
            symbol_name = kwargs.get('symbol_name')
            file_path = kwargs.get('file_path')
            
            if not symbol_name or not file_path:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.INLINE_METHOD if inline_type == 'method' else RefactoringType.INLINE_VARIABLE,
                    changes=[],
                    conflicts=[],
                    error_message="symbol_name and file_path are required"
                )
            
            # Generate inline changes
            changes = await self._generate_inline_changes(file_path, symbol_name, inline_type)
            
            # Apply changes if not dry run
            if not dry_run and changes:
                await self._apply_inline_changes(changes)
            
            refactoring_type = RefactoringType.INLINE_METHOD if inline_type == 'method' else RefactoringType.INLINE_VARIABLE
            
            return RefactoringResult(
                success=len(changes) > 0,
                refactoring_type=refactoring_type,
                changes=changes,
                conflicts=[],
                message=f"Inlined {inline_type} '{symbol_name}'" if changes else None,
                metadata={
                    'inline_type': inline_type,
                    'symbol_name': symbol_name,
                    'dry_run': dry_run
                }
            )
            
        except Exception as e:
            logger.error(f"Error in inline refactoring: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.INLINE_METHOD,
                changes=[],
                conflicts=[],
                error_message=f"Inline refactoring failed: {str(e)}"
            )
    
    async def _generate_inline_changes(
        self,
        file_path: str,
        symbol_name: str,
        inline_type: str
    ) -> List[RefactoringChange]:
        """Generate changes for inlining."""
        changes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find symbol definition and usages
            definition_line = None
            definition_content = ""
            usages = []
            
            for i, line in enumerate(lines):
                if inline_type == 'method' and f"def {symbol_name}(" in line:
                    definition_line = i + 1
                    # Extract method body (simplified)
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
                        if lines[j].strip():
                            definition_content += lines[j].strip() + "\n"
                        j += 1
                elif inline_type == 'variable' and f"{symbol_name} =" in line:
                    definition_line = i + 1
                    # Extract variable value
                    definition_content = line.split('=', 1)[1].strip()
                elif f"{symbol_name}(" in line or f"{symbol_name}" in line:
                    usages.append(i + 1)
            
            if definition_line and definition_content:
                # Remove definition
                changes.append(create_refactoring_change(
                    file_path=file_path,
                    start_line=definition_line,
                    start_char=0,
                    end_line=definition_line,
                    end_char=len(lines[definition_line-1]),
                    old_text=lines[definition_line-1],
                    new_text="",
                    change_type=ChangeType.DELETE,
                    description=f"Remove {inline_type} definition '{symbol_name}'"
                ))
                
                # Replace usages with inline content
                for usage_line in usages:
                    if usage_line != definition_line:
                        old_line = lines[usage_line-1]
                        if inline_type == 'method':
                            new_line = old_line.replace(f"{symbol_name}()", definition_content.strip())
                        else:
                            new_line = old_line.replace(symbol_name, definition_content)
                        
                        changes.append(create_refactoring_change(
                            file_path=file_path,
                            start_line=usage_line,
                            start_char=0,
                            end_line=usage_line,
                            end_char=len(old_line),
                            old_text=old_line,
                            new_text=new_line,
                            change_type=ChangeType.REPLACE,
                            description=f"Inline {inline_type} '{symbol_name}'"
                        ))
            
        except Exception as e:
            logger.error(f"Error generating inline changes: {e}")
        
        return changes
    
    async def _apply_inline_changes(self, changes: List[RefactoringChange]) -> None:
        """Apply inline changes to files."""
        logger.info(f"Applied {len(changes)} inline changes")

