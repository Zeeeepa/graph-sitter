"""
Fix Application Logic

This module provides real fix application logic for common error types
with rollback support and safety validation.
"""

import re
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .enhanced_error_types import (
    EnhancedErrorInfo, FixSuggestion, FixDifficulty, ErrorCategory
)

logger = logging.getLogger(__name__)


@dataclass
class FixResult:
    """Result of applying a fix."""
    success: bool
    error_id: str
    fix_type: str
    description: str
    files_modified: Dict[str, str]  # file_path -> new_content
    backup_info: Dict[str, str]     # file_path -> original_content
    validation_passed: bool
    new_errors_introduced: List[str] = None
    
    def __post_init__(self):
        if self.new_errors_introduced is None:
            self.new_errors_introduced = []


class FixApplicator:
    """Applies fixes to code with safety validation and rollback support."""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.backup_dir = None
        
    def apply_fix(self, error: EnhancedErrorInfo, fix: FixSuggestion) -> FixResult:
        """Apply a fix with safety validation and rollback support."""
        try:
            # Create backup
            backup_info = self._create_backup(error.location.file_path)
            
            # Apply the fix based on type
            if fix.fix_type == 'add_missing_colon':
                result = self._fix_missing_colon(error, fix)
            elif fix.fix_type == 'fix_undefined_variable':
                result = self._fix_undefined_variable(error, fix)
            elif fix.fix_type == 'add_missing_import':
                result = self._fix_missing_import(error, fix)
            elif fix.fix_type == 'fix_indentation':
                result = self._fix_indentation(error, fix)
            else:
                return FixResult(
                    success=False,
                    error_id=error.id,
                    fix_type=fix.fix_type,
                    description=f"Unsupported fix type: {fix.fix_type}",
                    files_modified={},
                    backup_info=backup_info,
                    validation_passed=False
                )
            
            # Validate the fix
            validation_passed = self._validate_fix(error.location.file_path, result.files_modified)
            result.validation_passed = validation_passed
            
            if not validation_passed:
                # Rollback changes
                self._rollback_changes(backup_info)
                result.success = False
                result.description += " (rolled back due to validation failure)"
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying fix for {error.id}: {e}")
            # Attempt rollback
            if 'backup_info' in locals():
                self._rollback_changes(backup_info)
            
            return FixResult(
                success=False,
                error_id=error.id,
                fix_type=fix.fix_type,
                description=f"Fix application failed: {str(e)}",
                files_modified={},
                backup_info={},
                validation_passed=False
            )
    
    def _create_backup(self, file_path: str) -> Dict[str, str]:
        """Create backup of file before modification."""
        try:
            full_path = self.codebase_path / file_path
            if full_path.exists():
                original_content = full_path.read_text(encoding='utf-8', errors='ignore')
                return {file_path: original_content}
            return {}
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            return {}
    
    def _rollback_changes(self, backup_info: Dict[str, str]):
        """Rollback changes using backup information."""
        for file_path, original_content in backup_info.items():
            try:
                full_path = self.codebase_path / file_path
                full_path.write_text(original_content, encoding='utf-8')
                logger.info(f"Rolled back changes to {file_path}")
            except Exception as e:
                logger.error(f"Failed to rollback {file_path}: {e}")
    
    def _validate_fix(self, file_path: str, modified_files: Dict[str, str]) -> bool:
        """Validate that the fix doesn't introduce syntax errors."""
        try:
            import ast
            
            for path, content in modified_files.items():
                try:
                    # Try to parse the modified content
                    ast.parse(content)
                except SyntaxError as e:
                    logger.warning(f"Fix introduced syntax error in {path}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return False
    
    def _fix_missing_colon(self, error: EnhancedErrorInfo, fix: FixSuggestion) -> FixResult:
        """Fix missing colon errors (e.g., after if, for, def statements)."""
        file_path = error.location.file_path
        full_path = self.codebase_path / file_path
        
        if not full_path.exists():
            return FixResult(
                success=False,
                error_id=error.id,
                fix_type=fix.fix_type,
                description="File not found",
                files_modified={},
                backup_info={},
                validation_passed=False
            )
        
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        # Find the line with the missing colon
        target_line_idx = error.location.line - 1  # Convert to 0-based
        
        if 0 <= target_line_idx < len(lines):
            line = lines[target_line_idx]
            
            # Common patterns that need colons
            colon_patterns = [
                (r'^(\s*)(if\s+.+)$', r'\1\2:'),
                (r'^(\s*)(elif\s+.+)$', r'\1\2:'),
                (r'^(\s*)(else\s*)$', r'\1\2:'),
                (r'^(\s*)(for\s+.+)$', r'\1\2:'),
                (r'^(\s*)(while\s+.+)$', r'\1\2:'),
                (r'^(\s*)(def\s+\w+\s*\([^)]*\)\s*)$', r'\1\2:'),
                (r'^(\s*)(class\s+\w+.*?)$', r'\1\2:'),
                (r'^(\s*)(try\s*)$', r'\1\2:'),
                (r'^(\s*)(except.*?)$', r'\1\2:'),
                (r'^(\s*)(finally\s*)$', r'\1\2:'),
                (r'^(\s*)(with\s+.+)$', r'\1\2:'),
            ]
            
            for pattern, replacement in colon_patterns:
                if re.match(pattern, line) and not line.rstrip().endswith(':'):
                    fixed_line = re.sub(pattern, replacement, line)
                    lines[target_line_idx] = fixed_line
                    
                    new_content = '\n'.join(lines)
                    full_path.write_text(new_content, encoding='utf-8')
                    
                    return FixResult(
                        success=True,
                        error_id=error.id,
                        fix_type=fix.fix_type,
                        description=f"Added missing colon to line {error.location.line}",
                        files_modified={file_path: new_content},
                        backup_info={},
                        validation_passed=True
                    )
        
        return FixResult(
            success=False,
            error_id=error.id,
            fix_type=fix.fix_type,
            description="Could not identify where to add colon",
            files_modified={},
            backup_info={},
            validation_passed=False
        )
    
    def _fix_undefined_variable(self, error: EnhancedErrorInfo, fix: FixSuggestion) -> FixResult:
        """Fix undefined variable errors by suggesting variable definitions."""
        # This is a more complex fix that would require semantic analysis
        # For now, we'll provide a placeholder implementation
        
        return FixResult(
            success=False,
            error_id=error.id,
            fix_type=fix.fix_type,
            description="Undefined variable fixes require manual intervention",
            files_modified={},
            backup_info={},
            validation_passed=False
        )
    
    def _fix_missing_import(self, error: EnhancedErrorInfo, fix: FixSuggestion) -> FixResult:
        """Fix missing import errors by adding import statements."""
        file_path = error.location.file_path
        full_path = self.codebase_path / file_path
        
        if not full_path.exists():
            return FixResult(
                success=False,
                error_id=error.id,
                fix_type=fix.fix_type,
                description="File not found",
                files_modified={},
                backup_info={},
                validation_passed=False
            )
        
        # Extract module name from error message or fix suggestion
        module_to_import = self._extract_module_from_error(error.message)
        if not module_to_import:
            return FixResult(
                success=False,
                error_id=error.id,
                fix_type=fix.fix_type,
                description="Could not determine which module to import",
                files_modified={},
                backup_info={},
                validation_passed=False
            )
        
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        # Find the best place to insert the import
        import_line_idx = self._find_import_insertion_point(lines)
        
        # Add the import
        import_statement = f"import {module_to_import}"
        lines.insert(import_line_idx, import_statement)
        
        new_content = '\n'.join(lines)
        full_path.write_text(new_content, encoding='utf-8')
        
        return FixResult(
            success=True,
            error_id=error.id,
            fix_type=fix.fix_type,
            description=f"Added import statement: {import_statement}",
            files_modified={file_path: new_content},
            backup_info={},
            validation_passed=True
        )
    
    def _fix_indentation(self, error: EnhancedErrorInfo, fix: FixSuggestion) -> FixResult:
        """Fix indentation errors."""
        file_path = error.location.file_path
        full_path = self.codebase_path / file_path
        
        if not full_path.exists():
            return FixResult(
                success=False,
                error_id=error.id,
                fix_type=fix.fix_type,
                description="File not found",
                files_modified={},
                backup_info={},
                validation_passed=False
            )
        
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        # Simple indentation fix: ensure consistent 4-space indentation
        fixed_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                # Convert tabs to spaces
                line_content = line.lstrip()
                # Calculate proper indentation level (assuming 4 spaces per level)
                indent_level = leading_spaces // 4
                fixed_line = '    ' * indent_level + line_content
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)  # Keep empty lines as-is
        
        new_content = '\n'.join(fixed_lines)
        full_path.write_text(new_content, encoding='utf-8')
        
        return FixResult(
            success=True,
            error_id=error.id,
            fix_type=fix.fix_type,
            description="Fixed indentation to use 4 spaces consistently",
            files_modified={file_path: new_content},
            backup_info={},
            validation_passed=True
        )
    
    def _extract_module_from_error(self, error_message: str) -> Optional[str]:
        """Extract module name from error message."""
        # Common patterns in import error messages
        patterns = [
            r"No module named '([^']+)'",
            r"cannot import name '([^']+)'",
            r"ImportError: ([^\s]+)",
            r"ModuleNotFoundError: ([^\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        
        return None
    
    def _find_import_insertion_point(self, lines: List[str]) -> int:
        """Find the best place to insert an import statement."""
        # Look for existing imports
        last_import_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_idx = i
            elif stripped and not stripped.startswith('#'):
                # Found first non-import, non-comment line
                break
        
        if last_import_idx >= 0:
            # Insert after last import
            return last_import_idx + 1
        else:
            # No imports found, insert at beginning (after docstring if present)
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    return i
            return 0


def create_fix_suggestions_for_error(error: EnhancedErrorInfo) -> List[FixSuggestion]:
    """Create fix suggestions for common error types."""
    suggestions = []
    
    # Missing colon fixes
    if 'missing colon' in error.message.lower() or error.error_type == 'E001':
        suggestions.append(FixSuggestion(
            fix_type='add_missing_colon',
            description='Add missing colon after control statement',
            confidence=0.9,
            difficulty=FixDifficulty.EASY,
            code_change=f"Add ':' at end of line {error.location.line}",
            file_changes={error.location.file_path: "Add colon"}
        ))
    
    # Undefined variable fixes
    if 'undefined' in error.message.lower() or 'not defined' in error.message.lower():
        suggestions.append(FixSuggestion(
            fix_type='fix_undefined_variable',
            description='Define the undefined variable',
            confidence=0.6,
            difficulty=FixDifficulty.MEDIUM,
            code_change="Requires manual variable definition",
            file_changes={error.location.file_path: "Add variable definition"},
            side_effects=["May require additional context to determine correct value"]
        ))
    
    # Import error fixes
    if 'import' in error.message.lower() and ('not found' in error.message.lower() or 'cannot import' in error.message.lower()):
        suggestions.append(FixSuggestion(
            fix_type='add_missing_import',
            description='Add missing import statement',
            confidence=0.8,
            difficulty=FixDifficulty.EASY,
            code_change="Add import statement at top of file",
            file_changes={error.location.file_path: "Add import"}
        ))
    
    # Indentation fixes
    if 'indentation' in error.message.lower() or 'indent' in error.message.lower():
        suggestions.append(FixSuggestion(
            fix_type='fix_indentation',
            description='Fix indentation to use consistent 4 spaces',
            confidence=0.85,
            difficulty=FixDifficulty.EASY,
            code_change="Normalize indentation to 4 spaces",
            file_changes={error.location.file_path: "Fix indentation"}
        ))
    
    return suggestions
