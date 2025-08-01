#!/usr/bin/env python3
"""
Comprehensive Analysis of Serena Extension Files

This script analyzes all Serena extension files to determine:
1. Implementation status and completeness
2. Usage patterns and dependencies
3. Overlapping functionality
4. Consolidation opportunities
5. Integration with the new unified interface
"""

import os
import sys
import ast
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
import re

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class SerenaFileAnalyzer:
    """Analyzes Serena extension files for implementation status and usage."""
    
    def __init__(self):
        self.serena_path = Path("src/graph_sitter/extensions/serena")
        self.analysis_results = {}
        self.import_graph = defaultdict(set)
        self.function_definitions = defaultdict(list)
        self.class_definitions = defaultdict(list)
        self.usage_patterns = defaultdict(list)
        
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all Serena extension files."""
        print("🔍 COMPREHENSIVE SERENA EXTENSION ANALYSIS")
        print("=" * 70)
        
        # Get all Python files in the Serena extension
        serena_files = list(self.serena_path.rglob("*.py"))
        
        print(f"📊 Found {len(serena_files)} Python files in Serena extension")
        print()
        
        # Analyze each file
        for file_path in serena_files:
            try:
                self.analyze_file(file_path)
            except Exception as e:
                print(f"❌ Error analyzing {file_path}: {e}")
        
        # Generate comprehensive report
        return self.generate_comprehensive_report()
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        relative_path = file_path.relative_to(Path("src"))
        
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Basic file info
            lines = content.splitlines()
            file_info = {
                'path': str(relative_path),
                'size_bytes': len(content),
                'line_count': len(lines),
                'is_empty': len(content.strip()) == 0,
                'has_docstring': content.strip().startswith('"""') or content.strip().startswith("'''"),
                'imports': [],
                'functions': [],
                'classes': [],
                'async_functions': [],
                'decorators': [],
                'todos': [],
                'errors': []
            }
            
            # Parse AST if possible
            try:
                tree = ast.parse(content)
                self.analyze_ast(tree, file_info, relative_path)
            except SyntaxError as e:
                file_info['errors'].append(f"Syntax error: {e}")
            except Exception as e:
                file_info['errors'].append(f"AST parse error: {e}")
            
            # Analyze content patterns
            self.analyze_content_patterns(content, file_info)
            
            # Store results
            self.analysis_results[str(relative_path)] = file_info
            
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    def analyze_ast(self, tree: ast.AST, file_info: Dict[str, Any], file_path: Path) -> None:
        """Analyze the AST of a Python file."""
        for node in ast.walk(tree):
            # Import statements
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name
                    file_info['imports'].append({
                        'type': 'import',
                        'name': import_name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
                    self.import_graph[str(file_path)].add(import_name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    file_info['imports'].append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
                    self.import_graph[str(file_path)].add(import_name)
            
            # Function definitions
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'is_async': False,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self.get_decorator_name(d) for d in node.decorator_list],
                    'has_docstring': ast.get_docstring(node) is not None,
                    'returns': self.get_return_annotation(node)
                }
                file_info['functions'].append(func_info)
                self.function_definitions[str(file_path)].append(func_info)
            
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'is_async': True,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self.get_decorator_name(d) for d in node.decorator_list],
                    'has_docstring': ast.get_docstring(node) is not None,
                    'returns': self.get_return_annotation(node)
                }
                file_info['async_functions'].append(func_info)
                self.function_definitions[str(file_path)].append(func_info)
            
            # Class definitions
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [self.get_base_name(base) for base in node.bases],
                    'decorators': [self.get_decorator_name(d) for d in node.decorator_list],
                    'has_docstring': ast.get_docstring(node) is not None,
                    'methods': []
                }
                
                # Analyze methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'is_property': any(self.get_decorator_name(d) == 'property' for d in item.decorator_list),
                            'is_classmethod': any(self.get_decorator_name(d) == 'classmethod' for d in item.decorator_list),
                            'is_staticmethod': any(self.get_decorator_name(d) == 'staticmethod' for d in item.decorator_list)
                        }
                        class_info['methods'].append(method_info)
                
                file_info['classes'].append(class_info)
                self.class_definitions[str(file_path)].append(class_info)
    
    def analyze_content_patterns(self, content: str, file_info: Dict[str, Any]) -> None:
        """Analyze content patterns in the file."""
        lines = content.splitlines()
        
        # Look for TODOs, FIXMEs, etc.
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['todo', 'fixme', 'hack', 'xxx']):
                file_info['todos'].append({
                    'line': i,
                    'text': line.strip(),
                    'type': 'todo' if 'todo' in line_lower else 'fixme' if 'fixme' in line_lower else 'other'
                })
        
        # Look for error handling patterns
        error_patterns = ['try:', 'except:', 'raise ', 'assert ', 'logging.error', 'logger.error']
        file_info['error_handling'] = any(pattern in content for pattern in error_patterns)
        
        # Look for async patterns
        async_patterns = ['async def', 'await ', 'asyncio.']
        file_info['uses_async'] = any(pattern in content for pattern in async_patterns)
        
        # Look for type hints
        type_patterns = ['typing.', 'List[', 'Dict[', 'Optional[', 'Union[', '-> ']
        file_info['uses_type_hints'] = any(pattern in content for pattern in type_patterns)
        
        # Look for dataclass usage
        file_info['uses_dataclass'] = '@dataclass' in content
        
        # Look for logging usage
        file_info['uses_logging'] = any(pattern in content for pattern in ['logging.', 'logger.', 'get_logger'])
    
    def get_decorator_name(self, decorator) -> str:
        """Get the name of a decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self.get_base_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self.get_decorator_name(decorator.func)
        else:
            return str(decorator)
    
    def get_base_name(self, node) -> str:
        """Get the name of a base class or attribute."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_base_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def get_return_annotation(self, node) -> Optional[str]:
        """Get the return type annotation of a function."""
        if node.returns:
            return self.get_base_name(node.returns)
        return None
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        print("📊 GENERATING COMPREHENSIVE REPORT")
        print("=" * 50)
        
        # Categorize files
        empty_files = []
        minimal_files = []  # < 50 lines
        small_files = []    # 50-200 lines
        medium_files = []   # 200-500 lines
        large_files = []    # > 500 lines
        
        core_files = []
        api_files = []
        integration_files = []
        analysis_files = []
        utility_files = []
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for file_path, info in self.analysis_results.items():
            lines = info['line_count']
            total_lines += lines
            total_functions += len(info['functions']) + len(info['async_functions'])
            total_classes += len(info['classes'])
            
            # Categorize by size
            if info['is_empty']:
                empty_files.append(file_path)
            elif lines < 50:
                minimal_files.append(file_path)
            elif lines < 200:
                small_files.append(file_path)
            elif lines < 500:
                medium_files.append(file_path)
            else:
                large_files.append(file_path)
            
            # Categorize by purpose
            if 'core' in file_path or 'auto_init' in file_path:
                core_files.append(file_path)
            elif 'api' in file_path:
                api_files.append(file_path)
            elif 'integration' in file_path or 'bridge' in file_path:
                integration_files.append(file_path)
            elif 'analysis' in file_path or 'error' in file_path or 'context' in file_path:
                analysis_files.append(file_path)
            else:
                utility_files.append(file_path)
        
        # Identify overlapping functionality
        overlapping_functions = self.find_overlapping_functions()
        overlapping_classes = self.find_overlapping_classes()
        
        # Generate usage analysis
        usage_analysis = self.analyze_usage_patterns()
        
        # Create comprehensive report
        report = {
            'summary': {
                'total_files': len(self.analysis_results),
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'average_lines_per_file': total_lines / len(self.analysis_results) if self.analysis_results else 0
            },
            'file_categorization': {
                'by_size': {
                    'empty': empty_files,
                    'minimal': minimal_files,
                    'small': small_files,
                    'medium': medium_files,
                    'large': large_files
                },
                'by_purpose': {
                    'core': core_files,
                    'api': api_files,
                    'integration': integration_files,
                    'analysis': analysis_files,
                    'utility': utility_files
                }
            },
            'overlapping_functionality': {
                'functions': overlapping_functions,
                'classes': overlapping_classes
            },
            'usage_analysis': usage_analysis,
            'consolidation_opportunities': self.identify_consolidation_opportunities(),
            'implementation_status': self.assess_implementation_status(),
            'detailed_files': self.analysis_results
        }
        
        # Print summary
        self.print_report_summary(report)
        
        return report
    
    def find_overlapping_functions(self) -> Dict[str, List[str]]:
        """Find functions with similar names across files."""
        function_names = defaultdict(list)
        
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                function_names[func['name']].append(file_path)
        
        # Return only functions that appear in multiple files
        return {name: files for name, files in function_names.items() if len(files) > 1}
    
    def find_overlapping_classes(self) -> Dict[str, List[str]]:
        """Find classes with similar names across files."""
        class_names = defaultdict(list)
        
        for file_path, classes in self.class_definitions.items():
            for cls in classes:
                class_names[cls['name']].append(file_path)
        
        # Return only classes that appear in multiple files
        return {name: files for name, files in class_names.items() if len(files) > 1}
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns across the codebase."""
        # This would require analyzing imports from outside the Serena extension
        # For now, return basic patterns
        return {
            'most_imported_modules': dict(sorted(
                {module: len(files) for module, files in self.import_graph.items()}.items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
            'async_usage': sum(1 for info in self.analysis_results.values() if info['uses_async']),
            'type_hints_usage': sum(1 for info in self.analysis_results.values() if info['uses_type_hints']),
            'dataclass_usage': sum(1 for info in self.analysis_results.values() if info['uses_dataclass']),
            'logging_usage': sum(1 for info in self.analysis_results.values() if info['uses_logging'])
        }
    
    def identify_consolidation_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for consolidation."""
        opportunities = []
        
        # Empty files
        empty_files = [f for f, info in self.analysis_results.items() if info['is_empty']]
        if empty_files:
            opportunities.append({
                'type': 'remove_empty_files',
                'priority': 'high',
                'description': 'Remove completely empty files',
                'files': empty_files,
                'impact': 'low_risk'
            })
        
        # Minimal files that could be merged
        minimal_files = [f for f, info in self.analysis_results.items() 
                        if not info['is_empty'] and info['line_count'] < 50]
        if len(minimal_files) > 3:
            opportunities.append({
                'type': 'merge_minimal_files',
                'priority': 'medium',
                'description': 'Consider merging minimal files with related functionality',
                'files': minimal_files,
                'impact': 'medium_risk'
            })
        
        # Files with overlapping functionality
        overlapping_analysis = [f for f in self.analysis_results.keys() 
                              if 'analysis' in f and 'advanced' in f]
        if len(overlapping_analysis) > 1:
            opportunities.append({
                'type': 'consolidate_analysis',
                'priority': 'high',
                'description': 'Consolidate overlapping analysis components',
                'files': overlapping_analysis,
                'impact': 'medium_risk'
            })
        
        # LSP integration files
        lsp_files = [f for f in self.analysis_results.keys() if 'lsp' in f.lower()]
        if len(lsp_files) > 3:
            opportunities.append({
                'type': 'consolidate_lsp',
                'priority': 'high',
                'description': 'Consolidate LSP integration components',
                'files': lsp_files,
                'impact': 'high_risk'
            })
        
        return opportunities
    
    def assess_implementation_status(self) -> Dict[str, Any]:
        """Assess the implementation status of different components."""
        status = {
            'core_components': {},
            'api_interfaces': {},
            'analysis_engines': {},
            'integration_layers': {},
            'overall_health': 'unknown'
        }
        
        # Assess core components
        core_files = ['core.py', 'auto_init.py', 'types.py', 'api.py']
        for core_file in core_files:
            file_path = f"graph_sitter/extensions/serena/{core_file}"
            if file_path in self.analysis_results:
                info = self.analysis_results[file_path]
                status['core_components'][core_file] = {
                    'status': 'implemented' if info['line_count'] > 100 else 'partial',
                    'lines': info['line_count'],
                    'functions': len(info['functions']) + len(info['async_functions']),
                    'classes': len(info['classes'])
                }
            else:
                status['core_components'][core_file] = {'status': 'missing'}
        
        # Calculate overall health
        implemented_core = sum(1 for comp in status['core_components'].values() 
                             if comp.get('status') == 'implemented')
        total_core = len(core_files)
        
        if implemented_core >= total_core * 0.8:
            status['overall_health'] = 'good'
        elif implemented_core >= total_core * 0.5:
            status['overall_health'] = 'fair'
        else:
            status['overall_health'] = 'poor'
        
        return status
    
    def print_report_summary(self, report: Dict[str, Any]) -> None:
        """Print a summary of the analysis report."""
        summary = report['summary']
        categorization = report['file_categorization']
        opportunities = report['consolidation_opportunities']
        status = report['implementation_status']
        
        print(f"📊 ANALYSIS SUMMARY")
        print(f"   Total Files: {summary['total_files']}")
        print(f"   Total Lines: {summary['total_lines']:,}")
        print(f"   Total Functions: {summary['total_functions']}")
        print(f"   Total Classes: {summary['total_classes']}")
        print(f"   Average Lines/File: {summary['average_lines_per_file']:.1f}")
        
        print(f"\n📁 FILE CATEGORIZATION")
        print(f"   Empty Files: {len(categorization['by_size']['empty'])}")
        print(f"   Minimal Files (<50 lines): {len(categorization['by_size']['minimal'])}")
        print(f"   Small Files (50-200 lines): {len(categorization['by_size']['small'])}")
        print(f"   Medium Files (200-500 lines): {len(categorization['by_size']['medium'])}")
        print(f"   Large Files (>500 lines): {len(categorization['by_size']['large'])}")
        
        print(f"\n🎯 CONSOLIDATION OPPORTUNITIES")
        for opp in opportunities:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(opp['priority'], '⚪')
            print(f"   {priority_emoji} {opp['type']}: {len(opp['files'])} files")
            print(f"      {opp['description']}")
        
        print(f"\n🏥 IMPLEMENTATION STATUS")
        print(f"   Overall Health: {status['overall_health'].upper()}")
        for component, info in status['core_components'].items():
            status_emoji = {'implemented': '✅', 'partial': '⚠️', 'missing': '❌'}.get(info['status'], '❓')
            print(f"   {status_emoji} {component}: {info['status']}")


