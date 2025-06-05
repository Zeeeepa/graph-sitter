#!/usr/bin/env python3
"""
Remove Redundant Code - Clean up overcomplicated analysis implementations

This script identifies and removes redundant code structures that redefine
functionality already provided by graph-sitter's built-in capabilities.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Set


class RedundantCodeRemover:
    """Identifies and removes redundant analysis code."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.redundant_files: List[Path] = []
        self.redundant_directories: List[Path] = []
        self.files_to_simplify: List[Path] = []
        
    def analyze_redundancy(self) -> Dict[str, List[str]]:
        """Analyze the codebase for redundant implementations."""
        print("🔍 Analyzing codebase for redundant implementations...")
        
        redundancy_report = {
            'redundant_analyzers': [],
            'redundant_databases': [],
            'redundant_visualizations': [],
            'redundant_reports': [],
            'redundant_legacy': [],
            'overcomplicated_examples': []
        }
        
        # Find redundant analyzer implementations
        self._find_redundant_analyzers(redundancy_report)
        
        # Find redundant database adapters
        self._find_redundant_databases(redundancy_report)
        
        # Find redundant visualization systems
        self._find_redundant_visualizations(redundancy_report)
        
        # Find redundant report generators
        self._find_redundant_reports(redundancy_report)
        
        # Find legacy compatibility layers
        self._find_redundant_legacy(redundancy_report)
        
        # Find overcomplicated examples
        self._find_overcomplicated_examples(redundancy_report)
        
        return redundancy_report
    
    def _find_redundant_analyzers(self, report: Dict[str, List[str]]):
        """Find analyzer classes that duplicate graph-sitter functionality."""
        analyzer_patterns = [
            'comprehensive_analyzer',
            'unified_analyzer', 
            'repository_analyzer',
            'codebase_analyzer',
            'static_analyzer'
        ]
        
        for pattern in analyzer_patterns:
            files = list(self.repo_path.rglob(f"*{pattern}*"))
            for file in files:
                if file.suffix == '.py':
                    report['redundant_analyzers'].append(str(file))
                    self.redundant_files.append(file)
    
    def _find_redundant_databases(self, report: Dict[str, List[str]]):
        """Find database adapters that duplicate graph-sitter's in-memory graph."""
        database_patterns = [
            'database_adapter',
            'codebase_database',
            'analysis_database',
            'graph_database'
        ]
        
        for pattern in database_patterns:
            files = list(self.repo_path.rglob(f"*{pattern}*"))
            for file in files:
                if file.suffix == '.py':
                    report['redundant_databases'].append(str(file))
                    self.redundant_files.append(file)
    
    def _find_redundant_visualizations(self, report: Dict[str, List[str]]):
        """Find visualization systems that duplicate graph-sitter's built-in visualize()."""
        # Keep only the simple dashboard, remove complex implementations
        viz_dir = self.repo_path / "src" / "graph_sitter" / "adapters" / "visualizations"
        if viz_dir.exists():
            for file in viz_dir.rglob("*.py"):
                if file.name not in ['__init__.py', 'dashboard.py']:
                    report['redundant_visualizations'].append(str(file))
                    self.redundant_files.append(file)
    
    def _find_redundant_reports(self, report: Dict[str, List[str]]):
        """Find report generators that are unnecessarily complex."""
        report_patterns = [
            'html_generator',
            'comprehensive_report',
            'analysis_report'
        ]
        
        for pattern in report_patterns:
            files = list(self.repo_path.rglob(f"*{pattern}*"))
            for file in files:
                if file.suffix == '.py' and 'simple' not in file.name:
                    report['redundant_reports'].append(str(file))
                    self.redundant_files.append(file)
    
    def _find_redundant_legacy(self, report: Dict[str, List[str]]):
        """Find legacy compatibility layers that are no longer needed."""
        legacy_patterns = [
            'legacy_',
            'compatibility',
            'unified_framework',
            'base_analyzer'
        ]
        
        for pattern in legacy_patterns:
            files = list(self.repo_path.rglob(f"*{pattern}*"))
            for file in files:
                if file.suffix == '.py':
                    report['redundant_legacy'].append(str(file))
                    self.redundant_files.append(file)
    
    def _find_overcomplicated_examples(self, report: Dict[str, List[str]]):
        """Find examples that are unnecessarily complex."""
        examples_to_remove = [
            'comprehensive_analysis_example.py',
            'comprehensive_analysis_with_reports.py',
            'run_comprehensive_analysis.py',
            'generate_html_preview.py',
            'validate_analysis_system.py'
        ]
        
        for example in examples_to_remove:
            files = list(self.repo_path.rglob(example))
            for file in files:
                report['overcomplicated_examples'].append(str(file))
                self.redundant_files.append(file)
    
    def remove_redundant_files(self, dry_run: bool = True) -> Dict[str, int]:
        """Remove redundant files and directories."""
        removed_count = {
            'files': 0,
            'directories': 0,
            'total_size_mb': 0
        }
        
        if dry_run:
            print("🧪 DRY RUN - No files will actually be removed")
        else:
            print("🗑️  REMOVING redundant files...")
        
        # Remove redundant files
        for file_path in self.redundant_files:
            if file_path.exists():
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    removed_count['total_size_mb'] += size_mb
                    
                    if not dry_run:
                        file_path.unlink()
                    
                    removed_count['files'] += 1
                    print(f"  {'[DRY RUN] ' if dry_run else ''}Removed: {file_path}")
                    
                except Exception as e:
                    print(f"  ❌ Error removing {file_path}: {e}")
        
        # Remove empty directories
        for dir_path in self.redundant_directories:
            if dir_path.exists() and not any(dir_path.iterdir()):
                try:
                    if not dry_run:
                        dir_path.rmdir()
                    
                    removed_count['directories'] += 1
                    print(f"  {'[DRY RUN] ' if dry_run else ''}Removed empty dir: {dir_path}")
                    
                except Exception as e:
                    print(f"  ❌ Error removing directory {dir_path}: {e}")
        
        return removed_count
    
    def create_simplified_adapter(self):
        """Create a simplified adapter.py that imports only essential components."""
        adapter_content = '''"""
Simplified Graph-Sitter Adapter

This replaces the overcomplicated adapter system with simple imports
of graph-sitter's built-in capabilities.
"""

# Core graph-sitter functionality (already implemented)
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol

# Simple analysis using built-in properties
from .simplified_analysis import SimplifiedAnalysis

# Essential visualization (keep only simple dashboard)
try:
    from .visualizations.dashboard import InteractiveDashboard
except ImportError:
    InteractiveDashboard = None

# Simple exports
__all__ = [
    'Codebase',
    'Function', 
    'Class',
    'Symbol',
    'SimplifiedAnalysis',
    'InteractiveDashboard'
]


def analyze_codebase(repo_path: str) -> dict:
    """
    Simple codebase analysis using graph-sitter's built-in capabilities.
    
    This replaces all the complex analyzer classes with simple property access.
    """
    analysis = SimplifiedAnalysis(repo_path)
    return analysis.analyze()


def get_dead_code(repo_path: str) -> list:
    """
    Get dead code using graph-sitter's simple pattern.
    
    This is the exact pattern from graph-sitter.com documentation.
    """
    codebase = Codebase(repo_path)
    return [f.name for f in codebase.functions if not f.usages]


def remove_dead_code(repo_path: str):
    """
    Remove dead code using graph-sitter's built-in removal.
    
    This is the exact pattern from graph-sitter.com documentation.
    """
    codebase = Codebase(repo_path)
    for function in codebase.functions:
        if not function.usages:
            function.remove()
    codebase.commit()
'''
        
        adapter_file = self.repo_path / "src" / "graph_sitter" / "adapters" / "adapter.py"
        adapter_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(adapter_file, 'w') as f:
            f.write(adapter_content)
        
        print(f"✅ Created simplified adapter: {adapter_file}")
    
    def generate_removal_report(self, redundancy_report: Dict[str, List[str]]) -> str:
        """Generate a detailed report of what will be removed."""
        report_lines = [
            "# Redundant Code Removal Report",
            "",
            "## Summary",
            f"Based on analysis of graph-sitter.com, the following redundant implementations were identified:",
            ""
        ]
        
        total_files = 0
        for category, files in redundancy_report.items():
            if files:
                report_lines.extend([
                    f"### {category.replace('_', ' ').title()}",
                    f"Files to remove: {len(files)}",
                    ""
                ])
                
                for file in files:
                    report_lines.append(f"- `{file}`")
                    total_files += 1
                
                report_lines.append("")
        
        report_lines.extend([
            "## Rationale",
            "",
            "These files are redundant because graph-sitter already provides:",
            "",
            "1. **Pre-computed Analysis**: `function.dependencies`, `function.usages` (instant lookups)",
            "2. **Built-in Dead Code Detection**: `if not function.usages: function.remove()`", 
            "3. **Call Graph Traversal**: `function.function_calls` (pre-computed)",
            "4. **Inheritance Analysis**: `class.superclasses`, `class.is_subclass_of()`",
            "5. **Type Resolution**: `function.return_type.resolved_types`",
            "6. **Visualization**: `codebase.visualize(graph)`",
            "",
            f"**Total files to remove: {total_files}**",
            "",
            "## Simplified Approach",
            "",
            "Replace complex analyzers with simple property access:",
            "",
            "```python",
            "from graph_sitter import Codebase",
            "",
            "# Simple analysis",
            "codebase = Codebase('./')",
            "unused_functions = [f for f in codebase.functions if not f.usages]",
            "```",
            "",
            "This is dramatically simpler and uses graph-sitter's actual capabilities."
        ])
        
        return "\n".join(report_lines)


