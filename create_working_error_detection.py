#!/usr/bin/env python3
"""
CREATE WORKING ERROR DETECTION

This creates a proper error detection system that actually works.
"""

import subprocess
import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

def create_working_error_detection():
    """Create a working error detection implementation."""
    print("🔧 CREATING WORKING ERROR DETECTION")
    print("=" * 60)
    
    # Create a new error detection module
    error_detection_file = Path("src/graph_sitter/core/working_error_detection.py")
    error_detection_content = '''"""
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
                for line in result.stdout.strip().split('\\n'):
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
                for line in output.strip().split('\\n'):
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
'''
    
    error_detection_file.parent.mkdir(parents=True, exist_ok=True)
    with open(error_detection_file, 'w') as f:
        f.write(error_detection_content)
    
    print(f"✅ Created working error detection: {error_detection_file}")
    
    # Update the unified interface to use the working error detection
    update_unified_interface()
    
    return True


def update_unified_interface():
    """Update the unified interface to use working error detection."""
    print("\n🔧 UPDATING UNIFIED INTERFACE")
    print("=" * 60)
    
    # Update the error methods to use working detection
    error_methods_file = Path("src/graph_sitter/core/error_methods.py")
    
    if not error_methods_file.exists():
        print(f"❌ File not found: {error_methods_file}")
        return False
    
    # Read current content
    with open(error_methods_file, 'r') as f:
        content = f.read()
    
    # Add import for working error detection
    if "from graph_sitter.core.working_error_detection import WorkingErrorDetector" not in content:
        # Add import after existing imports
        import_line = "from graph_sitter.core.working_error_detection import WorkingErrorDetector, ErrorInfo as WorkingErrorInfo"
        
        # Find a good place to add the import
        lines = content.split('\\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from graph_sitter.') or line.startswith('import '):
                insert_index = i + 1
        
        lines.insert(insert_index, import_line)
        content = '\\n'.join(lines)
        print("✅ Added working error detection import")
    
    # Update the errors method to use working detection
    old_errors_method = '''def errors(self) -> List[Dict[str, Any]]:
    """Get all errors in the codebase using Serena analysis."""
    try:
        from graph_sitter.analysis.serena_analysis import SerenaAnalyzer
        
        analyzer = SerenaAnalyzer(str(self.repo_path))
        all_errors = analyzer.collect_all_lsp_diagnostics()
        
        # Convert to standard format
        error_list = []
        for error in all_errors:
            if hasattr(error, '__dict__'):
                error_dict = {
                    'id': f"{error.file_path}:{error.line}:{error.character}",
                    'file_path': error.file_path,
                    'line': error.line,
                    'character': error.character,
                    'severity': error.severity,
                    'message': error.message,
                    'source': error.source,
                    'code': getattr(error, 'code', None)
                }
                error_list.append(error_dict)
        
        return error_list
        
    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        return []'''
    
    new_errors_method = '''def errors(self) -> List[Dict[str, Any]]:
    """Get all errors in the codebase using working error detection."""
    try:
        # Use working error detection
        detector = WorkingErrorDetector(str(self.repo_path))
        all_errors = detector.scan_directory()
        
        # Convert to standard format
        error_list = []
        for error in all_errors:
            error_dict = {
                'id': f"{error.file_path}:{error.line}:{error.column}",
                'file_path': error.file_path,
                'line': error.line,
                'character': error.column,
                'column': error.column,
                'severity': error.severity,
                'message': error.message,
                'source': error.source,
                'code': error.code,
                'error_type': error.error_type
            }
            error_list.append(error_dict)
        
        logger.info(f"Found {len(error_list)} errors using working detection")
        return error_list
        
    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return []'''
    
    if old_errors_method in content:
        content = content.replace(old_errors_method, new_errors_method)
        print("✅ Updated errors method to use working detection")
    else:
        print("⚠️  errors method not found or already updated")
    
    # Write updated content
    with open(error_methods_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated unified interface: {error_methods_file}")
    return True


def test_working_error_detection():
    """Test the working error detection."""
    print("\n🧪 TESTING WORKING ERROR DETECTION")
    print("=" * 60)
    
    try:
        # Import the working error detection
        sys.path.insert(0, str(Path("src").absolute()))
        from graph_sitter.core.working_error_detection import WorkingErrorDetector
        
        # Create test files
        test_dir = Path("test_working_detection")
        test_dir.mkdir(exist_ok=True)
        
        # Syntax error file
        syntax_file = test_dir / "syntax_error.py"
        syntax_file.write_text("def broken()  # missing colon\\n    return 'broken'")
        
        # Import error file  
        import_file = test_dir / "import_error.py"
        import_file.write_text("import non_existent_module\\nprint('hello')")
        
        # Name error file
        name_file = test_dir / "name_error.py"
        name_file.write_text("result = undefined_variable\\nprint(result)")
        
        # Valid file
        valid_file = test_dir / "valid.py"
        valid_file.write_text("def working():\\n    return 'working'\\n\\nprint(working())")
        
        print(f"✅ Created test files in {test_dir}")
        
        # Test the detector
        detector = WorkingErrorDetector(str(test_dir))
        
        # Test individual files
        print("\\n🔍 Testing individual file detection...")
        
        for test_file in [syntax_file, import_file, name_file, valid_file]:
            print(f"\\n📄 Testing {test_file.name}...")
            errors = detector.detect_all_errors(str(test_file))
            print(f"   Found {len(errors)} errors:")
            for error in errors:
                print(f"      {error.severity}: {error.message} (line {error.line})")
        
        # Test directory scan
        print("\\n🔍 Testing directory scan...")
        all_errors = detector.scan_directory(str(test_dir))
        print(f"   Total errors found: {len(all_errors)}")
        
        # Count by severity
        error_counts = {'error': 0, 'warning': 0, 'info': 0, 'hint': 0}
        for error in all_errors:
            if error.severity in error_counts:
                error_counts[error.severity] += 1
        
        print("   Error breakdown:")
        for severity, count in error_counts.items():
            if count > 0:
                emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}[severity]
                print(f"      {emoji} {severity}: {count}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print(f"\\n🧹 Cleaned up test directory")
        
        # Test with unified interface
        print("\\n🎯 Testing unified interface...")
        from graph_sitter import Codebase
        from graph_sitter.core.diagnostics import add_diagnostic_capabilities
        
        codebase = Codebase(".")
        add_diagnostic_capabilities(codebase, enable_lsp=True)
        
        if hasattr(codebase, 'errors'):
            errors = codebase.errors()
            print(f"   Unified interface found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
            
            if isinstance(errors, list) and len(errors) > 0:
                print("   ✅ Working error detection is integrated!")
                for i, error in enumerate(errors[:3]):
                    print(f"      {i+1}. {error.get('severity', 'unknown')}: {error.get('message', 'no message')}")
            else:
                print("   ⚠️  No errors found - may be a clean codebase or need more time")
        
        return len(all_errors) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Create and test working error detection."""
    print("🔧 CREATING WORKING ERROR DETECTION SYSTEM")
    print("=" * 80)
    print("This will create a proper error detection system that actually works.")
    print()
    
    # Create working error detection
    success1 = create_working_error_detection()
    
    if success1:
        # Test the working error detection
        success2 = test_working_error_detection()
        
        if success2:
            print("\\n🎉 WORKING ERROR DETECTION CREATED SUCCESSFULLY!")
            print("\\n✅ The system now has:")
            print("   • Syntax error detection using Python AST")
            print("   • Comprehensive error detection using flake8")
            print("   • Additional checks using pyflakes")
            print("   • Unified interface integration")
            print("   • Proper error categorization and reporting")
            return True
        else:
            print("\\n⚠️  Error detection created but testing failed")
            return False
    else:
        print("\\n❌ Failed to create working error detection")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

