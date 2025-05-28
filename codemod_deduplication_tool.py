#!/usr/bin/env python3
"""
Comprehensive Codemod Tool for Graph-Sitter/Codegen Deduplication

This tool performs intelligent deduplication and import management between
src/codegen and src/graph_sitter directories.

Features:
- Scans both codebases to understand module structure
- Identifies overlapping modules and determines which version to keep
- Removes duplicates while preserving feature-rich versions
- Updates imports in codegen to properly reference graph_sitter
- Leaves graph_sitter imports unchanged (as it's the library)

Usage:
    python codemod_deduplication_tool.py [--dry-run] [--verbose]

Options:
    --dry-run    Show what would be done without making changes
    --verbose    Show detailed analysis and progress
    --help       Show this help message

Author: Codegen Bot
Version: 1.0.0
"""

import os
import ast
import re
import argparse
import difflib
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ModuleAnalyzer:
    """Analyzes modules and their relationships between codegen and graph_sitter."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.codegen_modules = {}
        self.graph_sitter_modules = {}
        self.module_features = {}
    
    def scan_modules(self) -> Tuple[Dict[str, Path], Dict[str, Path]]:
        """Scan both codebases to understand module structure."""
        if self.verbose:
            print(f"{Colors.OKBLUE}🔍 Scanning module structure...{Colors.ENDC}")
        
        # Scan codegen modules
        self.codegen_modules = self._scan_directory("src/codegen", "codegen")
        print(f"  📁 Codegen modules: {Colors.OKGREEN}{len(self.codegen_modules)}{Colors.ENDC}")
        
        # Scan graph_sitter modules  
        self.graph_sitter_modules = self._scan_directory("src/graph_sitter", "graph_sitter")
        print(f"  📁 Graph_sitter modules: {Colors.OKGREEN}{len(self.graph_sitter_modules)}{Colors.ENDC}")
        
        return self.codegen_modules, self.graph_sitter_modules
    
    def _scan_directory(self, base_dir: str, package_name: str) -> Dict[str, Path]:
        """Scan a directory and return module mapping."""
        modules = {}
        base_path = Path(base_dir)
        
        if not base_path.exists():
            print(f"  {Colors.WARNING}⚠️ Directory {base_dir} does not exist{Colors.ENDC}")
            return modules
        
        for py_file in base_path.rglob("*.py"):
            # Convert file path to module path
            rel_path = py_file.relative_to(base_path)
            module_parts = list(rel_path.parts)
            
            # Handle __init__.py files
            if module_parts[-1] == "__init__.py":
                module_parts = module_parts[:-1]
            else:
                module_parts[-1] = module_parts[-1][:-3]  # Remove .py
            
            if module_parts:  # Skip empty module paths
                module_path = f"{package_name}.{'.'.join(module_parts)}"
                modules[module_path] = py_file
                
                # Analyze file features
                try:
                    self._analyze_file_features(py_file, module_path)
                except Exception as e:
                    if self.verbose:
                        print(f"    {Colors.WARNING}⚠️ Error analyzing {py_file}: {e}{Colors.ENDC}")
        
        return modules
    
    def _analyze_file_features(self, file_path: Path, module_path: str):
        """Analyze file features for comparison."""
        file_size = file_path.stat().st_size
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count features (classes, functions, imports, etc.)
        features = {
            'size': file_size,
            'lines': len(content.splitlines()),
            'classes': len(re.findall(r'^class\s+\w+', content, re.MULTILINE)),
            'functions': len(re.findall(r'^def\s+\w+', content, re.MULTILINE)),
            'imports': len(re.findall(r'^(?:from|import)\s+', content, re.MULTILINE)),
            'docstrings': len(re.findall(r'""".*?"""', content, re.DOTALL)),
            'comments': len(re.findall(r'#.*$', content, re.MULTILINE))
        }
        
        self.module_features[module_path] = features
    
    def find_overlapping_modules(self) -> Tuple[Dict[str, str], Set[str], Set[str]]:
        """Find modules that exist in both codebases and determine which to keep."""
        if self.verbose:
            print(f"\n{Colors.OKBLUE}🔍 Analyzing overlapping modules...{Colors.ENDC}")
        
        # Find modules that exist in both
        codegen_module_names = set(self.codegen_modules.keys())
        graph_sitter_module_names = set(self.graph_sitter_modules.keys())
        
        # Convert to relative module names for comparison
        codegen_relative = {m.replace('codegen.', '') for m in codegen_module_names}
        graph_sitter_relative = {m.replace('graph_sitter.', '') for m in graph_sitter_module_names}
        
        overlapping_relative = codegen_relative & graph_sitter_relative
        
        print(f"  📊 Overlapping modules: {Colors.OKGREEN}{len(overlapping_relative)}{Colors.ENDC}")
        
        # Decide which version to keep for each overlapping module
        keep_in_codegen = {}  # relative_module -> reason
        codegen_only = codegen_relative - graph_sitter_relative
        graph_sitter_only = graph_sitter_relative - codegen_relative
        
        for rel_module in sorted(overlapping_relative):
            codegen_module = f"codegen.{rel_module}"
            graph_sitter_module = f"graph_sitter.{rel_module}"
            
            codegen_features = self.module_features.get(codegen_module, {})
            graph_sitter_features = self.module_features.get(graph_sitter_module, {})
            
            # Calculate feature scores
            codegen_score = self._calculate_feature_score(codegen_features)
            graph_sitter_score = self._calculate_feature_score(graph_sitter_features)
            
            if self.verbose:
                print(f"\n📄 {rel_module}")
                print(f"  Codegen score: {codegen_score} (size: {codegen_features.get('size', 0)}, "
                      f"classes: {codegen_features.get('classes', 0)}, "
                      f"functions: {codegen_features.get('functions', 0)})")
                print(f"  Graph_sitter score: {graph_sitter_score} (size: {graph_sitter_features.get('size', 0)}, "
                      f"classes: {graph_sitter_features.get('classes', 0)}, "
                      f"functions: {graph_sitter_features.get('functions', 0)})")
            
            # Decision logic: keep in codegen if it has significantly more features
            if codegen_score > graph_sitter_score * 1.1:  # 10% threshold
                reason = f"more features (score: {codegen_score} vs {graph_sitter_score})"
                keep_in_codegen[rel_module] = reason
                print(f"    {Colors.OKGREEN}✅ Keep in codegen: {rel_module} - {reason}{Colors.ENDC}")
            else:
                print(f"    {Colors.OKCYAN}➡️ Use from graph_sitter: {rel_module}{Colors.ENDC}")
        
        if self.verbose:
            print(f"\n📊 Summary:")
            print(f"  🏠 Keep in codegen: {Colors.OKGREEN}{len(keep_in_codegen)}{Colors.ENDC} modules")
            print(f"  📚 Use from graph_sitter: {Colors.OKCYAN}{len(overlapping_relative) - len(keep_in_codegen)}{Colors.ENDC} modules")
            print(f"  🆕 Unique to codegen: {Colors.OKGREEN}{len(codegen_only)}{Colors.ENDC} modules")
            print(f"  🆕 Unique to graph_sitter: {Colors.OKCYAN}{len(graph_sitter_only)}{Colors.ENDC} modules")
        
        return keep_in_codegen, codegen_only, graph_sitter_only
    
    def _calculate_feature_score(self, features: Dict) -> int:
        """Calculate a feature score for comparison."""
        return (
            features.get('size', 0) +
            features.get('classes', 0) * 100 +
            features.get('functions', 0) * 50 +
            features.get('imports', 0) * 10 +
            features.get('docstrings', 0) * 25 +
            features.get('comments', 0) * 5
        )

class DeduplicationEngine:
    """Handles the actual deduplication and import updates."""
    
    def __init__(self, analyzer: ModuleAnalyzer, dry_run: bool = False, verbose: bool = False):
        self.analyzer = analyzer
        self.dry_run = dry_run
        self.verbose = verbose
        self.keep_in_codegen = {}
        self.codegen_only = set()
        self.graph_sitter_only = set()
    
    def execute_deduplication(self):
        """Perform the full deduplication process."""
        print(f"\n{Colors.HEADER}🚀 Starting comprehensive deduplication...{Colors.ENDC}")
        
        if self.dry_run:
            print(f"{Colors.WARNING}🔍 DRY RUN MODE - No changes will be made{Colors.ENDC}")
        
        # Step 1: Scan modules
        self.analyzer.scan_modules()
        
        # Step 2: Analyze overlaps
        self.keep_in_codegen, self.codegen_only, self.graph_sitter_only = self.analyzer.find_overlapping_modules()
        
        # Step 3: Remove duplicates
        self._remove_duplicates()
        
        # Step 4: Update imports in codegen
        self._update_codegen_imports()
        
        print(f"\n{Colors.OKGREEN}✅ Deduplication completed!{Colors.ENDC}")
        
        if self.dry_run:
            print(f"{Colors.WARNING}Note: This was a dry run. Use without --dry-run to apply changes.{Colors.ENDC}")
    
    def _remove_duplicates(self):
        """Remove duplicate files, keeping the better versions."""
        print(f"\n{Colors.OKBLUE}🗑️ Removing duplicate files...{Colors.ENDC}")
        
        removed_from_codegen = 0
        removed_from_graph_sitter = 0
        
        # Remove from graph_sitter where codegen has better versions
        for rel_module in self.keep_in_codegen:
            graph_sitter_module = f"graph_sitter.{rel_module}"
            if graph_sitter_module in self.analyzer.graph_sitter_modules:
                file_path = self.analyzer.graph_sitter_modules[graph_sitter_module]
                
                if self.dry_run:
                    print(f"  {Colors.WARNING}[DRY RUN] Would remove from graph_sitter: {rel_module}{Colors.ENDC}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"  {Colors.OKGREEN}✅ Removed from graph_sitter: {rel_module}{Colors.ENDC}")
                        removed_from_graph_sitter += 1
                        
                        # Remove empty directories
                        self._remove_empty_dirs(file_path.parent, Path("src/graph_sitter"))
                        
                    except Exception as e:
                        print(f"  {Colors.FAIL}❌ Error removing {file_path}: {e}{Colors.ENDC}")
        
        # Remove from codegen where graph_sitter has equivalent/better versions
        overlapping_relative = set()
        codegen_relative = {m.replace('codegen.', '') for m in self.analyzer.codegen_modules.keys()}
        graph_sitter_relative = {m.replace('graph_sitter.', '') for m in self.analyzer.graph_sitter_modules.keys()}
        overlapping_relative = codegen_relative & graph_sitter_relative
        
        for rel_module in overlapping_relative:
            if rel_module not in self.keep_in_codegen:
                codegen_module = f"codegen.{rel_module}"
                if codegen_module in self.analyzer.codegen_modules:
                    file_path = self.analyzer.codegen_modules[codegen_module]
                    
                    if self.dry_run:
                        print(f"  {Colors.WARNING}[DRY RUN] Would remove from codegen: {rel_module}{Colors.ENDC}")
                    else:
                        try:
                            os.remove(file_path)
                            print(f"  {Colors.OKGREEN}✅ Removed from codegen: {rel_module}{Colors.ENDC}")
                            removed_from_codegen += 1
                            
                            # Remove empty directories
                            self._remove_empty_dirs(file_path.parent, Path("src/codegen"))
                            
                        except Exception as e:
                            print(f"  {Colors.FAIL}❌ Error removing {file_path}: {e}{Colors.ENDC}")
        
        if not self.dry_run:
            print(f"\n📊 Removal summary:")
            print(f"  🗑️ Removed from codegen: {Colors.OKGREEN}{removed_from_codegen}{Colors.ENDC} files")
            print(f"  🗑️ Removed from graph_sitter: {Colors.OKGREEN}{removed_from_graph_sitter}{Colors.ENDC} files")
    
    def _remove_empty_dirs(self, dir_path: Path, base_path: Path):
        """Remove empty directories recursively."""
        try:
            while dir_path != base_path and dir_path.exists():
                if not any(dir_path.iterdir()):
                    if not self.dry_run:
                        dir_path.rmdir()
                    if self.verbose:
                        action = "[DRY RUN] Would remove" if self.dry_run else "Removed"
                        print(f"    🗂️ {action} empty directory: {dir_path.relative_to(base_path)}")
                    dir_path = dir_path.parent
                else:
                    break
        except OSError:
            pass
    
    def _update_codegen_imports(self):
        """Update imports in codegen files to reference graph_sitter when appropriate."""
        print(f"\n{Colors.OKBLUE}🔧 Updating imports in codegen files...{Colors.ENDC}")
        
        # Get all remaining Python files in codegen
        codegen_files = list(Path("src/codegen").rglob("*.py"))
        
        files_updated = 0
        total_changes = 0
        
        for py_file in codegen_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Update imports based on our analysis
                updated_content = self._update_imports_in_content(content)
                
                if updated_content != original_content:
                    if self.dry_run:
                        rel_path = py_file.relative_to(Path("src/codegen"))
                        print(f"  {Colors.WARNING}[DRY RUN] Would update: {rel_path}{Colors.ENDC}")
                    else:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        
                        rel_path = py_file.relative_to(Path("src/codegen"))
                        print(f"  {Colors.OKGREEN}✅ Updated: {rel_path}{Colors.ENDC}")
                    
                    files_updated += 1
                    # Count changes
                    changes = abs(len(re.findall(r'from graph_sitter\.', updated_content)) - 
                                len(re.findall(r'from graph_sitter\.', original_content)))
                    total_changes += changes
            
            except Exception as e:
                print(f"  {Colors.FAIL}❌ Error updating {py_file}: {e}{Colors.ENDC}")
        
        if not self.dry_run:
            print(f"\n📊 Import update summary:")
            print(f"  📝 Files updated: {Colors.OKGREEN}{files_updated}{Colors.ENDC}")
            print(f"  🔄 Total import changes: {Colors.OKGREEN}{total_changes}{Colors.ENDC}")
    
    def _update_imports_in_content(self, content: str) -> str:
        """Update imports in file content."""
        lines = content.splitlines()
        updated_lines = []
        
        for line in lines:
            updated_line = line
            
            # Handle 'from codegen.X import Y' patterns
            from_match = re.match(r'^(\s*from\s+)codegen\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+(import\s+.+)$', line)
            if from_match:
                prefix, module_path, import_part = from_match.groups()
                
                # Check if this module should be imported from graph_sitter
                if self._should_import_from_graph_sitter(module_path):
                    updated_line = f"{prefix}graph_sitter.{module_path} {import_part}"
            
            # Handle 'import codegen.X' patterns
            import_match = re.match(r'^(\s*import\s+)codegen\.([a-zA-Z_][a-zA-Z0-9_.]*)', line)
            if import_match:
                prefix, module_path = import_match.groups()
                
                # Check if this module should be imported from graph_sitter
                if self._should_import_from_graph_sitter(module_path):
                    updated_line = f"{prefix}graph_sitter.{module_path}"
            
            updated_lines.append(updated_line)
        
        return '\n'.join(updated_lines)
    
    def _should_import_from_graph_sitter(self, module_path: str) -> bool:
        """Determine if a module should be imported from graph_sitter."""
        # If the module is kept in codegen, import from codegen
        if module_path in self.keep_in_codegen:
            return False
        
        # If the module is unique to codegen, import from codegen
        if module_path in self.codegen_only:
            return False
        
        # If the module exists in graph_sitter, import from graph_sitter
        graph_sitter_module = f"graph_sitter.{module_path}"
        if graph_sitter_module in self.analyzer.graph_sitter_modules:
            return True
        
        # Default to codegen if unsure
        return False

def main():
    """Main function to run the codemod tool."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Codemod Tool for Graph-Sitter/Codegen Deduplication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python codemod_deduplication_tool.py --dry-run --verbose
  python codemod_deduplication_tool.py
  python codemod_deduplication_tool.py --verbose

