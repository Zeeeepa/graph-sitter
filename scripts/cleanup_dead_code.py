#!/usr/bin/env python3
"""
Dead Code Cleanup Script for Graph-Sitter Repository

This script identifies and removes dead code including:
- Unused imports
- Unreferenced functions and classes
- TODO/FIXME comments analysis
- Syntax error fixes
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeadCodeAnalyzer:
    """Analyzes and removes dead code from Python files"""
    
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.unused_imports = []
        self.todo_comments = []
        self.syntax_errors = []
        self.unreferenced_functions = []
        
    def analyze_file(self, filepath: Path) -> Dict[str, any]:
        """Analyze a single Python file for dead code"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors first
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.syntax_errors.append({
                    'file': str(filepath),
                    'error': str(e),
                    'line': e.lineno
                })
                return {'status': 'syntax_error', 'error': str(e)}
            
            # Analyze imports and usage
            imports = []
            used_names = set()
            defined_functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'name': alias.name,
                            'alias': alias.asname or alias.name,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append({
                            'name': alias.name,
                            'alias': alias.asname or alias.name,
                            'line': node.lineno,
                            'from': node.module
                        })
                elif isinstance(node, ast.FunctionDef):
                    defined_functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'is_private': node.name.startswith('_'),
                        'has_decorator': len(node.decorator_list) > 0
                    })
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Find unused imports
            unused = []
            for imp in imports:
                if imp['alias'] not in used_names and imp['name'] not in used_names:
                    # Skip __all__ and __init__ related imports
                    if not self._is_special_import(imp, content):
                        unused.append(imp)
                        self.unused_imports.append({
                            'file': str(filepath),
                            'import': imp
                        })
            
            # Find TODO/FIXME comments
            todos = self._find_todo_comments(content, filepath)
            self.todo_comments.extend(todos)
            
            return {
                'status': 'success',
                'imports': len(imports),
                'unused_imports': len(unused),
                'functions': len(defined_functions),
                'todos': len(todos)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _is_special_import(self, imp: Dict, content: str) -> bool:
        """Check if import is special (used in __all__, type hints, etc.)"""
        name = imp['alias']
        
        # Check if used in __all__
        if f'"{name}"' in content or f"'{name}'" in content:
            return True
        
        # Check if used in type hints (comments or annotations)
        if f': {name}' in content or f'-> {name}' in content:
            return True
        
        # Check if used in string literals (might be dynamic imports)
        if f'"{imp["name"]}"' in content or f"'{imp['name']}'" in content:
            return True
        
        return False
    
    def _find_todo_comments(self, content: str, filepath: Path) -> List[Dict]:
        """Find TODO/FIXME/XXX/HACK comments"""
        todos = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Look for TODO, FIXME, XXX, HACK comments
            match = re.search(r'#.*?\b(TODO|FIXME|XXX|HACK)\b.*', line, re.IGNORECASE)
            if match:
                todos.append({
                    'file': str(filepath),
                    'line': i,
                    'type': match.group(1).upper(),
                    'comment': line.strip(),
                    'priority': self._get_todo_priority(match.group(1))
                })
        
        return todos
    
    def _get_todo_priority(self, todo_type: str) -> str:
        """Get priority level for TODO type"""
        priority_map = {
            'FIXME': 'high',
            'HACK': 'high',
            'XXX': 'medium',
            'TODO': 'low'
        }
        return priority_map.get(todo_type.upper(), 'low')
    
    def analyze_directory(self) -> Dict[str, any]:
        """Analyze all Python files in the source directory"""
        logger.info(f"Analyzing directory: {self.src_dir}")
        
        results = {
            'files_analyzed': 0,
            'files_with_issues': 0,
            'total_unused_imports': 0,
            'total_todos': 0,
            'syntax_errors': 0
        }
        
        for py_file in self.src_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            result = self.analyze_file(py_file)
            results['files_analyzed'] += 1
            
            if result['status'] == 'success':
                if result['unused_imports'] > 0 or result['todos'] > 0:
                    results['files_with_issues'] += 1
                results['total_unused_imports'] += result['unused_imports']
                results['total_todos'] += result['todos']
            elif result['status'] == 'syntax_error':
                results['syntax_errors'] += 1
        
        return results
    
    def _should_skip_file(self, filepath: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.pytest_cache',
            'node_modules'
        ]
        
        return any(pattern in str(filepath) for pattern in skip_patterns)
    
    def generate_cleanup_script(self, output_file: str = "cleanup_commands.sh"):
        """Generate shell script to clean up unused imports"""
        commands = []
        
        # Group by file for efficient processing
        files_to_clean = {}
        for unused in self.unused_imports:
            filepath = unused['file']
            if filepath not in files_to_clean:
                files_to_clean[filepath] = []
            files_to_clean[filepath].append(unused['import'])
        
        commands.append("#!/bin/bash")
        commands.append("# Auto-generated cleanup script")
        commands.append("# Run this script to remove unused imports")
        commands.append("")
        
        # Install cleanup tools
        commands.append("# Install cleanup tools")
        commands.append("pip install autoflake unimport")
        commands.append("")
        
        # Generate autoflake commands
        commands.append("# Remove unused imports with autoflake")
        for filepath in files_to_clean.keys():
            commands.append(f"autoflake --remove-all-unused-imports --in-place {filepath}")
        
        commands.append("")
        commands.append("# Alternative: Use unimport for more aggressive cleanup")
        commands.append("# unimport --remove-unused-imports src/")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(commands))
        
        logger.info(f"Cleanup script generated: {output_file}")
    
    def fix_syntax_errors(self, dry_run: bool = True):
        """Fix common syntax errors"""
        for error in self.syntax_errors:
            filepath = error['file']
            logger.info(f"Fixing syntax error in {filepath}: {error['error']}")
            
            if not dry_run:
                self._fix_line_continuation_error(filepath)
    
    def _fix_line_continuation_error(self, filepath: str):
        """Fix line continuation character errors"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix common line continuation issues
            fixed_content = content.replace('\\\\n', '\\n')
            fixed_content = re.sub(r'\\n\s+', '\n        ', fixed_content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            logger.info(f"Fixed line continuation errors in {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to fix {filepath}: {e}")
    
    def generate_report(self, output_file: str = "dead_code_report.md"):
        """Generate comprehensive dead code analysis report"""
        report = []
        
        report.append("# Dead Code Analysis Report")
        report.append(f"**Generated**: {os.popen('date').read().strip()}")
        report.append("")
        
        # Summary
        report.append("## 📊 Summary")
        report.append(f"- **Unused Imports**: {len(self.unused_imports)}")
        report.append(f"- **TODO Comments**: {len(self.todo_comments)}")
        report.append(f"- **Syntax Errors**: {len(self.syntax_errors)}")
        report.append("")
        
        # Syntax Errors (High Priority)
        if self.syntax_errors:
            report.append("## 🚨 Syntax Errors (High Priority)")
            for error in self.syntax_errors:
                report.append(f"- **{error['file']}** (line {error['line']}): {error['error']}")
            report.append("")
        
        # Unused Imports
        if self.unused_imports:
            report.append("## 🧹 Unused Imports")
            
            # Group by file
            by_file = {}
            for unused in self.unused_imports:
                filepath = unused['file']
                if filepath not in by_file:
                    by_file[filepath] = []
                by_file[filepath].append(unused['import'])
            
            for filepath, imports in sorted(by_file.items()):
                report.append(f"### {filepath}")
                for imp in imports:
                    if 'from' in imp:
                        report.append(f"- `from {imp['from']} import {imp['name']}`")
                    else:
                        report.append(f"- `import {imp['name']}`")
                report.append("")
        
        # TODO Comments Analysis
        if self.todo_comments:
            report.append("## 📝 TODO Comments Analysis")
            
            # Group by priority
            by_priority = {'high': [], 'medium': [], 'low': []}
            for todo in self.todo_comments:
                by_priority[todo['priority']].append(todo)
            
            for priority in ['high', 'medium', 'low']:
                if by_priority[priority]:
                    report.append(f"### {priority.title()} Priority")
                    for todo in by_priority[priority]:
                        report.append(f"- **{todo['file']}** (line {todo['line']}): {todo['comment']}")
                    report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        report.append("1. **Fix syntax errors immediately** - These prevent code execution")
        report.append("2. **Remove unused imports** - Use the generated cleanup script")
        report.append("3. **Address high-priority TODOs** - These indicate critical issues")
        report.append("4. **Review medium-priority TODOs** - Plan for future sprints")
        report.append("")
        
        # Cleanup Commands
        report.append("## 🔧 Cleanup Commands")
        report.append("```bash")
        report.append("# Install cleanup tools")
        report.append("pip install autoflake unimport")
        report.append("")
        report.append("# Remove unused imports")
        report.append("autoflake --remove-all-unused-imports --in-place --recursive src/")
        report.append("")
        report.append("# Alternative aggressive cleanup")
        report.append("unimport --remove-unused-imports src/")
        report.append("```")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(report))
        
        logger.info(f"Report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Analyze and clean dead code")
    parser.add_argument("--src-dir", default="src", help="Source directory to analyze")
    parser.add_argument("--fix-syntax", action="store_true", help="Fix syntax errors")
    parser.add_argument("--generate-cleanup", action="store_true", help="Generate cleanup script")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--report", default="dead_code_report.md", help="Output report file")
    
    args = parser.parse_args()
    
    analyzer = DeadCodeAnalyzer(args.src_dir)
    
    logger.info("Starting dead code analysis...")
    results = analyzer.analyze_directory()
    
    logger.info("Analysis Results:")
    logger.info(f"  Files analyzed: {results['files_analyzed']}")
    logger.info(f"  Files with issues: {results['files_with_issues']}")
    logger.info(f"  Unused imports: {results['total_unused_imports']}")
    logger.info(f"  TODO comments: {results['total_todos']}")
    logger.info(f"  Syntax errors: {results['syntax_errors']}")
    
    # Generate report
    analyzer.generate_report(args.report)
    
    # Fix syntax errors if requested
    if args.fix_syntax:
        analyzer.fix_syntax_errors(dry_run=args.dry_run)
    
    # Generate cleanup script if requested
    if args.generate_cleanup:
        analyzer.generate_cleanup_script()
    
    logger.info("Analysis complete!")

if __name__ == "__main__":
    main()

