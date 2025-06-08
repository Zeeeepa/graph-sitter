#!/usr/bin/env python3
"""
Comprehensive Analysis of Graph-Sitter Implementation

This script analyzes the graph-sitter codebase to:
1. Compare implementation with official Tree-sitter documentation
2. Identify code errors, unused parameters, and issues
3. Consolidate analysis features
4. Provide recommendations based on official patterns
"""

import os
import sys
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict, Counter
import re

# Add our analysis modules to path
sys.path.insert(0, 'src')

from contexten.extensions.graph_sitter.analysis.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary, get_optimized_config
)
from contexten.extensions.graph_sitter.analysis.dead_code_detector import detect_dead_code
from contexten.extensions.graph_sitter.analysis.complexity_analyzer import analyze_complexity
from contexten.extensions.graph_sitter.analysis.dependency_analyzer import analyze_dependencies
from contexten.extensions.graph_sitter.analysis.security_analyzer import analyze_security
from contexten.extensions.graph_sitter.analysis.call_graph_analyzer import analyze_call_graph

class ComprehensiveAnalyzer:
    def __init__(self, target_repo_path: str):
        self.target_path = Path(target_repo_path)
        self.issues = []
        self.recommendations = []
        self.metrics = {}
        
    def analyze_tree_sitter_compliance(self) -> Dict[str, Any]:
        """Analyze compliance with official Tree-sitter patterns"""
        compliance_issues = []
        
        # Check for proper Tree-sitter parser usage
        parser_files = list(self.target_path.rglob("*parser*.py"))
        for file_path in parser_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper Language initialization
                if 'Language(' in content and 'tree_sitter_' in content:
                    self.recommendations.append(f"✅ {file_path.name}: Proper Tree-sitter Language usage found")
                else:
                    compliance_issues.append(f"❌ {file_path.name}: Missing proper Tree-sitter Language initialization")
                    
                # Check for Parser class usage
                if 'Parser(' in content:
                    self.recommendations.append(f"✅ {file_path.name}: Parser class properly used")
                else:
                    compliance_issues.append(f"❌ {file_path.name}: Missing Parser class usage")
                    
            except Exception as e:
                compliance_issues.append(f"❌ Error analyzing {file_path}: {e}")
                
        return {
            "compliance_issues": compliance_issues,
            "total_parser_files": len(parser_files)
        }
    
    def find_unused_parameters(self) -> Dict[str, List[str]]:
        """Find unused parameters in function definitions"""
        unused_params = defaultdict(list)
        
        python_files = list(self.target_path.rglob("*.py"))
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get parameter names
                        param_names = [arg.arg for arg in node.args.args]
                        
                        # Get all names used in function body
                        used_names = set()
                        for child in ast.walk(node):
                            if isinstance(child, ast.Name):
                                used_names.add(child.id)
                                
                        # Find unused parameters (excluding 'self', 'cls', and underscore prefixed)
                        for param in param_names:
                            if (param not in used_names and 
                                param not in ['self', 'cls'] and 
                                not param.startswith('_')):
                                unused_params[str(file_path)].append(f"{node.name}({param})")
                                
            except Exception as e:
                self.issues.append(f"Error analyzing {file_path}: {e}")
                
        return dict(unused_params)
    
    def find_code_errors(self) -> Dict[str, List[str]]:
        """Find potential code errors and issues"""
        errors = defaultdict(list)
        
        python_files = list(self.target_path.rglob("*.py"))
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for syntax errors
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    errors[str(file_path)].append(f"Syntax error: {e}")
                    continue
                    
                # Check for common issues
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Unused imports (basic check)
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        import_name = line.split()[-1] if 'import' in line else line.split()[1]
                        if import_name not in content.replace(line, ''):
                            errors[str(file_path)].append(f"Line {i}: Potentially unused import: {line.strip()}")
                    
                    # TODO comments
                    if 'TODO' in line.upper() or 'FIXME' in line.upper():
                        errors[str(file_path)].append(f"Line {i}: TODO/FIXME found: {line.strip()}")
                    
                    # Long lines (>120 chars)
                    if len(line) > 120:
                        errors[str(file_path)].append(f"Line {i}: Line too long ({len(line)} chars)")
                        
            except Exception as e:
                errors[str(file_path)].append(f"Error analyzing file: {e}")
                
        return dict(errors)
    
    def analyze_architecture_patterns(self) -> Dict[str, Any]:
        """Analyze architectural patterns and suggest improvements"""
        patterns = {
            "factory_pattern": 0,
            "singleton_pattern": 0,
            "observer_pattern": 0,
            "strategy_pattern": 0,
            "builder_pattern": 0
        }
        
        python_files = list(self.target_path.rglob("*.py"))
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for design patterns
                if 'factory' in content.lower():
                    patterns["factory_pattern"] += 1
                if '_instance' in content and 'None' in content:
                    patterns["singleton_pattern"] += 1
                if 'observer' in content.lower() or 'notify' in content.lower():
                    patterns["observer_pattern"] += 1
                if 'strategy' in content.lower():
                    patterns["strategy_pattern"] += 1
                if 'builder' in content.lower():
                    patterns["builder_pattern"] += 1
                    
            except Exception:
                continue
                
        return patterns
    
    def generate_consolidation_recommendations(self) -> List[str]:
        """Generate recommendations for code consolidation"""
        recommendations = []
        
        # Find duplicate function names across files
        function_names = defaultdict(list)
        python_files = list(self.target_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_names[node.name].append(str(file_path))
                        
            except Exception:
                continue
        
        # Find potential duplicates
        for func_name, files in function_names.items():
            if len(files) > 1 and not func_name.startswith('_'):
                recommendations.append(f"Function '{func_name}' appears in {len(files)} files: {files}")
        
        # Check for similar file names
        file_names = [f.name for f in python_files]
        similar_files = []
        for i, name1 in enumerate(file_names):
            for name2 in file_names[i+1:]:
                if name1 != name2 and (name1 in name2 or name2 in name1):
                    similar_files.append((name1, name2))
        
        if similar_files:
            recommendations.append(f"Similar file names found (potential consolidation candidates): {similar_files}")
            
        return recommendations
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run all analysis modules and generate comprehensive report"""
        print("🔍 Starting comprehensive analysis...")
        
        # Tree-sitter compliance analysis
        print("📋 Analyzing Tree-sitter compliance...")
        compliance = self.analyze_tree_sitter_compliance()
        
        # Code quality analysis
        print("🔧 Finding unused parameters...")
        unused_params = self.find_unused_parameters()
        
        print("❌ Finding code errors...")
        code_errors = self.find_code_errors()
        
        print("🏗️ Analyzing architecture patterns...")
        patterns = self.analyze_architecture_patterns()
        
        print("📦 Generating consolidation recommendations...")
        consolidation_recs = self.generate_consolidation_recommendations()
        
        # Calculate metrics
        total_files = len(list(self.target_path.rglob("*.py")))
        total_lines = 0
        for file_path in self.target_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except Exception:
                continue
        
        self.metrics = {
            "total_python_files": total_files,
            "total_lines_of_code": total_lines,
            "files_with_unused_params": len(unused_params),
            "files_with_errors": len(code_errors),
            "total_issues": sum(len(issues) for issues in code_errors.values()),
            "total_unused_params": sum(len(params) for params in unused_params.values())
        }
        
        return {
            "metrics": self.metrics,
            "tree_sitter_compliance": compliance,
            "unused_parameters": unused_params,
            "code_errors": code_errors,
            "architecture_patterns": patterns,
            "consolidation_recommendations": consolidation_recs,
            "general_recommendations": self.recommendations,
            "issues": self.issues
        }

def main():
    target_repo = "/tmp/codegen-graph-sitter"
    
    if not os.path.exists(target_repo):
        print(f"❌ Target repository not found: {target_repo}")
        return
    
    analyzer = ComprehensiveAnalyzer(target_repo)
    results = analyzer.run_comprehensive_analysis()
    
    # Generate report
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📈 METRICS:")
    for key, value in results["metrics"].items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🌳 TREE-SITTER COMPLIANCE:")
    compliance = results["tree_sitter_compliance"]
    print(f"  • Parser files found: {compliance['total_parser_files']}")
    for issue in compliance["compliance_issues"]:
        print(f"  • {issue}")
    
    print(f"\n🔧 UNUSED PARAMETERS:")
    unused = results["unused_parameters"]
    if unused:
        for file_path, params in list(unused.items())[:5]:  # Show first 5
            print(f"  • {Path(file_path).name}: {params}")
        if len(unused) > 5:
            print(f"  • ... and {len(unused) - 5} more files")
    else:
        print("  • ✅ No unused parameters found!")
    
    print(f"\n❌ CODE ERRORS:")
    errors = results["code_errors"]
    if errors:
        for file_path, file_errors in list(errors.items())[:3]:  # Show first 3
            print(f"  • {Path(file_path).name}:")
            for error in file_errors[:3]:  # Show first 3 errors per file
                print(f"    - {error}")
        if len(errors) > 3:
            print(f"  • ... and {len(errors) - 3} more files with errors")
    else:
        print("  • ✅ No major code errors found!")
    
    print(f"\n🏗️ ARCHITECTURE PATTERNS:")
    patterns = results["architecture_patterns"]
    for pattern, count in patterns.items():
        print(f"  • {pattern.replace('_', ' ').title()}: {count} occurrences")
    
    print(f"\n📦 CONSOLIDATION RECOMMENDATIONS:")
    consolidation = results["consolidation_recommendations"]
    if consolidation:
        for rec in consolidation[:5]:  # Show first 5
            print(f"  • {rec}")
    else:
        print("  • ✅ No obvious consolidation opportunities found!")
    
    print(f"\n💡 GENERAL RECOMMENDATIONS:")
    for rec in results["general_recommendations"]:
        print(f"  • {rec}")
    
    # Save detailed report
    report_file = "analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

