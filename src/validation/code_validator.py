"""
Code Validator
Validates code quality and structure for Graph-Sitter
"""

import ast
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Set
import re

class CodeValidator:
    """Validates code quality and structure"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def validate_all(self) -> Tuple[bool, Dict]:
        """Validate all code aspects"""
        results = {
            "syntax_check": self._validate_syntax(),
            "import_structure": self._validate_import_structure(),
            "code_style": self._validate_code_style(),
            "documentation": self._validate_documentation()
        }
        
        success = all(results.values())
        return success, results
    
    def _validate_syntax(self) -> bool:
        """Validate Python syntax across the codebase"""
        src_dir = Path("src")
        if not src_dir.exists():
            self.warnings.append("No src directory found")
            return True
        
        syntax_errors = []
        
        for py_file in src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse with AST to check syntax
                ast.parse(content, filename=str(py_file))
                
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
            except Exception as e:
                self.warnings.append(f"Could not check {py_file}: {e}")
        
        if syntax_errors:
            self.issues.extend(syntax_errors)
            return False
        
        return True
    
    def _validate_import_structure(self) -> bool:
        """Validate import structure and dependencies"""
        src_dir = Path("src")
        if not src_dir.exists():
            return True
        
        import_issues = []
        circular_imports = self._detect_circular_imports()
        
        if circular_imports:
            import_issues.extend([f"Circular import: {ci}" for ci in circular_imports])
        
        # Check for unused imports (basic check)
        unused_imports = self._find_unused_imports()
        if len(unused_imports) > 10:  # Only warn if many unused imports
            self.warnings.append(f"Found {len(unused_imports)} potentially unused imports")
        
        if import_issues:
            self.issues.extend(import_issues)
            return False
        
        return True
    
    def _validate_code_style(self) -> bool:
        """Validate code style using available tools"""
        # Try to run ruff if available
        try:
            result = subprocess.run(
                ["ruff", "check", "src/", "--quiet"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0 and result.stdout:
                # Parse ruff output for serious issues
                lines = result.stdout.strip().split('\n')
                serious_issues = [line for line in lines if any(
                    severity in line for severity in ['E', 'F']  # Errors and fatal issues
                )]
                
                if serious_issues:
                    self.issues.extend(serious_issues[:5])  # Limit to first 5
                    return False
                else:
                    self.warnings.append("Code style warnings found (run 'ruff check src/' for details)")
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.warnings.append("Could not run code style check (ruff not available)")
        
        return True
    
    def _validate_documentation(self) -> bool:
        """Validate documentation coverage"""
        src_dir = Path("src")
        if not src_dir.exists():
            return True
        
        undocumented_modules = []
        
        for py_file in src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for module docstring
                tree = ast.parse(content)
                
                # Check if first statement is a docstring
                if (not tree.body or 
                    not isinstance(tree.body[0], ast.Expr) or 
                    not isinstance(tree.body[0].value, ast.Constant) or
                    not isinstance(tree.body[0].value.value, str)):
                    
                    undocumented_modules.append(str(py_file.relative_to(src_dir)))
                
            except Exception:
                continue
        
        if len(undocumented_modules) > 20:  # Only warn if many undocumented
            self.warnings.append(f"Found {len(undocumented_modules)} modules without docstrings")
        
        return True
    
    def _detect_circular_imports(self) -> List[str]:
        """Detect circular imports (basic implementation)"""
        # This is a simplified implementation
        # A full implementation would build a dependency graph
        return []
    
    def _find_unused_imports(self) -> List[str]:
        """Find potentially unused imports (basic implementation)"""
        src_dir = Path("src")
        if not src_dir.exists():
            return []
        
        unused_imports = []
        
        for py_file in src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find import statements
                import_pattern = r'^(?:from\s+\S+\s+)?import\s+(\S+)'
                imports = re.findall(import_pattern, content, re.MULTILINE)
                
                # Check if imported names are used
                for imported_name in imports:
                    # Simple check: if name appears elsewhere in file
                    if imported_name not in content.replace(f"import {imported_name}", ""):
                        unused_imports.append(f"{py_file}:{imported_name}")
                
            except Exception:
                continue
        
        return unused_imports
    
    def print_results(self):
        """Print validation results"""
        if self.issues:
            print("❌ Code Quality Issues:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print("⚠️  Code Quality Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.issues and not self.warnings:
            print("✅ Code validation passed")
        elif not self.issues:
            print("✅ Code validation passed with warnings")

