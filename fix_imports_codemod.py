#!/usr/bin/env python3
"""
Codemod to fix import issues after renaming codegen to contexten.
This script analyzes the codebase and fixes imports systematically.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportAnalyzer:
    def __init__(self, src_dir: str = "./src"):
        self.src_dir = Path(src_dir)
        self.graph_sitter_modules = set()
        self.contexten_modules = set()
        self.import_issues = []
        
    def analyze_module_structure(self):
        """Analyze what modules exist in graph_sitter vs contexten."""
        print("🔍 Analyzing module structure...")
        
        # Find all Python modules in graph_sitter
        graph_sitter_dir = self.src_dir / "graph_sitter"
        if graph_sitter_dir.exists():
            for py_file in graph_sitter_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    rel_path = py_file.relative_to(graph_sitter_dir)
                    module_path = str(rel_path.with_suffix("")).replace("/", ".")
                    self.graph_sitter_modules.add(f"graph_sitter.{module_path}")
        
        # Find all Python modules in contexten
        contexten_dir = self.src_dir / "contexten"
        if contexten_dir.exists():
            for py_file in contexten_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    rel_path = py_file.relative_to(contexten_dir)
                    module_path = str(rel_path.with_suffix("")).replace("/", ".")
                    self.contexten_modules.add(f"contexten.{module_path}")
        
        print(f"  📦 Found {len(self.graph_sitter_modules)} graph_sitter modules")
        print(f"  📦 Found {len(self.contexten_modules)} contexten modules")
    
    def find_import_issues(self):
        """Find all import issues in Python files."""
        print("🔍 Scanning for import issues...")
        
        for py_file in Path(".").rglob("*.py"):
            if ".git" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find problematic imports
                issues = self._analyze_file_imports(py_file, content)
                if issues:
                    self.import_issues.extend(issues)
                    
            except Exception as e:
                print(f"  ⚠️ Error reading {py_file}: {e}")
        
        print(f"  🚨 Found {len(self.import_issues)} import issues")
    
    def _analyze_file_imports(self, file_path: Path, content: str) -> List[Dict]:
        """Analyze imports in a single file."""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for various import patterns that might be wrong
            if re.match(r'from\s+codegen\b', line):
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'still_using_codegen',
                    'content': line
                })
            
            # Check for imports that should be from graph_sitter
            if re.match(r'from\s+contexten.*\bCodebase\b', line):
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'codebase_from_contexten',
                    'content': line
                })
            
            # Check for PyCodebaseType imports from contexten (should be graph_sitter)
            if re.match(r'from\s+contexten.*\bPyCodebaseType\b', line):
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'py_codebase_type_from_contexten',
                    'content': line
                })
            
            # Check for incorrect CodegenApp imports
            if re.match(r'from\s+contexten\.extensions\.events\.app\s+import\s+CodegenApp', line):
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'incorrect_codegen_app_import',
                    'content': line
                })
            
            # Check for imports that might be from wrong module
            # Only flag this if the file is NOT in graph_sitter/extensions
            if re.match(r'from\s+graph_sitter\.extensions', line):
                # Skip if this file is within graph_sitter/extensions (internal imports are OK)
                if not str(file_path).startswith('./src/graph_sitter/extensions/'):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'issue': 'extensions_from_graph_sitter',
                        'content': line
                    })
        
        return issues
    
    def print_analysis(self):
        """Print analysis results."""
        print("\n📊 Import Issues Analysis:")
        
        issue_types = {}
        for issue in self.import_issues:
            issue_type = issue['issue']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        for issue_type, issues in issue_types.items():
            print(f"\n  🔴 {issue_type}: {len(issues)} occurrences")
            for issue in issues[:3]:  # Show first 3 examples
                print(f"    📁 {issue['file']}:{issue['line']} - {issue['content']}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")


class ImportFixer:
    def __init__(self):
        self.fixes_applied = 0
        
    def create_missing_init_files(self):
        """Create missing __init__.py files."""
        print("🔧 Creating missing __init__.py files...")
        
        # Create main contexten __init__.py
        contexten_init = Path("./src/contexten/__init__.py")
        if not contexten_init.exists():
            with open(contexten_init, 'w') as f:
                f.write('"""Contexten package - AI agent extensions and tools."""\n')
                f.write('from .extensions.events.codegen_app import CodegenApp\n')
                f.write('\n__all__ = ["CodegenApp"]\n')
            print("  ✅ Created src/contexten/__init__.py")
            self.fixes_applied += 1
        
        # Create main graph_sitter __init__.py if missing
        graph_sitter_init = Path("./src/graph_sitter/__init__.py")
        if not graph_sitter_init.exists():
            with open(graph_sitter_init, 'w') as f:
                f.write('"""Graph-sitter package - code analysis and manipulation."""\n')
                f.write('from .core.codebase import Codebase\n')
                f.write('\n__all__ = ["Codebase"]\n')
            print("  ✅ Created src/graph_sitter/__init__.py")
            self.fixes_applied += 1
    
    def fix_import_statements(self):
        """Fix import statements throughout the codebase."""
        print("🔧 Fixing import statements...")
        
        for py_file in Path(".").rglob("*.py"):
            if ".git" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply fixes based on file location
                content = self._fix_file_imports(py_file, content)
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed imports in {py_file}")
                    self.fixes_applied += 1
                    
            except Exception as e:
                print(f"  ⚠️ Error fixing {py_file}: {e}")
    
    def _fix_file_imports(self, file_path: Path, content: str) -> str:
        """Fix imports in file content."""
        lines = content.split('\n')
        fixed_lines = []
        
        # Check if this file is within graph_sitter/extensions
        is_internal_extension = str(file_path).startswith('./src/graph_sitter/extensions/')
        
        for line in lines:
            original_line = line
            
            # Fix: from codegen -> from contexten (but be careful about specific cases)
            if re.match(r'from\s+codegen\b', line):
                # Don't change if it's already been handled or is a special case
                if 'Codebase' in line:
                    # Codebase should come from graph_sitter
                    line = re.sub(r'from\s+codegen\b', 'from graph_sitter', line)
                else:
                    line = re.sub(r'from\s+codegen\b', 'from contexten', line)
            
            # Fix: import codegen -> import contexten
            if re.match(r'import\s+codegen\b', line):
                line = re.sub(r'import\s+codegen\b', 'import contexten', line)
            
            # Fix: Codebase imports should be from graph_sitter
            if re.match(r'from\s+contexten.*\bCodebase\b', line):
                # Extract just the Codebase import
                if 'import Codebase' in line:
                    line = 'from graph_sitter import Codebase'
            
            # Fix: PyCodebaseType imports should be from graph_sitter
            if re.match(r'from\s+contexten.*\bPyCodebaseType\b', line):
                # Extract just the PyCodebaseType import
                if 'import PyCodebaseType' in line:
                    line = 'from graph_sitter.core.codebase import PyCodebaseType'
            
            # Fix: incorrect CodegenApp imports
            if re.match(r'from\s+contexten\.extensions\.events\.app\s+import\s+CodegenApp', line):
                line = 'from contexten import CodegenApp'
            
            # Fix: Extensions should be from contexten, not graph_sitter
            # BUT: Don't change if we're inside graph_sitter/extensions (internal imports)
            if re.match(r'from\s+graph_sitter\.extensions', line) and not is_internal_extension:
                line = re.sub(r'from\s+graph_sitter\.extensions', 'from contexten.extensions', line)
            
            # Fix: configs should be from graph_sitter
            if re.match(r'from\s+contexten\.configs', line):
                line = re.sub(r'from\s+contexten\.configs', 'from graph_sitter.configs', line)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)


def main():
    print("🚀 Starting import analysis and fixes...")
    
    # Step 1: Analyze current state
    analyzer = ImportAnalyzer()
    analyzer.analyze_module_structure()
    analyzer.find_import_issues()
    analyzer.print_analysis()
    
    # Step 2: Apply fixes
    fixer = ImportFixer()
    fixer.create_missing_init_files()
    fixer.fix_import_statements()
    
    print(f"\n✅ Applied {fixer.fixes_applied} fixes!")
    print("🔍 Re-analyzing to check remaining issues...")
    
    # Step 3: Re-analyze to see what's left
    analyzer2 = ImportAnalyzer()
    analyzer2.find_import_issues()
    
    if analyzer2.import_issues:
        print(f"⚠️ {len(analyzer2.import_issues)} issues remain - may need manual review")
        analyzer2.print_analysis()
    else:
        print("🎉 All import issues resolved!")


if __name__ == "__main__":
    main()
