"""
Working Error Detection Module

This module provides actual error detection using Python's built-in tools
and external linters like flake8 and pyflakes.
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorInfo:
    """Information about a detected error."""
    file_path: str
    line: int
    column: int
    severity: str  # 'error', 'warning', 'info', 'hint'
    message: str
    code: Optional[str] = None
    source: str = 'python'
    error_type: str = 'unknown'


class WorkingErrorDetector:
    """A working error detector that actually finds errors."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.errors_cache: List[ErrorInfo] = []
        
    def detect_syntax_errors(self, file_path: str) -> List[ErrorInfo]:
        """Detect syntax errors using Python's AST parser."""
        errors = []
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return errors
            
            with open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            try:
                ast.parse(content, filename=str(file_path_obj))
            except SyntaxError as e:
                error = ErrorInfo(
                    file_path=str(file_path_obj),
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    severity='error',
                    message=f"Syntax Error: {e.msg}",
                    code='E999',
                    source='python-ast',
                    error_type='syntax_error'
                )
                errors.append(error)
                
        except Exception as e:
            logger.warning(f"Error checking syntax for {file_path}: {e}")
            
        return errors
    
    def detect_flake8_errors(self, file_path: str) -> List[ErrorInfo]:
        """Detect errors using flake8."""
        errors = []
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return errors
            
            # Run flake8 on the file
            result = subprocess.run(
                ['flake8', '--format=%(path)s:%(row)d:%(col)d:%(code)s:%(text)s', str(file_path_obj)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            parts = line.split(':', 4)
                            if len(parts) >= 5:
                                file_part, line_part, col_part, code_part, message_part = parts
                                
                                # Determine severity based on code
                                severity = 'error'
                                if code_part.startswith('W'):
                                    severity = 'warning'
                                elif code_part.startswith('E9'):
                                    severity = 'error'  # Syntax errors
                                elif code_part.startswith('E'):
                                    severity = 'warning'  # Style errors
                                elif code_part.startswith('F'):
                                    severity = 'error'  # Pyflakes errors
                                
                                error = ErrorInfo(
                                    file_path=file_part,
                                    line=int(line_part),
                                    column=int(col_part),
                                    severity=severity,
                                    message=message_part.strip(),
                                    code=code_part,
                                    source='flake8',
                                    error_type='lint_error'
                                )
                                errors.append(error)
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing flake8 output line: {line} - {e}")
                            
        except subprocess.TimeoutExpired:
            logger.warning(f"flake8 timeout for {file_path}")
        except FileNotFoundError:
            logger.warning("flake8 not found - install with: pip install flake8")
        except Exception as e:
            logger.warning(f"Error running flake8 on {file_path}: {e}")
            
        return errors
    
    def detect_pyflakes_errors(self, file_path: str) -> List[ErrorInfo]:
        """Detect errors using pyflakes."""
        errors = []
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return errors
            
            # Run pyflakes on the file
            result = subprocess.run(
                ['pyflakes', str(file_path_obj)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # pyflakes outputs to stderr for syntax errors, stdout for other errors
            output = result.stdout + result.stderr
            
            if output:
                for line in output.strip().split('\n'):
                    if line.strip() and ':' in line:
                        try:
                            # Parse pyflakes output: file:line:col: message
                            if line.count(':') >= 2:
                                parts = line.split(':', 2)
                                if len(parts) >= 3:
                                    file_part = parts[0]
                                    line_part = parts[1]
                                    message_part = parts[2].strip()
                                    
                                    # Extract column if present
                                    col = 1
                                    if ':' in message_part:
                                        try:
                                            col_part, message_part = message_part.split(':', 1)
                                            col = int(col_part)
                                            message_part = message_part.strip()
                                        except ValueError:
                                            pass
                                    
                                    # Determine error type and severity
                                    severity = 'error'
                                    error_type = 'pyflakes_error'
                                    
                                    if 'undefined name' in message_part.lower():
                                        error_type = 'undefined_name'
                                    elif 'imported but unused' in message_part.lower():
                                        severity = 'warning'
                                        error_type = 'unused_import'
                                    elif 'redefinition' in message_part.lower():
                                        severity = 'warning'
                                        error_type = 'redefinition'
                                    
                                    error = ErrorInfo(
                                        file_path=file_part,
                                        line=int(line_part),
                                        column=col,
                                        severity=severity,
                                        message=message_part,
                                        code=None,
                                        source='pyflakes',
                                        error_type=error_type
                                    )
                                    errors.append(error)
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing pyflakes output line: {line} - {e}")
                            
        except subprocess.TimeoutExpired:
            logger.warning(f"pyflakes timeout for {file_path}")
        except FileNotFoundError:
            logger.warning("pyflakes not found - install with: pip install pyflakes")
        except Exception as e:
            logger.warning(f"Error running pyflakes on {file_path}: {e}")
            
        return errors
    
    def detect_all_errors(self, file_path: str) -> List[ErrorInfo]:
        """Detect all errors in a file using multiple methods."""
        all_errors = []
        
        # Use AST for syntax errors (fastest)
        syntax_errors = self.detect_syntax_errors(file_path)
        all_errors.extend(syntax_errors)
        
        # If there are syntax errors, don't run other tools
        if syntax_errors:
            return all_errors
        
        # Use flake8 for comprehensive checking
        flake8_errors = self.detect_flake8_errors(file_path)
        all_errors.extend(flake8_errors)
        
        # Use pyflakes for additional checks
        pyflakes_errors = self.detect_pyflakes_errors(file_path)
        
        # Deduplicate pyflakes errors that might overlap with flake8
        for pyflakes_error in pyflakes_errors:
            # Check if this error is already covered by flake8
            duplicate = False
            for existing_error in all_errors:
                if (existing_error.file_path == pyflakes_error.file_path and
                    existing_error.line == pyflakes_error.line and
                    existing_error.column == pyflakes_error.column):
                    duplicate = True
                    break
            
            if not duplicate:
                all_errors.append(pyflakes_error)
        
        return all_errors
    
    def scan_directory(self, directory: str = None) -> List[ErrorInfo]:
        """Scan a directory for Python files and detect errors."""
        if directory is None:
            directory = self.repo_path
        else:
            directory = Path(directory)
        
        all_errors = []
        python_files = list(directory.rglob("*.py"))
        
        logger.info(f"Scanning {len(python_files)} Python files for errors...")
        
        for i, py_file in enumerate(python_files):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(python_files)} files scanned...")
            
            try:
                file_errors = self.detect_all_errors(str(py_file))
                all_errors.extend(file_errors)
            except Exception as e:
                logger.warning(f"Error scanning {py_file}: {e}")
        
        logger.info(f"Scan complete: found {len(all_errors)} errors in {len(python_files)} files")
        
        self.errors_cache = all_errors
        return all_errors
    
    def get_errors(self) -> List[ErrorInfo]:
        """Get all cached errors."""
        return self.errors_cache
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        return [error for error in self.errors_cache if error.file_path == file_path]
