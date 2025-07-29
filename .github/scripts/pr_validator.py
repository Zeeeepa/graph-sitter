#!/usr/bin/env python3
"""
Automated PR Validator using Graph-Sitter
This script validates PR changes to ensure:
- Functions/classes are properly implemented
- Parameters are correctly defined and used
- Dependencies are valid and resolvable
- No broken references or missing imports
- Code structure integrity is maintained

Specifically adapted for the graph-sitter repository.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add the src directory to the path to import graph_sitter modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Graph-sitter imports
try:
    from graph_sitter import Codebase
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    from graph_sitter.codebase.validation import post_init_validation, PostInitValidationStatus

    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    symbol_name: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    summary: Dict[str, int]

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.is_valid = False

        # Update summary
        key = f"{issue.severity.value}s"
        self.summary[key] = self.summary.get(key, 0) + 1


class PRValidator:
    """Automated PR validator using graph-sitter analysis"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.codebase = None
        self.changed_files = []
        self.validation_result = ValidationResult(is_valid=True, issues=[], summary={})

    def validate_pr(self, pr_files: List[str] = None) -> ValidationResult:
        """Main validation entry point"""
        print("🔍 Starting PR validation...")

        if not GRAPH_SITTER_AVAILABLE:
            self.validation_result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="setup",
                    message="Graph-sitter not available",
                    file_path="system",
                )
            )
            return self.validation_result

        try:
            # Initialize codebase
            print("📊 Initializing codebase analysis...")
            self.codebase = Codebase(str(self.repo_path))

            # Run post-init validation from existing infrastructure
            validation_status = post_init_validation(self.codebase)
            if validation_status != PostInitValidationStatus.SUCCESS:
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="codebase_health",
                        message=f"Codebase validation status: {validation_status.value}",
                        file_path="system",
                        suggestion="Check codebase integrity and import resolution",
                    )
                )

            # Get changed files
            self.changed_files = pr_files or self._get_changed_files()
            print(f"📝 Validating {len(self.changed_files)} changed files...")

            # Run validation checks
            self._validate_file_structure()
            self._validate_function_implementations()
            self._validate_class_implementations()
            self._validate_imports_and_dependencies()
            self._validate_graph_sitter_specific_patterns()
            self._validate_architectural_integrity()

            print(
                f"✅ Validation complete: {len(self.validation_result.issues)} issues found"
            )
            return self.validation_result

        except Exception as e:
            self.validation_result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="system",
                    message=f"Validation failed: {e}",
                    file_path="system",
                )
            )
            return self.validation_result

    def _get_changed_files(self) -> List[str]:
        """Get list of files changed in the PR"""
        try:
            # Try different git commands to get changed files
            commands = [
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                ["git", "diff", "--name-only", "origin/develop..HEAD"],
                ["git", "diff", "--name-only", "develop..HEAD"],
                ["git", "diff", "--name-only", "--cached"],
                ["git", "ls-files", "--modified"],
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=self.repo_path,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        files = [f for f in result.stdout.strip().split("\n") if f.strip()]
                        if files:
                            print(f"📁 Found {len(files)} changed files using: {' '.join(cmd)}")
                            return files
                except Exception:
                    continue
            
            # Fallback: analyze all Python files in src directory
            print("⚠️ Could not detect changed files, analyzing src Python files...")
            python_files = []
            src_path = self.repo_path / "src"
            if src_path.exists():
                python_files.extend(src_path.rglob("*.py"))
            
            return [str(f.relative_to(self.repo_path)) for f in python_files[:30]]  # Limit to 30 files
            
        except Exception as e:
            print(f"⚠️ Could not detect changed files: {e}")
            return []

    def _validate_file_structure(self):
        """Validate file structure and syntax"""
        print("📁 Validating file structure...")

        for file_path in self.changed_files:
            full_path = self.repo_path / file_path

            # Check if file exists
            if not full_path.exists():
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="file_structure",
                        message="File does not exist",
                        file_path=file_path,
                    )
                )
                continue

            # Check if file is parseable
            try:
                if file_path.endswith(".py"):
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    compile(content, file_path, "exec")
                    
                    # Check for graph-sitter specific patterns
                    self._check_graph_sitter_imports(content, file_path)
                    
            except SyntaxError as e:
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="syntax",
                        message=f"Syntax error: {e.msg}",
                        file_path=file_path,
                        line_number=e.lineno,
                    )
                )
            except Exception as e:
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="file_access",
                        message=f"Could not read file: {e}",
                        file_path=file_path,
                    )
                )

    def _check_graph_sitter_imports(self, content: str, file_path: str):
        """Check for proper graph-sitter import patterns"""
        lines = content.split('\n')
        
        # Check for TYPE_CHECKING imports
        has_type_checking = "from typing import TYPE_CHECKING" in content
        has_conditional_imports = "if TYPE_CHECKING:" in content
        
        # Look for graph_sitter imports that should be conditional
        heavy_imports = [
            "from rustworkx import",
            "from graph_sitter.core.codebase import CodebaseType"
        ]
        
        for i, line in enumerate(lines, 1):
            for heavy_import in heavy_imports:
                if heavy_import in line and not has_type_checking:
                    self.validation_result.add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category="import_optimization",
                            message=f"Consider using TYPE_CHECKING for heavy import: {heavy_import}",
                            file_path=file_path,
                            line_number=i,
                            suggestion="Use 'if TYPE_CHECKING:' for type-only imports to improve startup time",
                        )
                    )

    def _validate_function_implementations(self):
        """Validate function implementations in changed files"""
        print("🔧 Validating function implementations...")

        for file_path in self.changed_files:
            # Find the file in codebase
            source_file = self._find_source_file(file_path)
            if not source_file:
                continue

            if hasattr(source_file, 'functions'):
                for function in source_file.functions:
                    self._validate_function(function, file_path)

    def _validate_function(self, function: Function, file_path: str):
        """Validate a specific function"""
        if not hasattr(function, 'name'):
            return
        
        # Check if function has implementation
        if not hasattr(function, "code_block") or not function.code_block:
            # Skip abstract methods and interface definitions
            if not any(keyword in function.name for keyword in ["abstract", "interface", "protocol"]):
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="function_implementation",
                        message=f"Function '{function.name}' has no implementation",
                        file_path=file_path,
                        symbol_name=function.name,
                        suggestion="Add function body or mark as abstract",
                    )
                )
            return

        # Check parameters
        if hasattr(function, "parameters"):
            for param in function.parameters:
                self._validate_parameter(param, function, file_path)

        # Check for graph-sitter specific patterns
        self._validate_graph_sitter_function_patterns(function, file_path)

    def _validate_parameter(self, param, function: Function, file_path: str):
        """Validate function parameter"""
        if not hasattr(param, 'name'):
            return
        
        param_name = param.name
        
        # Skip common parameter patterns
        if param_name in ["self", "cls", "args", "kwargs"] or param_name.startswith("_"):
            return
        
        # Check if parameter is used in function body
        if hasattr(function, "code_block") and hasattr(function.code_block, "source"):
            function_source = function.code_block.source

            if param_name not in function_source:
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="unused_parameter",
                        message=f"Parameter '{param_name}' in function '{function.name}' is not used",
                        file_path=file_path,
                        symbol_name=function.name,
                        suggestion=f"Remove unused parameter or prefix with underscore: _{param_name}",
                    )
                )

    def _validate_graph_sitter_function_patterns(self, function: Function, file_path: str):
        """Validate graph-sitter specific function patterns"""
        if not hasattr(function, 'name') or not hasattr(function, 'code_block'):
            return
            
        function_name = function.name
        
        # Check for proper error handling in graph operations
        if any(keyword in function_name.lower() for keyword in ["sync", "reset", "init", "validate"]):
            if hasattr(function.code_block, "source"):
                source = function.code_block.source
                if "try:" not in source and "except" not in source:
                    self.validation_result.add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category="error_handling",
                            message=f"Graph operation function '{function_name}' should have error handling",
                            file_path=file_path,
                            symbol_name=function_name,
                            suggestion="Add try/except blocks for robust graph operations",
                        )
                    )

    def _validate_class_implementations(self):
        """Validate class implementations in changed files"""
        print("🏗️ Validating class implementations...")

        for file_path in self.changed_files:
            source_file = self._find_source_file(file_path)
            if not source_file:
                continue

            if hasattr(source_file, 'classes'):
                for cls in source_file.classes:
                    self._validate_class(cls, file_path)

    def _validate_class(self, cls: Class, file_path: str):
        """Validate a specific class"""
        if not hasattr(cls, 'name'):
            return
        
        # Check if class has methods
        if hasattr(cls, "methods") and len(cls.methods) == 0:
            # Skip dataclasses, enums, and other special classes
            if not any(keyword in cls.name.lower() for keyword in ["enum", "dataclass", "namedtuple", "config", "type"]):
                self.validation_result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="empty_class",
                        message=f"Class '{cls.name}' has no methods",
                        file_path=file_path,
                        symbol_name=cls.name,
                        suggestion="Add methods or consider using a dataclass/namedtuple",
                    )
                )

        # Validate methods
        if hasattr(cls, "methods"):
            for method in cls.methods:
                self._validate_function(method, file_path)

    def _validate_imports_and_dependencies(self):
        """Validate imports and dependencies"""
        print("📦 Validating imports and dependencies...")

        for file_path in self.changed_files:
            source_file = self._find_source_file(file_path)
            if not source_file:
                continue

            if hasattr(source_file, "imports"):
                for import_stmt in source_file.imports:
                    self._validate_import(import_stmt, file_path)

    def _validate_import(self, import_stmt: Import, file_path: str):
        """Validate a specific import"""
        if not hasattr(import_stmt, "module_name"):
            return

        module_name = import_stmt.module_name

        # Skip validation for known good modules
        known_modules = {
            "os", "sys", "json", "time", "datetime", "pathlib", "typing", "dataclasses",
            "enum", "collections", "itertools", "functools", "operator", "re", "math",
            "random", "uuid", "hashlib", "base64", "urllib", "http", "socket", "threading",
            "multiprocessing", "subprocess", "logging", "warnings", "traceback", "inspect",
            "ast", "importlib", "pkgutil", "unittest", "pytest", "numpy", "pandas",
            "requests", "flask", "django", "fastapi", "pydantic", "sqlalchemy", "click",
            "rich", "typer", "openai", "anthropic", "langchain", "graph_sitter", "rustworkx",
            "tabulate", "tree_sitter"
        }
        
        # Check if it's a known module or local import
        if (module_name.split('.')[0] in known_modules or 
            module_name.startswith('.') or 
            module_name.startswith('graph_sitter')):
            return

        # Check if imported module exists
        if not self._module_exists(module_name):
            self.validation_result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="missing_import",
                    message=f"Imported module '{module_name}' cannot be resolved",
                    file_path=file_path,
                    suggestion=f"Install package containing '{module_name}' or fix import path",
                )
            )

    def _validate_graph_sitter_specific_patterns(self):
        """Validate graph-sitter specific code patterns"""
        print("🎯 Validating graph-sitter specific patterns...")
        
        for file_path in self.changed_files:
            if not file_path.endswith('.py'):
                continue
                
            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper logging usage
                if 'logger' in content and 'get_logger' not in content:
                    self.validation_result.add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category="logging_pattern",
                            message="Consider using graph_sitter.shared.logging.get_logger for consistent logging",
                            file_path=file_path,
                            suggestion="Import and use get_logger(__name__) for consistent logging patterns",
                        )
                    )
                
                # Check for proper codebase context usage
                if 'codebase.ctx' in content and 'TYPE_CHECKING' not in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'codebase.ctx' in line and 'if' not in line.lower():
                            self.validation_result.add_issue(
                                ValidationIssue(
                                    severity=ValidationSeverity.INFO,
                                    category="context_usage",
                                    message="Direct codebase.ctx access should be used carefully",
                                    file_path=file_path,
                                    line_number=i,
                                    suggestion="Consider using codebase methods instead of direct ctx access",
                                )
                            )
                            break
                            
            except Exception as e:
                # Skip files that can't be read
                pass

    def _validate_architectural_integrity(self):
        """Validate architectural integrity and patterns"""
        print("🏛️ Validating architectural integrity...")

        # Check for proper module organization
        self._check_module_organization()

    def _check_module_organization(self):
        """Check basic module organization patterns"""
        for file_path in self.changed_files:
            if file_path.endswith('.py'):
                # Check for proper module structure in src/graph_sitter
                if file_path.startswith('src/graph_sitter/'):
                    parts = file_path.split('/')
                    if len(parts) > 6:  # src/graph_sitter/module/submodule/file.py = 5 parts
                        self.validation_result.add_issue(
                            ValidationIssue(
                                severity=ValidationSeverity.INFO,
                                category="module_organization",
                                message=f"File '{file_path}' is deeply nested ({len(parts)} levels)",
                                file_path=file_path,
                                suggestion="Consider flattening the module structure",
                            )
                        )

    # Helper methods
    def _find_source_file(self, file_path: str) -> Optional[SourceFile]:
        """Find source file in codebase"""
        if not self.codebase or not hasattr(self.codebase, 'files'):
            return None
        
        for file in self.codebase.files:
            if hasattr(file, "path") and str(file.path).endswith(file_path):
                return file
        return None

    def _module_exists(self, module_name: str) -> bool:
        """Check if module exists"""
        # Check internal modules
        if self.codebase and hasattr(self.codebase, 'files'):
            for file in self.codebase.files:
                if hasattr(file, "path"):
                    file_path = str(file.path)
                    if module_name.replace(".", "/") in file_path:
                        return True

        # Try importing (for external packages)
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False


