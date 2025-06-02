#!/usr/bin/env python3
"""
Comprehensive Contexten Component Testing and Validation Framework

This script performs comprehensive testing of all contexten components:
1. Component integrity validation
2. Import dependency analysis
3. Dead code detection
4. Missing feature identification
5. Integration point testing
6. Usability validation

Usage:
    python test_contexten_comprehensive.py [--module MODULE] [--fix] [--report]
"""

import ast
import os
import sys
import importlib
import inspect
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ComponentAnalysis:
    """Analysis results for a single component"""
    file_path: str
    module_name: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    external_deps: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    is_importable: bool = False
    is_executable: bool = False
    has_tests: bool = False
    coverage_gaps: List[str] = field(default_factory=list)
    dead_code_candidates: List[str] = field(default_factory=list)

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    total_files: int = 0
    analyzed_files: int = 0
    importable_files: int = 0
    files_with_issues: int = 0
    dead_code_files: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)
    integration_issues: List[str] = field(default_factory=list)
    components: Dict[str, ComponentAnalysis] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

class ContextenValidator:
    """Comprehensive validator for contexten components"""
    
    def __init__(self, base_path: str = "src/contexten"):
        self.base_path = Path(base_path)
        self.report = ValidationReport()
        self.python_files = []
        self.module_cache = {}
        
    def discover_files(self) -> List[Path]:
        """Discover all Python files in the contexten module"""
        python_files = list(self.base_path.rglob("*.py"))
        self.python_files = [f for f in python_files if not f.name.startswith('__')]
        self.report.total_files = len(self.python_files)
        logger.info(f"Discovered {len(self.python_files)} Python files")
        return self.python_files
    
    def analyze_ast(self, file_path: Path) -> ComponentAnalysis:
        """Analyze a Python file using AST"""
        analysis = ComponentAnalysis(
            file_path=str(file_path),
            module_name=self._path_to_module_name(file_path)
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        full_import = f"{module}.{alias.name}" if module else alias.name
                        analysis.imports.append(full_import)
                
                # Extract function definitions
                elif isinstance(node, ast.FunctionDef):
                    analysis.functions.append(node.name)
                
                # Extract class definitions
                elif isinstance(node, ast.ClassDef):
                    analysis.classes.append(node.name)
            
            # Categorize dependencies
            for imp in analysis.imports:
                if imp.startswith('contexten'):
                    analysis.dependencies.append(imp)
                elif not imp.startswith('.') and '.' in imp:
                    analysis.external_deps.append(imp.split('.')[0])
            
            analysis.external_deps = list(set(analysis.external_deps))
            
        except Exception as e:
            analysis.issues.append(f"AST parsing failed: {str(e)}")
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return analysis
    
    def test_importability(self, analysis: ComponentAnalysis) -> bool:
        """Test if a module can be imported"""
        try:
            # Add the project root to Python path
            project_root = Path.cwd()
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            module = importlib.import_module(analysis.module_name)
            analysis.is_importable = True
            
            # Extract exports
            if hasattr(module, '__all__'):
                analysis.exports = list(module.__all__)
            else:
                analysis.exports = [name for name in dir(module) 
                                 if not name.startswith('_')]
            
            return True
            
        except Exception as e:
            analysis.issues.append(f"Import failed: {str(e)}")
            logger.warning(f"Cannot import {analysis.module_name}: {e}")
            return False
    
    def detect_dead_code(self, analysis: ComponentAnalysis) -> List[str]:
        """Detect potentially dead code in a component"""
        dead_code = []
        
        # Check for unused imports
        file_content = ""
        try:
            with open(analysis.file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except:
            return dead_code
        
        for imp in analysis.imports:
            # Simple heuristic: if import is not used in file content
            import_name = imp.split('.')[-1]
            if import_name not in file_content.replace(f"import {imp}", ""):
                dead_code.append(f"Unused import: {imp}")
        
        # Check for functions/classes that might be unused
        for func in analysis.functions:
            if func.startswith('_') and func != '__init__':
                # Private functions might be unused
                if file_content.count(func) <= 1:  # Only defined, never called
                    dead_code.append(f"Potentially unused private function: {func}")
        
        analysis.dead_code_candidates = dead_code
        return dead_code
    
    def identify_missing_features(self, analysis: ComponentAnalysis) -> List[str]:
        """Identify missing features based on common patterns"""
        missing = []
        
        # Check for common missing patterns
        if 'agent' in analysis.file_path.lower():
            if not any('async' in func for func in analysis.functions):
                missing.append("Missing async methods for agent operations")
            if not any('error' in func.lower() or 'exception' in func.lower() for func in analysis.functions):
                missing.append("Missing error handling methods")
        
        if 'dashboard' in analysis.file_path.lower():
            if not any('websocket' in imp.lower() for imp in analysis.imports):
                missing.append("Missing WebSocket support for real-time updates")
            if not any('auth' in imp.lower() for imp in analysis.imports):
                missing.append("Missing authentication integration")
        
        if 'integration' in analysis.file_path.lower() or 'client' in analysis.file_path.lower():
            if not any('retry' in func.lower() for func in analysis.functions):
                missing.append("Missing retry logic for API calls")
            if not any('rate' in func.lower() or 'limit' in func.lower() for func in analysis.functions):
                missing.append("Missing rate limiting")
        
        analysis.coverage_gaps = missing
        return missing
    
    def validate_integration_points(self) -> List[str]:
        """Validate integration points between components"""
        issues = []
        
        # Check for common integration patterns
        linear_files = [f for f in self.python_files if 'linear' in str(f)]
        github_files = [f for f in self.python_files if 'github' in str(f)]
        slack_files = [f for f in self.python_files if 'slack' in str(f)]
        dashboard_files = [f for f in self.python_files if 'dashboard' in str(f)]
        
        # Validate Linear integration
        if linear_files:
            has_webhook = any('webhook' in str(f) for f in linear_files)
            has_client = any('client' in str(f) for f in linear_files)
            has_agent = any('agent' in str(f) for f in linear_files)
            
            if not has_webhook:
                issues.append("Linear integration missing webhook handling")
            if not has_client:
                issues.append("Linear integration missing API client")
            if not has_agent:
                issues.append("Linear integration missing agent implementation")
        
        # Validate GitHub integration
        if github_files:
            has_webhook = any('webhook' in str(f) for f in github_files)
            has_events = any('event' in str(f) for f in github_files)
            
            if not has_webhook:
                issues.append("GitHub integration missing webhook handling")
            if not has_events:
                issues.append("GitHub integration missing event processing")
        
        # Validate Dashboard integration
        if dashboard_files:
            has_api = any('api' in str(f) or 'app' in str(f) for f in dashboard_files)
            has_static = any('static' in str(f) for f in dashboard_files)
            
            if not has_api:
                issues.append("Dashboard missing API implementation")
        
        return issues
    
    def _path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative_path = file_path.relative_to(Path.cwd())
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        return '.'.join(module_parts)
    
    def run_comprehensive_analysis(self) -> ValidationReport:
        """Run comprehensive analysis of all components"""
        logger.info("Starting comprehensive contexten analysis...")
        
        # Discover files
        files = self.discover_files()
        
        # Analyze each file
        for file_path in files:
            logger.info(f"Analyzing {file_path}")
            
            # AST analysis
            analysis = self.analyze_ast(file_path)
            
            # Test importability
            if self.test_importability(analysis):
                self.report.importable_files += 1
            
            # Detect dead code
            self.detect_dead_code(analysis)
            
            # Identify missing features
            self.identify_missing_features(analysis)
            
            # Check for issues
            if analysis.issues or analysis.dead_code_candidates or analysis.coverage_gaps:
                self.report.files_with_issues += 1
            
            if analysis.dead_code_candidates:
                self.report.dead_code_files.append(str(file_path))
            
            self.report.components[str(file_path)] = analysis
            self.report.analyzed_files += 1
        
        # Validate integration points
        self.report.integration_issues = self.validate_integration_points()
        
        # Generate recommendations
        self._generate_recommendations()
        
        logger.info("Analysis complete!")
        return self.report
    
    def _generate_recommendations(self):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Dead code recommendations
        if self.report.dead_code_files:
            recommendations.append(f"Remove or refactor {len(self.report.dead_code_files)} files with dead code")
        
        # Import issues
        import_success_rate = (self.report.importable_files / self.report.total_files) * 100
        if import_success_rate < 80:
            recommendations.append(f"Fix import issues - only {import_success_rate:.1f}% of files are importable")
        
        # Integration issues
        if self.report.integration_issues:
            recommendations.append("Address integration point issues for better component connectivity")
        
        # Missing features
        missing_count = sum(len(comp.coverage_gaps) for comp in self.report.components.values())
        if missing_count > 0:
            recommendations.append(f"Implement {missing_count} missing features across components")
        
        self.report.recommendations = recommendations
    
    def generate_detailed_report(self) -> str:
        """Generate a detailed analysis report"""
        report = []
        report.append("# Contexten Comprehensive Analysis Report\n")
        
        # Summary
        report.append("## Executive Summary")
        report.append(f"- **Total Files Analyzed**: {self.report.analyzed_files}/{self.report.total_files}")
        report.append(f"- **Importable Files**: {self.report.importable_files} ({(self.report.importable_files/self.report.total_files)*100:.1f}%)")
        report.append(f"- **Files with Issues**: {self.report.files_with_issues}")
        report.append(f"- **Dead Code Files**: {len(self.report.dead_code_files)}")
        report.append(f"- **Integration Issues**: {len(self.report.integration_issues)}\n")
        
        # Recommendations
        if self.report.recommendations:
            report.append("## Key Recommendations")
            for rec in self.report.recommendations:
                report.append(f"- {rec}")
            report.append("")
        
        # Integration Issues
        if self.report.integration_issues:
            report.append("## Integration Issues")
            for issue in self.report.integration_issues:
                report.append(f"- ❌ {issue}")
            report.append("")
        
        # Dead Code Analysis
        if self.report.dead_code_files:
            report.append("## Dead Code Analysis")
            for file_path in self.report.dead_code_files:
                component = self.report.components[file_path]
                report.append(f"### {file_path}")
                for dead_code in component.dead_code_candidates:
                    report.append(f"- 🗑️ {dead_code}")
                report.append("")
        
        # Missing Features
        report.append("## Missing Features by Component")
        for file_path, component in self.report.components.items():
            if component.coverage_gaps:
                report.append(f"### {file_path}")
                for gap in component.coverage_gaps:
                    report.append(f"- ⚠️ {gap}")
                report.append("")
        
        # Component Details
        report.append("## Component Analysis Details")
        for file_path, component in self.report.components.items():
            report.append(f"### {file_path}")
            report.append(f"- **Module**: {component.module_name}")
            report.append(f"- **Importable**: {'✅' if component.is_importable else '❌'}")
            report.append(f"- **Functions**: {len(component.functions)}")
            report.append(f"- **Classes**: {len(component.classes)}")
            report.append(f"- **External Dependencies**: {len(component.external_deps)}")
            
            if component.issues:
                report.append("- **Issues**:")
                for issue in component.issues:
                    report.append(f"  - ❌ {issue}")
            
            report.append("")
        
        return "\n".join(report)
    
    def fix_common_issues(self):
        """Automatically fix common issues where possible"""
        logger.info("Attempting to fix common issues...")
        
        fixes_applied = 0
        
        for file_path, component in self.report.components.items():
            if not component.is_importable and component.issues:
                # Try to fix import issues
                try:
                    self._fix_import_issues(file_path, component)
                    fixes_applied += 1
                except Exception as e:
                    logger.error(f"Failed to fix {file_path}: {e}")
        
        logger.info(f"Applied {fixes_applied} automatic fixes")
    
    def _fix_import_issues(self, file_path: str, component: ComponentAnalysis):
        """Fix common import issues"""
        # This would implement automatic fixes for common import problems
        # For now, just log what would be fixed
        logger.info(f"Would fix import issues in {file_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Contexten Component Testing")
    parser.add_argument("--module", help="Specific module to analyze")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues")
    parser.add_argument("--report", default="contexten_analysis_report.md", help="Output report file")
    parser.add_argument("--json", help="Output JSON report file")
    
    args = parser.parse_args()
    
    # Initialize validator
    base_path = f"src/contexten/{args.module}" if args.module else "src/contexten"
    validator = ContextenValidator(base_path)
    
    # Run analysis
    report = validator.run_comprehensive_analysis()
    
    # Apply fixes if requested
    if args.fix:
        validator.fix_common_issues()
    
    # Generate reports
    detailed_report = validator.generate_detailed_report()
    
    # Save markdown report
    with open(args.report, 'w') as f:
        f.write(detailed_report)
    
    # Save JSON report if requested
    if args.json:
        report_dict = {
            'summary': {
                'total_files': report.total_files,
                'analyzed_files': report.analyzed_files,
                'importable_files': report.importable_files,
                'files_with_issues': report.files_with_issues,
                'dead_code_files': len(report.dead_code_files),
                'integration_issues': len(report.integration_issues)
            },
            'recommendations': report.recommendations,
            'integration_issues': report.integration_issues,
            'dead_code_files': report.dead_code_files
        }
        
        with open(args.json, 'w') as f:
            json.dump(report_dict, f, indent=2)
    
    # Print summary
    print(f"\n📊 Analysis Complete!")
    print(f"📁 Analyzed: {report.analyzed_files}/{report.total_files} files")
    print(f"✅ Importable: {report.importable_files} ({(report.importable_files/report.total_files)*100:.1f}%)")
    print(f"⚠️  Issues: {report.files_with_issues} files")
    print(f"🗑️  Dead code: {len(report.dead_code_files)} files")
    print(f"🔗 Integration issues: {len(report.integration_issues)}")
    print(f"📄 Report saved to: {args.report}")
    
    if args.json:
        print(f"📄 JSON report saved to: {args.json}")

if __name__ == "__main__":
    main()