This tool intelligently deduplicates files between src/codegen and src/graph_sitter,
keeping feature-rich versions in codegen and updating imports appropriately.
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed analysis and progress'
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not (Path("src/codegen").exists() and Path("src/graph_sitter").exists()):
        print(f"{Colors.FAIL}❌ Error: This tool must be run from the root of the graph-sitter repository{Colors.ENDC}")
        print(f"Expected directories: src/codegen and src/graph_sitter")
        return 1
    
    print(f"{Colors.HEADER}🔧 COMPREHENSIVE CODEMOD FOR DEDUPLICATION{Colors.ENDC}")
    print("=" * 60)
    
    # Create analyzer and deduplication engine
    analyzer = ModuleAnalyzer(verbose=args.verbose)
    engine = DeduplicationEngine(analyzer, dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        # Execute the deduplication
        engine.execute_deduplication()
        
        print(f"\n{Colors.OKGREEN}🎯 CODEMOD COMPLETED!{Colors.ENDC}")
        print("- Analyzed module structure comprehensively")
        print("- Removed duplicates, keeping feature-rich versions in codegen")
        print("- Updated codegen imports to reference graph_sitter appropriately")
        print("- Left graph_sitter imports unchanged (as it's the library)")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️ Operation cancelled by user{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    exit(main())