def generate_validation_report(result: ValidationResult) -> str:
    """Generate a comprehensive validation report"""
    report = f"""# 🔍 PR Validation Report

## Summary
- Status: {"✅ PASSED" if result.is_valid else "❌ FAILED"}
- Total Issues: {len(result.issues)}
- Errors: {result.summary.get("errors", 0)}
- Warnings: {result.summary.get("warnings", 0)}
- Info: {result.summary.get("infos", 0)}

## Issues by Category
"""

    # Group issues by category
    categories = {}
    for issue in result.issues:
        if issue.category not in categories:
            categories[issue.category] = []
        categories[issue.category].append(issue)

    for category, issues in categories.items():
        report += f"\n### {category.replace('_', ' ').title()}\n"
        for issue in issues:
            severity_icon = {
                ValidationSeverity.ERROR: "❌",
                ValidationSeverity.WARNING: "⚠️",
                ValidationSeverity.INFO: "ℹ️",
            }[issue.severity]

            report += f"- {severity_icon} **{issue.file_path}**"
            if issue.line_number:
                report += f":{issue.line_number}"
            if issue.symbol_name:
                report += f" ({issue.symbol_name})"
            report += f": {issue.message}\n"

            if issue.suggestion:
                report += f"  💡 *Suggestion: {issue.suggestion}*\n"

    if not result.issues:
        report += "\n🎉 No issues found! Your code looks great!\n"

    return report


def main():
    """Main validation function for CI/CD"""
    print("🚀 Graph-Sitter PR Validator")
    print("=" * 50)

    # Get environment variables
    repo_path = os.getenv("GITHUB_WORKSPACE", ".")
    pr_number = os.getenv("GITHUB_PR_NUMBER")

    # Initialize validator
    validator = PRValidator(repo_path)

    # Run validation
    result = validator.validate_pr()

    # Generate report
    report = generate_validation_report(result)
    print(report)

    # Save report for CI/CD
    with open("pr_validation_report.md", "w") as f:
        f.write(report)

    # Save JSON for programmatic access
    with open("pr_validation_result.json", "w") as f:
        json.dump(
            {
                "is_valid": result.is_valid,
                "summary": result.summary,
                "issues": [asdict(issue) for issue in result.issues],
            },
            f,
            indent=2,
            default=str,
        )

    # Exit with appropriate code
    if result.is_valid:
        print("\n✅ PR validation passed!")
        sys.exit(0)
    else:
        print(
            f"\n❌ PR validation failed with {result.summary.get('errors', 0)} errors"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

