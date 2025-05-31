"""
Code Validation System for Graph-Sitter

Provides comprehensive validation for code files, syntax checking,
and quality assessment before analysis.
"""

import os
import ast
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import hashlib
import mimetypes
import chardet


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    file_path: str
    language: str
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    encoding: str
    file_size: int
    line_count: int


@dataclass
class SyntaxCheckResult:
    """Result of syntax checking"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    line_number: Optional[int] = None
    column_number: Optional[int] = None


class CodeValidator:
    """
    Comprehensive code validation system
    """
    
    def __init__(self, max_file_size_mb: int = 10):
        """
        Initialize the code validator
        
        Args:
            max_file_size_mb: Maximum file size to process in MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
        
        # Supported file extensions and their languages
        self.language_extensions = {
            '.py': 'python',
            '.pyx': 'python',
            '.pyi': 'python',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.mjs': 'javascript',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.h': 'c',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.R': 'r',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.md': 'markdown',
            '.markdown': 'markdown'
        }
        
        # Binary file extensions to skip
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.a', '.lib',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv',
            '.pyc', '.pyo', '.class', '.jar', '.war'
        }
        
        # Files to always skip
        self.skip_patterns = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.venv', 'venv', '.env', 'env', 'build', 'dist',
            'target', 'bin', 'obj', 'out', '.idea', '.vscode'
        }
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a single file
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            ValidationResult with validation details
        """
        self.logger.debug(f"Validating file: {file_path}")
        
        errors = []
        warnings = []
        metrics = {}
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                errors.append(f"File does not exist: {file_path}")
                return ValidationResult(
                    is_valid=False,
                    file_path=file_path,
                    language='unknown',
                    errors=errors,
                    warnings=warnings,
                    metrics=metrics,
                    encoding='unknown',
                    file_size=0,
                    line_count=0
                )
            
            # Check if it's a file (not directory)
            if not os.path.isfile(file_path):
                errors.append(f"Path is not a file: {file_path}")
                return ValidationResult(
                    is_valid=False,
                    file_path=file_path,
                    language='unknown',
                    errors=errors,
                    warnings=warnings,
                    metrics=metrics,
                    encoding='unknown',
                    file_size=0,
                    line_count=0
                )
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_path_obj = Path(file_path)
            
            # Check file size
            if file_size > self.max_file_size_bytes:
                errors.append(f"File too large: {file_size / (1024*1024):.1f}MB > {self.max_file_size_mb}MB")
            
            # Check if file should be skipped
            if self._should_skip_file(file_path):
                warnings.append(f"File type typically skipped: {file_path}")
            
            # Detect language
            language = self._detect_language(file_path)
            if not language:
                warnings.append(f"Unknown file type: {file_path_obj.suffix}")
                language = 'unknown'
            
            # Check if binary file
            if self._is_binary_file(file_path):
                errors.append("File appears to be binary")
                return ValidationResult(
                    is_valid=False,
                    file_path=file_path,
                    language=language,
                    errors=errors,
                    warnings=warnings,
                    metrics=metrics,
                    encoding='binary',
                    file_size=file_size,
                    line_count=0
                )
            
            # Detect encoding and read file
            encoding, content = self._read_file_with_encoding(file_path)
            if not content:
                errors.append("Could not read file content")
                return ValidationResult(
                    is_valid=False,
                    file_path=file_path,
                    language=language,
                    errors=errors,
                    warnings=warnings,
                    metrics=metrics,
                    encoding=encoding,
                    file_size=file_size,
                    line_count=0
                )
            
            # Count lines
            line_count = content.count('\n') + 1 if content else 0
            
            # Basic content validation
            content_errors, content_warnings = self._validate_content(content, language)
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            
            # Syntax validation
            if language in ['python', 'javascript', 'typescript', 'java']:
                syntax_result = self._validate_syntax(content, language, file_path)
                if not syntax_result.is_valid:
                    errors.extend(syntax_result.errors)
                warnings.extend(syntax_result.warnings)
            
            # Calculate basic metrics
            metrics = self._calculate_basic_metrics(content, language)
            
            # Security checks
            security_warnings = self._check_security_issues(content, language)
            warnings.extend(security_warnings)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                file_path=file_path,
                language=language,
                errors=errors,
                warnings=warnings,
                metrics=metrics,
                encoding=encoding,
                file_size=file_size,
                line_count=line_count
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed for {file_path}: {str(e)}")
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                file_path=file_path,
                language='unknown',
                errors=errors,
                warnings=warnings,
                metrics=metrics,
                encoding='unknown',
                file_size=0,
                line_count=0
            )
    
    def validate_directory(self, directory_path: str, recursive: bool = True) -> List[ValidationResult]:
        """
        Validate all files in a directory
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            
        Returns:
            List of ValidationResult objects
        """
        self.logger.info(f"Validating directory: {directory_path}")
        
        results = []
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Invalid directory: {directory_path}")
            return results
        
        # Get all files
        if recursive:
            files = directory.rglob('*')
        else:
            files = directory.glob('*')
        
        for file_path in files:
            if file_path.is_file() and not self._should_skip_file(str(file_path)):
                result = self.validate_file(str(file_path))
                results.append(result)
        
        return results
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        return self.language_extensions.get(extension)
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() in self.binary_extensions:
            return True
        
        # Check path components
        for part in path.parts:
            if part in self.skip_patterns:
                return True
        
        # Check filename patterns
        if path.name.startswith('.') and path.name not in {'.gitignore', '.env.example'}:
            return True
        
        return False
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is binary"""
        try:
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith('text/'):
                return True
            
            # Read first chunk and check for null bytes
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
            
            return False
            
        except Exception:
            return True
    
    def _read_file_with_encoding(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Read file with proper encoding detection"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'utf-8', content
        except UnicodeDecodeError:
            pass
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
            
            # Read with detected encoding
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
                return encoding, content
                
        except Exception as e:
            self.logger.warning(f"Could not read file {file_path}: {str(e)}")
            return 'unknown', None
    
    def _validate_content(self, content: str, language: str) -> Tuple[List[str], List[str]]:
        """Validate file content"""
        errors = []
        warnings = []
        
        # Check for empty content
        if not content.strip():
            warnings.append("File is empty or contains only whitespace")
            return errors, warnings
        
        # Check for very long lines
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 500:
                warnings.append(f"Very long line at line {i}: {len(line)} characters")
        
        # Check for mixed line endings
        if '\r\n' in content and '\n' in content.replace('\r\n', ''):
            warnings.append("Mixed line endings detected")
        
        # Check for tabs vs spaces (for Python)
        if language == 'python':
            has_tabs = '\t' in content
            has_spaces = '    ' in content or '  ' in content
            if has_tabs and has_spaces:
                warnings.append("Mixed tabs and spaces for indentation")
        
        # Check for potential encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            warnings.append("File contains characters that may cause encoding issues")
        
        return errors, warnings
    
    def _validate_syntax(self, content: str, language: str, file_path: str) -> SyntaxCheckResult:
        """Validate syntax for supported languages"""
        if language == 'python':
            return self._validate_python_syntax(content)
        elif language in ['javascript', 'typescript']:
            return self._validate_js_ts_syntax(content, language, file_path)
        elif language == 'java':
            return self._validate_java_syntax(content, file_path)
        else:
            return SyntaxCheckResult(is_valid=True, errors=[], warnings=[])
    
    def _validate_python_syntax(self, content: str) -> SyntaxCheckResult:
        """Validate Python syntax using AST"""
        try:
            ast.parse(content)
            return SyntaxCheckResult(is_valid=True, errors=[], warnings=[])
        except SyntaxError as e:
            return SyntaxCheckResult(
                is_valid=False,
                errors=[f"Syntax error: {e.msg}"],
                warnings=[],
                line_number=e.lineno,
                column_number=e.offset
            )
        except Exception as e:
            return SyntaxCheckResult(
                is_valid=False,
                errors=[f"Parse error: {str(e)}"],
                warnings=[]
            )
    
    def _validate_js_ts_syntax(self, content: str, language: str, file_path: str) -> SyntaxCheckResult:
        """Validate JavaScript/TypeScript syntax using external tools"""
        errors = []
        warnings = []
        
        try:
            # Try using Node.js to validate syntax
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language[:2]}', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            try:
                # Use node to check syntax
                result = subprocess.run(
                    ['node', '--check', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    errors.append(f"Syntax error: {result.stderr.strip()}")
                    return SyntaxCheckResult(is_valid=False, errors=errors, warnings=warnings)
                
            finally:
                os.unlink(temp_file)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Node.js not available or other error, skip syntax check
            warnings.append("Could not validate JavaScript/TypeScript syntax (Node.js not available)")
        except Exception as e:
            warnings.append(f"Syntax validation error: {str(e)}")
        
        return SyntaxCheckResult(is_valid=True, errors=errors, warnings=warnings)
    
    def _validate_java_syntax(self, content: str, file_path: str) -> SyntaxCheckResult:
        """Validate Java syntax using javac"""
        errors = []
        warnings = []
        
        try:
            import tempfile
            
            # Extract class name from content
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            if not class_match:
                warnings.append("No public class found, skipping syntax validation")
                return SyntaxCheckResult(is_valid=True, errors=errors, warnings=warnings)
            
            class_name = class_match.group(1)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                java_file = os.path.join(temp_dir, f"{class_name}.java")
                with open(java_file, 'w') as f:
                    f.write(content)
                
                # Use javac to check syntax
                result = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    errors.append(f"Compilation error: {result.stderr.strip()}")
                    return SyntaxCheckResult(is_valid=False, errors=errors, warnings=warnings)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            warnings.append("Could not validate Java syntax (javac not available)")
        except Exception as e:
            warnings.append(f"Syntax validation error: {str(e)}")
        
        return SyntaxCheckResult(is_valid=True, errors=errors, warnings=warnings)
    
    def _calculate_basic_metrics(self, content: str, language: str) -> Dict[str, Any]:
        """Calculate basic code metrics"""
        lines = content.split('\n')
        
        metrics = {
            'total_lines': len(lines),
            'blank_lines': sum(1 for line in lines if not line.strip()),
            'comment_lines': 0,
            'code_lines': 0,
            'max_line_length': max(len(line) for line in lines) if lines else 0,
            'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0
        }
        
        # Count comment lines based on language
        comment_patterns = {
            'python': ['#'],
            'javascript': ['//', '/*', '*/', '/**'],
            'typescript': ['//', '/*', '*/', '/**'],
            'java': ['//', '/*', '*/', '/**'],
            'csharp': ['//', '/*', '*/', '/**'],
            'cpp': ['//', '/*', '*/', '/**'],
            'c': ['//', '/*', '*/', '/**'],
            'shell': ['#'],
            'yaml': ['#'],
            'sql': ['--', '/*', '*/']
        }
        
        patterns = comment_patterns.get(language, [])
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(pattern) for pattern in patterns):
                metrics['comment_lines'] += 1
            elif stripped:
                metrics['code_lines'] += 1
        
        # Calculate ratios
        if metrics['total_lines'] > 0:
            metrics['comment_ratio'] = metrics['comment_lines'] / metrics['total_lines']
            metrics['blank_ratio'] = metrics['blank_lines'] / metrics['total_lines']
            metrics['code_ratio'] = metrics['code_lines'] / metrics['total_lines']
        else:
            metrics['comment_ratio'] = 0
            metrics['blank_ratio'] = 0
            metrics['code_ratio'] = 0
        
        return metrics
    
    def _check_security_issues(self, content: str, language: str) -> List[str]:
        """Check for potential security issues"""
        warnings = []
        
        # Common security patterns to check
        security_patterns = {
            'hardcoded_password': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'pwd\s*=\s*["\'][^"\']+["\']',
                r'passwd\s*=\s*["\'][^"\']+["\']'
            ],
            'hardcoded_key': [
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret_key\s*=\s*["\'][^"\']+["\']',
                r'private_key\s*=\s*["\'][^"\']+["\']'
            ],
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'query\s*\(\s*["\'].*\+.*["\']'
            ],
            'command_injection': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'eval\s*\(',
                r'exec\s*\('
            ]
        }
        
        import re
        for issue_type, patterns in security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    warnings.append(f"Potential security issue: {issue_type}")
                    break
        
        # Check for TODO/FIXME comments that might indicate security issues
        todo_patterns = [
            r'TODO.*security',
            r'FIXME.*security',
            r'TODO.*auth',
            r'FIXME.*auth',
            r'TODO.*encrypt',
            r'FIXME.*encrypt'
        ]
        
        for pattern in todo_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append("Security-related TODO/FIXME found")
                break
        
        return warnings
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_files = len(results)
        valid_files = sum(1 for r in results if r.is_valid)
        invalid_files = total_files - valid_files
        
        languages = {}
        total_errors = 0
        total_warnings = 0
        total_size = 0
        total_lines = 0
        
        for result in results:
            # Count by language
            lang = result.language
            if lang not in languages:
                languages[lang] = {'count': 0, 'valid': 0, 'invalid': 0}
            languages[lang]['count'] += 1
            if result.is_valid:
                languages[lang]['valid'] += 1
            else:
                languages[lang]['invalid'] += 1
            
            # Accumulate metrics
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            total_size += result.file_size
            total_lines += result.line_count
        
        return {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'validation_rate': valid_files / total_files if total_files > 0 else 0,
            'languages': languages,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'total_size_mb': total_size / (1024 * 1024),
            'total_lines': total_lines,
            'avg_file_size_kb': (total_size / 1024) / total_files if total_files > 0 else 0,
            'avg_lines_per_file': total_lines / total_files if total_files > 0 else 0
        }

