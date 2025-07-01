"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import ast
import importlib.util
import logging
import os
import subprocess
import sys

Code Validation System
Validates all code files in the Graph-Sitter project for syntax, imports, and functionality
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class CodeIssue:
    """Represents a code validation issue"""
    file_path: str
    line_number: Optional[int]
    severity: ValidationSeverity
    issue_type: str
    message: str
    suggestion: Optional[str] = None

class CodeValidator:
    """Comprehensive code validation system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues: List[CodeIssue] = []
        self.validated_files: Set[str] = set()
        
        # Define validation patterns
        self.python_extensions = {'.py'}
        self.sql_extensions = {'.sql'}
        self.config_extensions = {'.json', '.yaml', '.yml', '.toml'}
        
        # Import validation patterns
        self.expected_imports = {
            'src/graph_sitter': ['graph_sitter'],
            'src/codegen': ['codegen'],
            'src/contexten': ['contexten']
        }
        
        # Exclude patterns
        self.exclude_patterns = {
            '__pycache__',
            '.git',
            '.pytest_cache',
            'node_modules',
            '.venv',
            'venv',
            '.env'
        }
    
    def validate_all(self) -> Tuple[bool, List[CodeIssue]]:
        """Run comprehensive code validation"""
        logger.info("Starting comprehensive code validation...")
        
        # Clear previous results
        self.issues = []
        self.validated_files = set()
        
        # Run validation checks
        self._validate_python_files()
        self._validate_sql_files()
        self._validate_import_structure()
        self._validate_module_structure()
        self._validate_configuration_files()
        self._validate_dependencies()
        self._run_syntax_checks()
        
        # Determine overall success
        has_critical_errors = any(
            issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR] 
            for issue in self.issues
        )
        
        logger.info(f"Code validation completed. Found {len(self.issues)} issues.")
        return not has_critical_errors, self.issues
    
    def _validate_python_files(self):
        """Validate Python files for syntax and basic structure"""
        logger.info("Validating Python files...")
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_exclude_file(file_path):
                continue
                
            self.validated_files.add(str(file_path))
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST for syntax validation
                try:
                    tree = ast.parse(content, filename=str(file_path))
                    self._analyze_ast(file_path, tree, content)
                    
                except SyntaxError as e:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=e.lineno,
                        severity=ValidationSeverity.ERROR,
                        issue_type="syntax_error",
                        message=f"Syntax error: {e.msg}",
                        suggestion="Fix the syntax error before proceeding"
                    ))
                
                # Check for common issues
                self._check_python_best_practices(file_path, content)
                
            except Exception as e:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=None,
                    severity=ValidationSeverity.ERROR,
                    issue_type="file_error",
                    message=f"Cannot read file: {str(e)}",
                    suggestion="Check file permissions and encoding"
                ))
    
    def _validate_sql_files(self):
        """Validate SQL files for basic syntax"""
        logger.info("Validating SQL files...")
        
        sql_files = list(self.project_root.rglob("*.sql"))
        
        for file_path in sql_files:
            if self._should_exclude_file(file_path):
                continue
                
            self.validated_files.add(str(file_path))
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic SQL validation
                self._check_sql_syntax(file_path, content)
                
            except Exception as e:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=None,
                    severity=ValidationSeverity.ERROR,
                    issue_type="file_error",
                    message=f"Cannot read SQL file: {str(e)}",
                    suggestion="Check file permissions and encoding"
                ))
    
    def _validate_import_structure(self):
        """Validate import structure and dependencies"""
        logger.info("Validating import structure...")
        
        # Check for circular imports
        self._detect_circular_imports()
        
        # Check for missing imports
        self._check_missing_imports()
        
        # Check for incorrect import paths
        self._check_import_paths()
    
    def _validate_module_structure(self):
        """Validate module structure and organization"""
        logger.info("Validating module structure...")
        
        # Check for required __init__.py files
        self._check_init_files()
        
        # Check module naming conventions
        self._check_naming_conventions()
        
        # Check for duplicate functionality
        self._check_duplicate_functions()
    
    def _validate_configuration_files(self):
        """Validate configuration files"""
        logger.info("Validating configuration files...")
        
        config_files = []
        for ext in self.config_extensions:
            config_files.extend(self.project_root.rglob(f"*{ext}"))
        
        for file_path in config_files:
            if self._should_exclude_file(file_path):
                continue
                
            self._validate_config_file(file_path)
    
    def _validate_dependencies(self):
        """Validate dependencies and imports"""
        logger.info("Validating dependencies...")
        
        # Check requirements.txt if exists
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            self._validate_requirements_file(requirements_file)
        
        # Check pyproject.toml if exists
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            self._validate_pyproject_file(pyproject_file)
    
    def _run_syntax_checks(self):
        """Run additional syntax checks using external tools"""
        logger.info("Running syntax checks...")
        
        # Try to run flake8 if available
        try:
            result = subprocess.run(
                ['flake8', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._run_flake8_check()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.issues.append(CodeIssue(
                file_path="",
                line_number=None,
                severity=ValidationSeverity.INFO,
                issue_type="tool_missing",
                message="flake8 not available for additional syntax checking",
                suggestion="Install flake8: pip install flake8"
            ))
    
    def _analyze_ast(self, file_path: Path, tree: ast.AST, content: str):
        """Analyze AST for potential issues"""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['os', 'subprocess', 'eval', 'exec']:
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            severity=ValidationSeverity.WARNING,
                            issue_type="dangerous_import",
                            message=f"Potentially dangerous import: {alias.name}",
                            suggestion="Ensure this import is necessary and used safely"
                        ))
            
            # Check for TODO/FIXME comments
            if hasattr(node, 'lineno') and node.lineno <= len(lines):
                line = lines[node.lineno - 1]
                if 'TODO' in line or 'FIXME' in line:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        severity=ValidationSeverity.INFO,
                        issue_type="todo_comment",
                        message="TODO/FIXME comment found",
                        suggestion="Consider addressing this comment"
                    ))
    
    def _check_python_best_practices(self, file_path: Path, content: str):
        """Check Python best practices"""
        lines = content.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    severity=ValidationSeverity.WARNING,
                    issue_type="long_line",
                    message=f"Line too long ({len(line)} characters)",
                    suggestion="Consider breaking long lines for better readability"
                ))
        
        # Check for missing docstrings in functions/classes
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            severity=ValidationSeverity.INFO,
                            issue_type="missing_docstring",
                            message=f"Missing docstring for {node.name}",
                            suggestion="Add docstring for better documentation"
                        ))
        except:
            pass  # Already handled in syntax validation
    
    def _check_sql_syntax(self, file_path: Path, content: str):
        """Basic SQL syntax checking"""
        lines = content.split('\n')
        
        # Check for common SQL issues
        for i, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            # Check for missing semicolons at end of statements
            if (line_lower.startswith(('select', 'insert', 'update', 'delete', 'create', 'drop')) 
                and not line_lower.endswith(';') 
                and not line_lower.endswith('\\')
                and i == len(lines)):
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    severity=ValidationSeverity.WARNING,
                    issue_type="missing_semicolon",
                    message="SQL statement may be missing semicolon",
                    suggestion="Add semicolon at end of SQL statements"
                ))
            
            # Check for SQL injection patterns
            if 'concat(' in line_lower and ('||' in line_lower or '+' in line_lower):
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    severity=ValidationSeverity.WARNING,
                    issue_type="sql_injection_risk",
                    message="Potential SQL injection risk with string concatenation",
                    suggestion="Use parameterized queries instead"
                ))
    
    def _detect_circular_imports(self):
        """Detect circular import dependencies"""
        # This is a simplified version - a full implementation would build a dependency graph
        python_files = list(self.project_root.rglob("*.py"))
        import_graph = {}
        
        for file_path in python_files:
            if self._should_exclude_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                import_graph[str(file_path)] = imports
                
            except:
                continue
        
        # Simple circular import detection (this could be more sophisticated)
        for file_path, imports in import_graph.items():
            for imported_module in imports:
                if imported_module in import_graph:
                    if file_path in import_graph[imported_module]:
                        self.issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=None,
                            severity=ValidationSeverity.ERROR,
                            issue_type="circular_import",
                            message=f"Potential circular import with {imported_module}",
                            suggestion="Restructure imports to avoid circular dependencies"
                        ))
    
    def _check_missing_imports(self):
        """Check for missing imports"""
        # This would require more sophisticated analysis
        pass
    
    def _check_import_paths(self):
        """Check for incorrect import paths"""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_exclude_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for incorrect relative imports
                if 'from codegen import codebase' in content and 'graph_sitter' in str(file_path):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=None,
                        severity=ValidationSeverity.ERROR,
                        issue_type="incorrect_import",
                        message="Incorrect import: codebase should be imported from graph_sitter",
                        suggestion="Change to: from graph_sitter import codebase"
                    ))
                
                if 'from graph_sitter import' in content and any(x in content for x in ['linear', 'github', 'slack']):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=None,
                        severity=ValidationSeverity.ERROR,
                        issue_type="incorrect_import",
                        message="Incorrect import: linear/github/slack should be imported from contexten",
                        suggestion="Change to: from contexten import linear/github/slack"
                    ))
                    
            except:
                continue
    
    def _check_init_files(self):
        """Check for required __init__.py files"""
        required_init_dirs = [
            'src/graph_sitter',
            'src/codegen',
            'src/contexten',
            'src/validation'
        ]
        
        for dir_path in required_init_dirs:
            init_file = self.project_root / dir_path / '__init__.py'
            if not init_file.exists():
                self.issues.append(CodeIssue(
                    file_path=str(init_file),
                    line_number=None,
                    severity=ValidationSeverity.WARNING,
                    issue_type="missing_init",
                    message=f"Missing __init__.py in {dir_path}",
                    suggestion=f"Create __init__.py file in {dir_path}"
                ))
    
    def _check_naming_conventions(self):
        """Check naming conventions"""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_exclude_file(file_path):
                continue
                
            # Check file naming (should be snake_case)
            filename = file_path.stem
            if filename != filename.lower() or '-' in filename:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=None,
                    severity=ValidationSeverity.WARNING,
                    issue_type="naming_convention",
                    message=f"File name should use snake_case: {filename}",
                    suggestion="Rename file to use snake_case convention"
                ))
    
    def _check_duplicate_functions(self):
        """Check for duplicate function definitions"""
        # This would require more sophisticated analysis
        pass
    
    def _validate_config_file(self, file_path: Path):
        """Validate configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.suffix == '.json':
                import json
                json.loads(content)
            elif file_path.suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    yaml.safe_load(content)
                except ImportError:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=None,
                        severity=ValidationSeverity.INFO,
                        issue_type="missing_dependency",
                        message="PyYAML not available for YAML validation",
                        suggestion="Install PyYAML: pip install PyYAML"
                    ))
            elif file_path.suffix == '.toml':
                try:
                    import tomli
                    tomli.loads(content)
                except ImportError:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=None,
                        severity=ValidationSeverity.INFO,
                        issue_type="missing_dependency",
                        message="tomli not available for TOML validation",
                        suggestion="Install tomli: pip install tomli"
                    ))
                    
        except Exception as e:
            self.issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=None,
                severity=ValidationSeverity.ERROR,
                issue_type="config_error",
                message=f"Configuration file error: {str(e)}",
                suggestion="Fix configuration file syntax"
            ))
    
    def _validate_requirements_file(self, file_path: Path):
        """Validate requirements.txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Basic package name validation
                    if not line.replace('-', '').replace('_', '').replace('.', '').replace('=', '').replace('>', '').replace('<', '').replace('!', '').replace('[', '').replace(']', '').replace(',', '').replace(' ', '').isalnum():
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i,
                            severity=ValidationSeverity.WARNING,
                            issue_type="invalid_requirement",
                            message=f"Potentially invalid requirement: {line}",
                            suggestion="Check requirement format"
                        ))
                        
        except Exception as e:
            self.issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=None,
                severity=ValidationSeverity.ERROR,
                issue_type="file_error",
                message=f"Cannot read requirements file: {str(e)}",
                suggestion="Check file permissions and format"
            ))
    
    def _validate_pyproject_file(self, file_path: Path):
        """Validate pyproject.toml file"""
        try:
            import tomli
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
            
            # Check for required sections
            if 'project' not in data and 'tool' not in data:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=None,
                    severity=ValidationSeverity.WARNING,
                    issue_type="missing_section",
                    message="pyproject.toml missing [project] or [tool] section",
                    suggestion="Add required sections to pyproject.toml"
                ))
                
        except ImportError:
            self.issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=None,
                severity=ValidationSeverity.INFO,
                issue_type="missing_dependency",
                message="tomli not available for pyproject.toml validation",
                suggestion="Install tomli: pip install tomli"
            ))
        except Exception as e:
            self.issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=None,
                severity=ValidationSeverity.ERROR,
                issue_type="config_error",
                message=f"pyproject.toml error: {str(e)}",
                suggestion="Fix pyproject.toml syntax"
            ))
    
    def _run_flake8_check(self):
        """Run flake8 for additional syntax checking"""
        try:
            result = subprocess.run(
                ['flake8', '--max-line-length=120', '--exclude=__pycache__,.git', str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            file_path, line_num, col, message = parts
                            self.issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=int(line_num) if line_num.isdigit() else None,
                                severity=ValidationSeverity.WARNING,
                                issue_type="flake8",
                                message=f"flake8: {message.strip()}",
                                suggestion="Fix the style issue"
                            ))
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            self.issues.append(CodeIssue(
                file_path="",
                line_number=None,
                severity=ValidationSeverity.WARNING,
                issue_type="tool_error",
                message=f"flake8 check failed: {str(e)}",
                suggestion="Check flake8 installation and configuration"
            ))
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from validation"""
        return any(pattern in str(file_path) for pattern in self.exclude_patterns)
    
    def print_results(self):
        """Print validation results in a formatted way"""
        if not self.issues:
            print("✅ No code validation issues found!")
            return
        
        # Group by severity
        critical = [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        info = [i for i in self.issues if i.severity == ValidationSeverity.INFO]
        
        # Print critical issues
        if critical:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in critical:
                print(f"  {issue.file_path}:{issue.line_number or '?'} - {issue.message}")
                if issue.suggestion:
                    print(f"    💡 {issue.suggestion}")
        
        # Print errors
        if errors:
            print("\n❌ ERRORS:")
            for issue in errors:
                print(f"  {issue.file_path}:{issue.line_number or '?'} - {issue.message}")
                if issue.suggestion:
                    print(f"    💡 {issue.suggestion}")
        
        # Print warnings
        if warnings:
            print("\n⚠️  WARNINGS:")
            for issue in warnings:
                print(f"  {issue.file_path}:{issue.line_number or '?'} - {issue.message}")
                if issue.suggestion:
                    print(f"    💡 {issue.suggestion}")
        
        # Print info
        if info:
            print("\n📋 INFO:")
            for issue in info:
                print(f"  {issue.file_path}:{issue.line_number or '?'} - {issue.message}")
                if issue.suggestion:
                    print(f"    💡 {issue.suggestion}")
        
        # Summary
        print(f"\n📊 SUMMARY: {len(critical)} critical, {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        print(f"📁 FILES VALIDATED: {len(self.validated_files)}")

def main():
    """Main validation entry point"""
    print("🔍 Graph-Sitter Code Validator")
    print("=" * 50)
    
    validator = CodeValidator()
    success, issues = validator.validate_all()
    
    validator.print_results()
    
    if success:
        print("\n✅ All critical code validations passed!")
        return 0
    else:
        print("\n❌ Code validation failed - please fix the critical issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
