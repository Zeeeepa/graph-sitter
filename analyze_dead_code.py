#!/usr/bin/env python3
"""
Comprehensive Dead Code Analysis for Contexten

This script analyzes all Python files in the contexten project to identify:
1. Files that are never imported
2. Core functionality mapping
3. Duplicate implementations
4. Missing features
"""

import os
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import re
import json

@dataclass
class FileAnalysis:
    """Analysis result for a single file"""
    filepath: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)  # classes, functions
    dependencies: List[str] = field(default_factory=list)  # files this imports from
    imported_by: List[str] = field(default_factory=list)  # files that import this
    lines_of_code: int = 0
    is_test: bool = False
    is_init: bool = False
    is_main: bool = False
    has_main_block: bool = False
    core_functionality: List[str] = field(default_factory=list)
    
@dataclass
class DeadCodeReport:
    """Complete dead code analysis report"""
    total_files: int = 0
    potentially_dead: List[str] = field(default_factory=list)
    core_features: Dict[str, List[str]] = field(default_factory=dict)
    duplicate_implementations: Dict[str, List[str]] = field(default_factory=dict)
    missing_features: List[str] = field(default_factory=list)
    import_graph: Dict[str, List[str]] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)

class ContextenAnalyzer:
    """Comprehensive analyzer for contexten codebase"""
    
    def __init__(self, root_path: str = "src/contexten"):
        self.root_path = Path(root_path)
        self.files: Dict[str, FileAnalysis] = {}
        self.report = DeadCodeReport()
        
        # Core feature patterns
        self.core_patterns = {
            "dashboard": ["dashboard", "ui", "web", "server", "app"],
            "agents": ["agent", "chat", "code", "tool"],
            "orchestration": ["orchestrat", "workflow", "flow", "task"],
            "extensions": ["extension", "integration", "plugin"],
            "linear": ["linear", "issue", "project"],
            "github": ["github", "git", "repo"],
            "slack": ["slack", "notification"],
            "cli": ["cli", "command", "main"],
            "mcp": ["mcp", "server", "protocol"],
            "shared": ["shared", "util", "common", "base"],
            "logging": ["log", "logger"],
            "config": ["config", "setting"],
            "auth": ["auth", "login", "token"],
            "api": ["api", "client", "request"],
            "database": ["db", "model", "schema"],
            "testing": ["test", "mock", "fixture"]
        }
    
    def analyze(self) -> DeadCodeReport:
        """Run complete analysis"""
        print("🔍 Starting comprehensive dead code analysis...")
        
        # Step 1: Discover all Python files
        self._discover_files()
        print(f"📁 Found {len(self.files)} Python files")
        
        # Step 2: Analyze each file
        self._analyze_files()
        print("📊 Analyzed file contents and dependencies")
        
        # Step 3: Build import graph
        self._build_import_graph()
        print("🕸️ Built import dependency graph")
        
        # Step 4: Identify entry points
        self._identify_entry_points()
        print(f"🚪 Found {len(self.report.entry_points)} entry points")
        
        # Step 5: Find potentially dead code
        self._find_dead_code()
        print(f"💀 Found {len(self.report.potentially_dead)} potentially dead files")
        
        # Step 6: Categorize core features
        self._categorize_core_features()
        print("🎯 Categorized core features")
        
        # Step 7: Find duplicates
        self._find_duplicates()
        print("🔄 Analyzed duplicate implementations")
        
        # Step 8: Identify missing features
        self._identify_missing_features()
        print("❓ Identified missing features")
        
        self.report.total_files = len(self.files)
        return self.report
    
    def _discover_files(self):
        """Discover all Python files"""
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                rel_path = str(py_file.relative_to(self.root_path))
                self.files[rel_path] = FileAnalysis(filepath=rel_path)
    
    def _analyze_files(self):
        """Analyze each file's content"""
        for rel_path, analysis in self.files.items():
            full_path = self.root_path / rel_path
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic file properties
                analysis.lines_of_code = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
                analysis.is_test = 'test' in rel_path.lower()
                analysis.is_init = rel_path.endswith('__init__.py')
                analysis.is_main = rel_path.endswith('main.py') or 'main' in rel_path
                analysis.has_main_block = 'if __name__ == "__main__"' in content
                
                # Parse AST for imports and exports
                try:
                    tree = ast.parse(content)
                    self._extract_imports_exports(tree, analysis)
                except SyntaxError:
                    print(f"⚠️ Syntax error in {rel_path}")
                
                # Identify core functionality
                self._identify_core_functionality(rel_path, content, analysis)
                
            except Exception as e:
                print(f"❌ Error analyzing {rel_path}: {e}")
    
    def _extract_imports_exports(self, tree: ast.AST, analysis: FileAnalysis):
        """Extract imports and exports from AST"""
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    analysis.imports.append(node.module)
                    # Track dependencies within contexten
                    if node.module.startswith('.') or 'contexten' in node.module:
                        analysis.dependencies.append(node.module)
            
            # Exports (classes and functions)
            elif isinstance(node, ast.ClassDef):
                analysis.exports.append(f"class:{node.name}")
            elif isinstance(node, ast.FunctionDef):
                analysis.exports.append(f"function:{node.name}")
            elif isinstance(node, ast.AsyncFunctionDef):
                analysis.exports.append(f"async_function:{node.name}")
    
    def _identify_core_functionality(self, filepath: str, content: str, analysis: FileAnalysis):
        """Identify what core functionality this file provides"""
        filepath_lower = filepath.lower()
        content_lower = content.lower()
        
        for feature, patterns in self.core_patterns.items():
            for pattern in patterns:
                if pattern in filepath_lower or pattern in content_lower:
                    analysis.core_functionality.append(feature)
                    break
    
    def _build_import_graph(self):
        """Build import dependency graph"""
        for rel_path, analysis in self.files.items():
            self.report.import_graph[rel_path] = analysis.dependencies
            
            # Find who imports this file
            module_name = rel_path.replace('/', '.').replace('.py', '')
            for other_path, other_analysis in self.files.items():
                for imp in other_analysis.imports:
                    if module_name in imp or rel_path in imp:
                        analysis.imported_by.append(other_path)
    
    def _identify_entry_points(self):
        """Identify entry points (files that are executed directly)"""
        entry_points = []
        
        for rel_path, analysis in self.files.items():
            # Main files
            if analysis.has_main_block:
                entry_points.append(rel_path)
            
            # CLI commands
            if 'cli' in rel_path and 'main.py' in rel_path:
                entry_points.append(rel_path)
            
            # Dashboard/server files
            if any(name in rel_path.lower() for name in ['dashboard', 'server', 'app']) and analysis.lines_of_code > 50:
                entry_points.append(rel_path)
            
            # MCP server
            if 'mcp' in rel_path and 'server' in rel_path:
                entry_points.append(rel_path)
        
        self.report.entry_points = entry_points
    
    def _find_dead_code(self):
        """Find potentially dead code using import analysis"""
        potentially_dead = []
        
        for rel_path, analysis in self.files.items():
            # Skip certain files that are typically not imported
            if (analysis.is_init or 
                analysis.has_main_block or 
                rel_path in self.report.entry_points or
                analysis.is_test):
                continue
            
            # Check if file is imported by others
            if not analysis.imported_by:
                # Additional checks for false positives
                if (analysis.lines_of_code > 10 and  # Not just empty files
                    not any(keyword in rel_path.lower() for keyword in ['__pycache__', '.pyc']) and
                    not rel_path.endswith('__init__.py')):
                    potentially_dead.append(rel_path)
        
        self.report.potentially_dead = potentially_dead
    
    def _categorize_core_features(self):
        """Categorize files by core features"""
        for feature in self.core_patterns.keys():
            self.report.core_features[feature] = []
        
        for rel_path, analysis in self.files.items():
            for feature in analysis.core_functionality:
                if feature in self.report.core_features:
                    self.report.core_features[feature].append(rel_path)
    
    def _find_duplicates(self):
        """Find potential duplicate implementations"""
        # Group by similar functionality
        functionality_groups = {}
        
        for rel_path, analysis in self.files.items():
            for export in analysis.exports:
                export_type, name = export.split(':', 1) if ':' in export else ('unknown', export)
                
                # Group similar names
                base_name = re.sub(r'(client|manager|handler|processor|agent|service)$', '', name.lower())
                if base_name not in functionality_groups:
                    functionality_groups[base_name] = []
                functionality_groups[base_name].append(rel_path)
        
        # Find groups with multiple implementations
        for name, files in functionality_groups.items():
            if len(files) > 1 and name:  # Skip empty names
                self.report.duplicate_implementations[name] = files
    
    def _identify_missing_features(self):
        """Identify missing core features"""
        expected_features = [
            "Authentication system",
            "Database models",
            "API documentation",
            "Configuration management",
            "Error handling middleware",
            "Logging configuration",
            "Testing utilities",
            "Deployment scripts"
        ]
        
        # This is a simplified check - in practice, you'd analyze more deeply
        for feature in expected_features:
            # Check if feature exists in codebase
            feature_found = False
            for rel_path, analysis in self.files.items():
                if any(keyword in rel_path.lower() for keyword in feature.lower().split()):
                    feature_found = True
                    break
            
            if not feature_found:
                self.report.missing_features.append(feature)

