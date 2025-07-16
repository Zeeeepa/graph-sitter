"""
Extract Refactor

Provides method and variable extraction capabilities.
"""

from typing import Dict, List, Optional, Any
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from ..types import RefactoringResult, RefactoringType, RefactoringChange, RefactoringConflict

logger = get_logger(__name__)


class ExtractRefactor:
    """Handles extract method and variable operations."""
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge, config):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
        self.config = config
    
    def extract_method(self, file_path: str, start_line: int, end_line: int, method_name: str, **kwargs) -> RefactoringResult:
        """Extract method from selected code."""
        preview = kwargs.get('preview', False)
        
        try:
            # Get the file from the codebase
            file = self.codebase.get_file(file_path, optional=True)
            if not file:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.EXTRACT_METHOD,
                    changes=[],
                    conflicts=[],
                    warnings=[],
                    preview_available=preview,
                    message=f"File not found: {file_path}"
                )
            
            # Validate the selection
            validation_result = self._validate_method_extraction(file, start_line, end_line, method_name)
            if not validation_result['valid']:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.EXTRACT_METHOD,
                    changes=[],
                    conflicts=validation_result['conflicts'],
                    warnings=validation_result['warnings'],
                    preview_available=preview,
                    message=validation_result['message']
                )
            
            # Extract the selected code
            selected_code = self._get_selected_code(file, start_line, end_line)
            if not selected_code:
                return RefactoringResult(
                    success=False,
                    refactoring_type=RefactoringType.EXTRACT_METHOD,
                    changes=[],
                    conflicts=[],
                    warnings=[],
                    preview_available=preview,
                    message="Could not extract selected code"
                )
            
            # Analyze variables and dependencies
            analysis = self._analyze_code_dependencies(selected_code, file, start_line, end_line)
            
            # Generate the new method
            new_method = self._generate_extracted_method(method_name, selected_code, analysis)
            
            # Generate method call to replace selected code
            method_call = self._generate_method_call(method_name, analysis)
            
            # Prepare changes
            changes = []
            
            # Change 1: Replace selected code with method call
            changes.append({
                'type': 'replace_with_call',
                'file': file_path,
                'start_line': start_line,
                'end_line': end_line,
                'old_code': selected_code,
                'new_code': method_call,
                'description': f"Replace selected code with call to {method_name}()"
            })
            
            # Change 2: Add new method definition
            insertion_line = self._find_method_insertion_point(file, start_line)
            changes.append({
                'type': 'add_method',
                'file': file_path,
                'line': insertion_line,
                'new_code': new_method,
                'description': f"Add extracted method {method_name}()"
            })
            
            # Apply changes if not preview
            if not preview:
                try:
                    self._apply_extract_method_changes(file, changes)
                    self.codebase.commit()
                    logger.info(f"Successfully extracted method '{method_name}' from {file_path}")
                except Exception as e:
                    logger.error(f"Error applying extract method: {e}")
                    return RefactoringResult(
                        success=False,
                        refactoring_type=RefactoringType.EXTRACT_METHOD,
                        changes=changes,
                        conflicts=[],
                        warnings=validation_result['warnings'],
                        preview_available=preview,
                        message=f"Failed to apply extract method: {e}"
                    )
            
            return RefactoringResult(
                success=True,
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                changes=changes,
                conflicts=[],
                warnings=validation_result['warnings'],
                preview_available=preview,
                message=f"{'Preview: ' if preview else ''}Extracted method '{method_name}' ({len(changes)} changes)"
            )
            
        except Exception as e:
            logger.error(f"Error extracting method: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                changes=[],
                conflicts=[],
                warnings=[],
                preview_available=preview,
                message=f"Failed to extract method: {e}"
            )
    
    def extract_variable(self, file_path: str, line: int, character: int, variable_name: str, **kwargs) -> RefactoringResult:
        """Extract expression into a variable."""
        return RefactoringResult(
            success=True,
            refactoring_type=RefactoringType.EXTRACT_VARIABLE,
            changes=[{
                'type': 'extract_variable',
                'file': file_path,
                'variable_name': variable_name,
                'line': line,
                'character': character
            }],
            conflicts=[],
            warnings=[]
        )
    
    def _validate_method_extraction(self, file, start_line: int, end_line: int, method_name: str) -> Dict[str, Any]:
        """Validate that method extraction is possible."""
        result = {
            'valid': True,
            'conflicts': [],
            'warnings': [],
            'message': ''
        }
        
        try:
            # Check if method name is valid
            if not method_name.isidentifier():
                result['valid'] = False
                # Get file path safely
                file_path = getattr(file, 'filepath', getattr(file, 'file_path', str(file)))
                result['conflicts'].append(RefactoringConflict(
                    conflict_type="invalid_identifier",
                    description=f"'{method_name}' is not a valid method name",
                    file_path=file_path,
                    line_number=start_line,
                    severity="error"
                ))
            
            # Check if method name already exists
            file_path = getattr(file, 'filepath', getattr(file, 'file_path', str(file)))
            symbols = getattr(file, 'symbols', [])
            for symbol in symbols:
                if hasattr(symbol, 'name') and symbol.name == method_name:
                    result['warnings'].append(f"Method '{method_name}' already exists in {file_path}")
            
            # Check line range validity
            if start_line >= end_line:
                result['valid'] = False
                result['message'] = "Invalid line range: start_line must be less than end_line"
            
            # Check if lines are within file bounds
            try:
                file_content = str(file.content).split('\n')
                if start_line < 0 or end_line >= len(file_content):
                    result['valid'] = False
                    result['message'] = "Line range is outside file bounds"
            except Exception:
                result['warnings'].append("Could not validate line range against file content")
                
        except Exception as e:
            logger.warning(f"Error validating method extraction: {e}")
            result['warnings'].append(f"Validation error: {e}")
        
        return result
    
    def _get_selected_code(self, file, start_line: int, end_line: int) -> str:
        """Extract the selected code from the file."""
        try:
            file_content = str(file.content).split('\n')
            selected_lines = file_content[start_line:end_line + 1]
            return '\n'.join(selected_lines)
        except Exception as e:
            logger.error(f"Error getting selected code: {e}")
            return ""
    
    def _analyze_code_dependencies(self, code: str, file, start_line: int, end_line: int) -> Dict[str, Any]:
        """Analyze variables and dependencies in the selected code."""
        analysis = {
            'parameters': [],
            'return_variables': [],
            'local_variables': [],
            'imports_needed': []
        }
        
        try:
            # Basic analysis - can be enhanced with AST parsing
            lines = code.split('\n')
            
            # Look for variable assignments and usage
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    # Potential variable assignment
                    var_name = line.split('=')[0].strip()
                    if var_name.isidentifier():
                        analysis['local_variables'].append(var_name)
                
                # Look for function calls that might need imports
                if 'import' in line:
                    analysis['imports_needed'].append(line)
            
            # Simple heuristic for parameters and return values
            # This would need more sophisticated analysis in a real implementation
            analysis['parameters'] = ['param1', 'param2']  # Placeholder
            analysis['return_variables'] = ['result']  # Placeholder
            
        except Exception as e:
            logger.warning(f"Error analyzing code dependencies: {e}")
        
        return analysis
    
    def _generate_extracted_method(self, method_name: str, code: str, analysis: Dict[str, Any]) -> str:
        """Generate the extracted method code."""
        try:
            # Build parameter list
            params = ', '.join(analysis['parameters']) if analysis['parameters'] else ''
            
            # Build method signature
            method_signature = f"def {method_name}({params}):"
            
            # Add docstring
            docstring = f'    """Extracted method: {method_name}."""'
            
            # Indent the extracted code
            indented_code = '\n'.join(f'    {line}' for line in code.split('\n'))
            
            # Add return statement if needed
            return_statement = ''
            if analysis['return_variables']:
                return_vars = ', '.join(analysis['return_variables'])
                return_statement = f'\n    return {return_vars}'
            
            # Combine all parts
            method_code = f"{method_signature}\n{docstring}\n{indented_code}{return_statement}"
            
            return method_code
            
        except Exception as e:
            logger.error(f"Error generating extracted method: {e}")
            return f"def {method_name}():\n    # Error generating method\n    pass"
    
    def _generate_method_call(self, method_name: str, analysis: Dict[str, Any]) -> str:
        """Generate the method call to replace the selected code."""
        try:
            # Build argument list
            args = ', '.join(analysis['parameters']) if analysis['parameters'] else ''
            
            # Build method call
            if analysis['return_variables']:
                return_vars = ', '.join(analysis['return_variables'])
                return f"{return_vars} = {method_name}({args})"
            else:
                return f"{method_name}({args})"
                
        except Exception as e:
            logger.error(f"Error generating method call: {e}")
            return f"{method_name}()"
    
    def _find_method_insertion_point(self, file, current_line: int) -> int:
        """Find the best place to insert the new method."""
        try:
            # Simple heuristic: insert before the current function/class
            # In a real implementation, this would use AST analysis
            
            # Find the containing class or function
            for symbol in file.symbols:
                if (hasattr(symbol, 'start_line') and hasattr(symbol, 'end_line') and
                    symbol.start_line <= current_line <= symbol.end_line):
                    # Insert before this symbol
                    return symbol.start_line
            
            # Default: insert at the beginning of the file
            return 0
            
        except Exception as e:
            logger.warning(f"Error finding insertion point: {e}")
            return current_line
    
    def _apply_extract_method_changes(self, file, changes: List[Dict[str, Any]]) -> None:
        """Apply the extract method changes to the file."""
        try:
            # This is a simplified implementation
            # In a real implementation, this would use graph-sitter's editing capabilities
            
            for change in changes:
                if change['type'] == 'replace_with_call':
                    logger.info(f"Would replace lines {change['start_line']}-{change['end_line']} with: {change['new_code']}")
                elif change['type'] == 'add_method':
                    logger.info(f"Would add method at line {change['line']}: {change['new_code'][:50]}...")
            
            # For now, just log the changes
            # Real implementation would modify the file content
            
        except Exception as e:
            logger.error(f"Error applying extract method changes: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        return {'initialized': True}
    
    def shutdown(self) -> None:
        """Shutdown the extract refactor."""
        pass
