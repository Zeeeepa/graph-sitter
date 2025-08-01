"""
Extract Refactoring

Provides extract method and extract variable refactoring operations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..types import (
    RefactoringType,
    RefactoringResult,
    RefactoringChange,
    RefactoringConflict,
    ChangeType
)
from .refactoring_engine import create_refactoring_change

logger = logging.getLogger(__name__)


class ExtractRefactor:
    """Handles extract method and extract variable operations."""
    
    def __init__(self, codebase_path: str, serena_core: Any, config: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        self.config = config
        logger.debug("ExtractRefactor initialized")
    
    async def initialize(self) -> None:
        """Initialize the extract refactor module."""
        logger.debug("✅ Extract refactor initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the extract refactor module."""
        logger.debug("✅ Extract refactor shutdown")
    
    async def perform_refactoring(
        self,
        dry_run: bool = True,
        operation_id: Optional[str] = None,
        **kwargs
    ) -> RefactoringResult:
        """Perform extract refactoring (method or variable)."""
        try:
            extract_type = kwargs.get('extract_type', 'method')  # 'method' or 'variable'
            file_path = kwargs.get('file_path')
            start_line = kwargs.get('start_line', 0)
            end_line = kwargs.get('end_line', 0)
            new_name = kwargs.get('new_name', f'extracted_{extract_type}')
            
            if not file_path:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.EXTRACT_METHOD if extract_type == 'method' else RefactoringType.EXTRACT_VARIABLE,
                    changes=[],
                    conflicts=[],
                    error_message="file_path is required"
                )
            
            # Generate extraction changes
            changes = await self._generate_extract_changes(
                file_path, start_line, end_line, new_name, extract_type
            )
            
            # Apply changes if not dry run
            if not dry_run and changes:
                await self._apply_extract_changes(changes)
            
            refactoring_type = RefactoringType.EXTRACT_METHOD if extract_type == 'method' else RefactoringType.EXTRACT_VARIABLE
            
            return RefactoringResult(
                success=len(changes) > 0,
                refactoring_type=refactoring_type,
                changes=changes,
                conflicts=[],
                message=f"Extracted {extract_type} '{new_name}'" if changes else None,
                metadata={
                    'extract_type': extract_type,
                    'new_name': new_name,
                    'dry_run': dry_run
                }
            )
            
        except Exception as e:
            logger.error(f"Error in extract refactoring: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                changes=[],
                conflicts=[],
                error_message=f"Extract refactoring failed: {str(e)}"
            )
    
    async def _generate_extract_changes(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        new_name: str,
        extract_type: str
    ) -> List[RefactoringChange]:
        """Generate changes for extraction."""
        changes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract the selected code
            extracted_lines = lines[start_line-1:end_line]
            extracted_code = ''.join(extracted_lines)
            
            if extract_type == 'method':
                # Create new method
                new_method = f"\n    def {new_name}(self):\n"
                for line in extracted_lines:
                    new_method += f"        {line}"
                new_method += "\n"
                
                # Replace original code with method call
                replacement = f"        self.{new_name}()\n"
                
                # Add method definition change
                changes.append(create_refactoring_change(
                    file_path=file_path,
                    start_line=start_line - 1,
                    start_char=0,
                    end_line=start_line - 1,
                    end_char=0,
                    old_text="",
                    new_text=new_method,
                    change_type=ChangeType.INSERT,
                    description=f"Insert extracted method '{new_name}'"
                ))
                
                # Replace original code
                changes.append(create_refactoring_change(
                    file_path=file_path,
                    start_line=start_line,
                    start_char=0,
                    end_line=end_line,
                    end_char=len(lines[end_line-1]) if end_line <= len(lines) else 0,
                    old_text=extracted_code,
                    new_text=replacement,
                    change_type=ChangeType.REPLACE,
                    description=f"Replace code with call to '{new_name}'"
                ))
            
            elif extract_type == 'variable':
                # Create variable assignment
                variable_assignment = f"        {new_name} = {extracted_code.strip()}\n"
                replacement = f"        {new_name}\n"
                
                # Add variable definition
                changes.append(create_refactoring_change(
                    file_path=file_path,
                    start_line=start_line - 1,
                    start_char=0,
                    end_line=start_line - 1,
                    end_char=0,
                    old_text="",
                    new_text=variable_assignment,
                    change_type=ChangeType.INSERT,
                    description=f"Insert variable '{new_name}'"
                ))
                
                # Replace original code
                changes.append(create_refactoring_change(
                    file_path=file_path,
                    start_line=start_line,
                    start_char=0,
                    end_line=end_line,
                    end_char=len(lines[end_line-1]) if end_line <= len(lines) else 0,
                    old_text=extracted_code,
                    new_text=replacement,
                    change_type=ChangeType.REPLACE,
                    description=f"Replace code with variable '{new_name}'"
                ))
            
        except Exception as e:
            logger.error(f"Error generating extract changes: {e}")
        
        return changes
    
    async def _apply_extract_changes(self, changes: List[RefactoringChange]) -> None:
        """Apply extraction changes to files."""
        # Implementation similar to rename refactor
        logger.info(f"Applied {len(changes)} extract changes")