def generate_report(report: DeadCodeReport) -> str:
    """Generate comprehensive markdown report"""
    
    md_report = f"""# Contexten Dead Code Analysis Report

## 📊 Summary

- **Total Files Analyzed**: {report.total_files}
- **Potentially Dead Files**: {len(report.potentially_dead)}
- **Entry Points**: {len(report.entry_points)}
- **Core Feature Categories**: {len(report.core_features)}
- **Potential Duplicates**: {len(report.duplicate_implementations)}
- **Missing Features**: {len(report.missing_features)}

## 🚪 Entry Points (Files that are executed directly)

These files are definitely NOT dead code as they serve as entry points:

"""
    
    for entry_point in report.entry_points:
        md_report += f"- `{entry_point}`\n"
    
    md_report += f"""

## 💀 Potentially Dead Code ({len(report.potentially_dead)} files)

These files are not imported by any other files and may be dead code:

"""
    
    # Group dead code by category
    dead_by_category = {}
    for dead_file in report.potentially_dead:
        category = dead_file.split('/')[0] if '/' in dead_file else 'root'
        if category not in dead_by_category:
            dead_by_category[category] = []
        dead_by_category[category].append(dead_file)
    
    for category, files in sorted(dead_by_category.items()):
        md_report += f"\n### {category.title()} ({len(files)} files)\n\n"
        for file in sorted(files):
            md_report += f"- `{file}`\n"
    
    md_report += f"""

## 🎯 Core Features Analysis

"""
    
    for feature, files in report.core_features.items():
        if files:  # Only show features that have files
            md_report += f"\n### {feature.title()} ({len(files)} files)\n\n"
            for file in sorted(files)[:10]:  # Show first 10 files
                md_report += f"- `{file}`\n"
            if len(files) > 10:
                md_report += f"- ... and {len(files) - 10} more files\n"
    
    md_report += f"""

## 🔄 Potential Duplicate Implementations

"""
    
    if report.duplicate_implementations:
        for name, files in report.duplicate_implementations.items():
            if len(files) > 1:
                md_report += f"\n### {name.title()}\n\n"
                for file in files:
                    md_report += f"- `{file}`\n"
    else:
        md_report += "No obvious duplicate implementations found.\n"
    
    md_report += f"""

## ❓ Missing Features

"""
    
    if report.missing_features:
        for feature in report.missing_features:
            md_report += f"- {feature}\n"
    else:
        md_report += "No obvious missing features identified.\n"
    
    md_report += f"""

## 🔍 Detailed Analysis by Category

### Dashboard Files
"""
    dashboard_files = report.core_features.get('dashboard', [])
    if dashboard_files:
        md_report += f"Found {len(dashboard_files)} dashboard-related files. "
        dead_dashboard = [f for f in dashboard_files if f in report.potentially_dead]
        if dead_dashboard:
            md_report += f"{len(dead_dashboard)} appear to be dead code:\n"
            for f in dead_dashboard:
                md_report += f"- `{f}`\n"
        else:
            md_report += "All appear to be in use.\n"
    else:
        md_report += "No dashboard files found.\n"
    
    md_report += f"""

### Agent Files
"""
    agent_files = report.core_features.get('agents', [])
    if agent_files:
        md_report += f"Found {len(agent_files)} agent-related files. "
        dead_agents = [f for f in agent_files if f in report.potentially_dead]
        if dead_agents:
            md_report += f"{len(dead_agents)} appear to be dead code:\n"
            for f in dead_agents:
                md_report += f"- `{f}`\n"
        else:
            md_report += "All appear to be in use.\n"
    else:
        md_report += "No agent files found.\n"
    
    md_report += f"""

### CLI Files
"""
    cli_files = report.core_features.get('cli', [])
    if cli_files:
        md_report += f"Found {len(cli_files)} CLI-related files. "
        dead_cli = [f for f in cli_files if f in report.potentially_dead]
        if dead_cli:
            md_report += f"{len(dead_cli)} appear to be dead code:\n"
            for f in dead_cli:
                md_report += f"- `{f}`\n"
        else:
            md_report += "All appear to be in use.\n"
    else:
        md_report += "No CLI files found.\n"
    
    md_report += f"""

## 🎯 Recommendations

### High Priority Actions
1. **Review Entry Points**: Ensure all {len(report.entry_points)} entry points are necessary
2. **Investigate Dead Code**: Manually review {len(report.potentially_dead)} potentially dead files
3. **Consolidate Duplicates**: Review {len(report.duplicate_implementations)} potential duplicate implementations

### Dead Code Removal Strategy
1. **Start with smallest files**: Remove files with <10 lines of code first
2. **Test after each removal**: Ensure functionality isn't broken
3. **Keep backups**: Maintain backups of removed files
4. **Remove incrementally**: Don't remove all files at once

### False Positive Checks
Before removing any file, verify it's not:
- Dynamically imported
- Used in configuration files
- Required for deployment
- Part of a plugin system
- Used in tests that weren't analyzed

---

*Analysis completed on {report.total_files} Python files*
"""
    
    return md_report

def main():
    """Main analysis function"""
    analyzer = ContextenAnalyzer()
    report = analyzer.analyze()
    
    # Generate markdown report
    md_report = generate_report(report)
    
    # Save report
    with open('DEAD_CODE_ANALYSIS_REPORT.md', 'w') as f:
        f.write(md_report)
    
    # Save JSON data for further analysis
    report_data = {
        'total_files': report.total_files,
        'potentially_dead': report.potentially_dead,
        'entry_points': report.entry_points,
        'core_features': report.core_features,
        'duplicate_implementations': report.duplicate_implementations,
        'missing_features': report.missing_features
    }
    
    with open('dead_code_analysis.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Report saved to: DEAD_CODE_ANALYSIS_REPORT.md")
    print(f"📊 Data saved to: dead_code_analysis.json")
    print(f"\n📈 Summary:")
    print(f"   - Total files: {report.total_files}")
    print(f"   - Potentially dead: {len(report.potentially_dead)}")
    print(f"   - Entry points: {len(report.entry_points)}")
    print(f"   - Core features: {len([f for files in report.core_features.values() for f in files])}")

if __name__ == "__main__":
    main()

