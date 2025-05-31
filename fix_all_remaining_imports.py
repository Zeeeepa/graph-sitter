#!/usr/bin/env python3
"""
Comprehensive codemod to fix ALL remaining import issues.
This script fixes systematic import errors where contexten.sdk.*, contexten.shared.*, 
and contexten.core.* imports should be graph_sitter.* imports.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List


class ComprehensiveImportFixer:
    def __init__(self):
        self.fixes_applied = 0
        self.files_processed = 0
        
        # Define the correct import mappings
        self.import_mappings = {
            # SDK imports should go to graph_sitter
            r'from contexten\.sdk\.core\.directory import': 'from graph_sitter.core.directory import',
            r'from contexten\.sdk\.ai\.utils import': 'from graph_sitter.ai.utils import',
            r'from contexten\.sdk\.core\.external_module import': 'from graph_sitter.core.external_module import',
            r'from contexten\.sdk\.core\.import_resolution import': 'from graph_sitter.core.import_resolution import',
            r'from contexten\.sdk\.core\.symbol import': 'from graph_sitter.core.symbol import',
            r'from contexten\.sdk\.core\.statements\.if_block_statement import': 'from graph_sitter.core.statements.if_block_statement import',
            r'from contexten\.sdk\.enums import': 'from graph_sitter.enums import',
            r'from contexten\.sdk\.core\.statements\.statement import': 'from graph_sitter.core.statements.statement import',
            r'from contexten\.sdk\.core\.codebase import': 'from graph_sitter.core.codebase import',
            
            # Shared imports should go to graph_sitter
            r'from contexten\.shared\.logging\.get_logger import': 'from graph_sitter.shared.logging.get_logger import',
            r'from contexten\.shared\.enums\.programming_language import': 'from graph_sitter.shared.enums.programming_language import',
            
            # Core imports should go to graph_sitter
            r'from contexten\.core\.': 'from graph_sitter.core.',
            
            # Codebase imports should be from graph_sitter (not contexten)
            r'from contexten import Codebase': 'from graph_sitter import Codebase',
        }
    
    def fix_all_files(self):
        """Fix import statements in all relevant files."""
        print("🔧 Fixing ALL remaining import statements...")
        
        # Find all Python and Jupyter notebook files
        file_patterns = ['**/*.py', '**/*.ipynb']
        all_files = []
        
        for pattern in file_patterns:
            all_files.extend(Path('.').glob(pattern))
        
        for file_path in all_files:
            if '.git' in str(file_path) or 'node_modules' in str(file_path):
                continue
            if 'fix_' in str(file_path):  # Skip our own fix scripts
                continue
                
            try:
                if file_path.suffix == '.ipynb':
                    self._fix_jupyter_notebook(file_path)
                else:
                    self._fix_python_file(file_path)
                    
            except Exception as e:
                print(f"  ⚠️ Error fixing {file_path}: {e}")
    
    def _fix_python_file(self, file_path: Path):
        """Fix imports in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            content = self._fix_content_imports(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed imports in {file_path}")
                self.fixes_applied += 1
            
            self.files_processed += 1
                
        except Exception as e:
            print(f"  ⚠️ Error fixing Python file {file_path}: {e}")
    
    def _fix_jupyter_notebook(self, file_path: Path):
        """Fix imports in a Jupyter notebook file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            original_notebook = json.dumps(notebook, sort_keys=True)
            
            # Fix imports in all code cells
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        # Join lines, fix imports, then split back
                        content = ''.join(source)
                        fixed_content = self._fix_content_imports(content)
                        if fixed_content != content:
                            # Split back into lines, preserving original format
                            cell['source'] = fixed_content.splitlines(keepends=True)
            
            new_notebook = json.dumps(notebook, sort_keys=True)
            
            if new_notebook != original_notebook:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(notebook, f, indent=1)
                print(f"  ✅ Fixed imports in {file_path}")
                self.fixes_applied += 1
            
            self.files_processed += 1
                
        except Exception as e:
            print(f"  ⚠️ Error fixing Jupyter notebook {file_path}: {e}")
    
    def _fix_content_imports(self, content: str) -> str:
        """Fix imports in content using the mapping rules."""
        for pattern, replacement in self.import_mappings.items():
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def analyze_remaining_issues(self):
        """Analyze what import issues remain after fixes."""
        print("\n🔍 Analyzing remaining import issues...")
        
        remaining_issues = []
        
        # Find all Python and Jupyter notebook files
        file_patterns = ['**/*.py', '**/*.ipynb']
        all_files = []
        
        for pattern in file_patterns:
            all_files.extend(Path('.').glob(pattern))
        
        for file_path in all_files:
            if '.git' in str(file_path) or 'node_modules' in str(file_path):
                continue
            if 'fix_' in str(file_path):  # Skip our own fix scripts
                continue
                
            try:
                if file_path.suffix == '.ipynb':
                    content = self._get_notebook_content(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    # Check for problematic patterns
                    if re.search(r'from contexten\.sdk', line):
                        remaining_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'contexten.sdk import'
                        })
                    elif re.search(r'from contexten\.shared', line):
                        remaining_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'contexten.shared import'
                        })
                    elif re.search(r'from contexten\.core', line):
                        remaining_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'contexten.core import'
                        })
                        
            except Exception as e:
                print(f"  ⚠️ Error analyzing {file_path}: {e}")
        
        if remaining_issues:
            print(f"  🚨 Found {len(remaining_issues)} remaining issues:")
            for issue in remaining_issues:
                print(f"    📁 {issue['file']}:{issue['line']} - {issue['content']}")
        else:
            print("  🎉 No remaining import issues found!")
        
        return remaining_issues
    
    def _get_notebook_content(self, file_path: Path) -> str:
        """Extract content from Jupyter notebook for analysis."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            content_lines = []
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        content_lines.extend(source)
            
            return ''.join(content_lines)
        except:
            return ""


def main():
    print("🚀 Starting comprehensive import fixes...")
    
    fixer = ComprehensiveImportFixer()
    
    # Apply fixes
    fixer.fix_all_files()
    
    print(f"\n✅ Processed {fixer.files_processed} files, applied {fixer.fixes_applied} fixes!")
    
    # Check for remaining issues
    remaining = fixer.analyze_remaining_issues()
    
    if not remaining:
        print("\n🎉 All import issues resolved!")
    else:
        print(f"\n⚠️ {len(remaining)} issues may need manual review")


if __name__ == "__main__":
    main()