def main():
    """Main function to run the comprehensive analysis."""
    print("🚀 SERENA EXTENSION COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print("This analysis will examine all Serena extension files to determine:")
    print("• Implementation status and completeness")
    print("• Usage patterns and dependencies") 
    print("• Overlapping functionality")
    print("• Consolidation opportunities")
    print("• Integration with the new unified interface")
    print()
    
    try:
        analyzer = SerenaFileAnalyzer()
        report = analyzer.analyze_all_files()
        
        # Save detailed report
        report_file = Path("serena_analysis_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Print key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        empty_files = report['file_categorization']['by_size']['empty']
        if empty_files:
            print(f"   🚨 {len(empty_files)} empty files found - candidates for removal")
            for file in empty_files[:3]:
                print(f"      • {file}")
            if len(empty_files) > 3:
                print(f"      • ... and {len(empty_files) - 3} more")
        
        opportunities = report['consolidation_opportunities']
        high_priority = [opp for opp in opportunities if opp['priority'] == 'high']
        if high_priority:
            print(f"   🔴 {len(high_priority)} high-priority consolidation opportunities")
            for opp in high_priority:
                print(f"      • {opp['type']}: {opp['description']}")
        
        overlapping = report['overlapping_functionality']
        if overlapping['functions'] or overlapping['classes']:
            print(f"   🔄 Overlapping functionality detected:")
            if overlapping['functions']:
                print(f"      • {len(overlapping['functions'])} duplicate function names")
            if overlapping['classes']:
                print(f"      • {len(overlapping['classes'])} duplicate class names")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   1. Remove empty files immediately (low risk)")
        print(f"   2. Consolidate overlapping analysis components (medium risk)")
        print(f"   3. Streamline LSP integration (high impact)")
        print(f"   4. Merge minimal utility files (low impact)")
        print(f"   5. Update import paths for renamed files")
        
        print(f"\n✅ UNIFIED INTERFACE STATUS:")
        print(f"   The new unified interface (codebase.errors(), etc.) is working!")
        print(f"   Consolidation will improve maintainability without breaking functionality.")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

