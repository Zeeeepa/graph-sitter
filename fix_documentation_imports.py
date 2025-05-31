#!/usr/bin/env python3
"""
Codemod to fix documentation import errors.
This script fixes systematic import errors in documentation files where
contexten.sdk.* and contexten.shared.* imports should be graph_sitter.* imports.
"""

import os
import re
from pathlib import Path
from typing import Dict, List


class DocumentationImportFixer:
    def __init__(self):
        self.fixes_applied = 0
        self.files_processed = 0
        
        # Define the correct import mappings
        self.import_mappings = {
            # SDK imports should go to graph_sitter
            r'from contexten\.sdk\.core\.interfaces\.callable import': 'from graph_sitter.core.interfaces.callable import',
            r'from contexten\.sdk\.core\.function import': 'from graph_sitter.core.function import',
            r'from contexten\.sdk\.core\.external_module import': 'from graph_sitter.core.external_module import',
            r'from contexten\.sdk\.codebase\.config import': 'from graph_sitter.codebase.config import',
            r'from contexten\.sdk import ExternalModule': 'from graph_sitter.core.external_module import ExternalModule',
            r'from contexten\.sdk\.core\.import_resolution import': 'from graph_sitter.core.import_resolution import',
            r'from contexten\.sdk\.core\.symbol import': 'from graph_sitter.core.symbol import',
            r'from contexten\.sdk\.core import': 'from graph_sitter.core import',
            
            # Shared imports should go to graph_sitter
            r'from contexten\.shared\.enums\.programming_language import': 'from graph_sitter.shared.enums.programming_language import',
            
            # Agent should be CodegenApp from contexten
            r'from contexten import Agent': 'from contexten import CodegenApp',
        }
    
    def fix_documentation_files(self):
        """Fix import statements in all documentation files."""
        print("🔧 Fixing documentation import statements...")
        
        # Find all documentation files
        doc_files = []
        for ext in ['*.md', '*.mdx']:
            doc_files.extend(Path('.').rglob(ext))
        
        for doc_file in doc_files:
            if '.git' in str(doc_file) or 'node_modules' in str(doc_file):
                continue
                
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                content = self._fix_file_imports(content)
                
                if content != original_content:
                    with open(doc_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed imports in {doc_file}")
                    self.fixes_applied += 1
                
                self.files_processed += 1
                    
            except Exception as e:
                print(f"  ⚠️ Error fixing {doc_file}: {e}")
    
    def _fix_file_imports(self, content: str) -> str:
        """Fix imports in file content using the mapping rules."""
        for pattern, replacement in self.import_mappings.items():
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def analyze_remaining_issues(self):
        """Analyze what import issues remain after fixes."""
        print("\n🔍 Analyzing remaining import issues...")
        
        remaining_issues = []
        
        # Find all documentation files
        doc_files = []
        for ext in ['*.md', '*.mdx']:
            doc_files.extend(Path('.').rglob(ext))
        
        for doc_file in doc_files:
            if '.git' in str(doc_file) or 'node_modules' in str(doc_file):
                continue
                
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    # Check for problematic patterns
                    if re.search(r'from contexten\.sdk', line):
                        remaining_issues.append({
                            'file': doc_file,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'contexten.sdk import'
                        })
                    elif re.search(r'from contexten\.shared', line):
                        remaining_issues.append({
                            'file': doc_file,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'contexten.shared import'
                        })
                    elif re.search(r'from contexten import Agent', line):
                        remaining_issues.append({
                            'file': doc_file,
                            'line': line_num,
                            'content': line.strip(),
                            'issue': 'Agent import'
                        })
                        
            except Exception as e:
                print(f"  ⚠️ Error analyzing {doc_file}: {e}")
        
        if remaining_issues:
            print(f"  🚨 Found {len(remaining_issues)} remaining issues:")
            for issue in remaining_issues:
                print(f"    📁 {issue['file']}:{issue['line']} - {issue['content']}")
        else:
            print("  🎉 No remaining import issues found!")
        
        return remaining_issues


def main():
    print("🚀 Starting documentation import fixes...")
    
    fixer = DocumentationImportFixer()
    
    # Apply fixes
    fixer.fix_documentation_files()
    
    print(f"\n✅ Processed {fixer.files_processed} files, applied {fixer.fixes_applied} fixes!")
    
    # Check for remaining issues
    remaining = fixer.analyze_remaining_issues()
    
    if not remaining:
        print("\n🎉 All documentation import issues resolved!")
    else:
        print(f"\n⚠️ {len(remaining)} issues may need manual review")


if __name__ == "__main__":
    main()