def main():
    """Main function to analyze and remove redundant code."""
    print("🧹 Graph-Sitter Redundant Code Removal")
    print("=" * 50)
    
    remover = RedundantCodeRemover()
    
    # Analyze redundancy
    redundancy_report = remover.analyze_redundancy()
    
    # Generate report
    report = remover.generate_removal_report(redundancy_report)
    
    # Save report
    with open("redundant_code_removal_report.md", "w") as f:
        f.write(report)
    
    print("📋 Redundancy analysis complete!")
    print(f"📄 Report saved to: redundant_code_removal_report.md")
    
    # Show summary
    total_redundant = sum(len(files) for files in redundancy_report.values())
    print(f"🗑️  Total redundant files identified: {total_redundant}")
    
    for category, files in redundancy_report.items():
        if files:
            print(f"  {category}: {len(files)} files")
    
    # Dry run removal
    print("\n🧪 Performing dry run removal...")
    removal_stats = remover.remove_redundant_files(dry_run=True)
    
    print(f"\n📊 Removal Statistics (Dry Run):")
    print(f"  Files to remove: {removal_stats['files']}")
    print(f"  Directories to remove: {removal_stats['directories']}")
    print(f"  Total size to free: {removal_stats['total_size_mb']:.2f} MB")
    
    # Create simplified adapter
    remover.create_simplified_adapter()
    
    print("\n✅ Analysis complete! Review the report before running actual removal.")
    print("💡 To actually remove files, modify the script to set dry_run=False")
    
    return redundancy_report


if __name__ == "__main__":
    main()

