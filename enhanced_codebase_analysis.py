"""
Enhanced Codebase Analysis System
Based on graph-sitter documentation analysis and comprehensive issue detection
"""

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from collections import Counter
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass
from enum import Enum

class IssueType(Enum):
    DEAD_CODE = "dead_code"
    UNUSED_IMPORT = "unused_import"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    COMPLEX_INHERITANCE = "complex_inheritance"
    LARGE_FUNCTION = "large_function"
    MISSING_TESTS = "missing_tests"
    DUPLICATE_CODE = "duplicate_code"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    CODE_SMELL = "code_smell"

@dataclass
class CodeIssue:
    type: IssueType
    severity: str  # "low", "medium", "high", "critical"
    location: str
    range: str
    description: str
    suggestion: str
    affected_symbols: List[str]

@dataclass
class AnalysisResult:
    total_files: int
    total_functions: int
    total_classes: int
    total_imports: int
    dead_code_items: List[Dict[str, Any]]
    issues: List[CodeIssue]
    test_coverage: Dict[str, Any]
    complexity_metrics: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    inheritance_analysis: Dict[str, Any]

class EnhancedCodebaseAnalyzer:
    """
    Comprehensive codebase analyzer based on graph-sitter capabilities
    """
    
    def __init__(self, codebase_path: str, config: Optional[CodebaseConfig] = None):
        """Initialize the analyzer with a codebase"""
        self.config = config or CodebaseConfig(
            verify_graph=True,
            method_usages=True,
            sync_enabled=True,
            generics=True
        )
        
        if codebase_path.startswith(('http', 'git')):
            self.codebase = Codebase.from_repo(codebase_path, config=self.config)
        else:
            self.codebase = Codebase(codebase_path, config=self.config)
    
    def analyze(self) -> AnalysisResult:
        """Perform comprehensive codebase analysis"""
        print("🔍 Starting Enhanced Codebase Analysis...")
        print("=" * 60)
        
        # Basic metrics
        basic_metrics = self._get_basic_metrics()
        
        # Dead code detection
        dead_code_items = self._detect_dead_code()
        
        # Issue detection
        issues = self._detect_all_issues()
        
        # Test analysis
        test_coverage = self._analyze_test_coverage()
        
        # Complexity metrics
        complexity_metrics = self._analyze_complexity()
        
        # Dependency analysis
        dependency_analysis = self._analyze_dependencies()
        
        # Inheritance analysis
        inheritance_analysis = self._analyze_inheritance()
        
        return AnalysisResult(
            total_files=basic_metrics['files'],
            total_functions=basic_metrics['functions'],
            total_classes=basic_metrics['classes'],
            total_imports=basic_metrics['imports'],
            dead_code_items=dead_code_items,
            issues=issues,
            test_coverage=test_coverage,
            complexity_metrics=complexity_metrics,
            dependency_analysis=dependency_analysis,
            inheritance_analysis=inheritance_analysis
        )
    
    def _get_basic_metrics(self) -> Dict[str, int]:
        """Get basic codebase metrics"""
        return {
            'files': len(list(self.codebase.files)),
            'functions': len(list(self.codebase.functions)),
            'classes': len(list(self.codebase.classes)),
            'imports': len(list(self.codebase.imports))
        }
    
    def _detect_dead_code(self) -> List[Dict[str, Any]]:
        """Detect dead code (unused functions, classes, imports)"""
        dead_code_items = []
        
        # Dead functions
        for func in self.codebase.functions:
            if len(func.usages) == 0 and not func.name.startswith('test_'):
                dead_code_items.append({
                    'type': 'function',
                    'name': func.name,
                    'location': func.file.filepath if hasattr(func, 'file') else 'unknown',
                    'range': f"line {func.start_line}-{func.end_line}" if hasattr(func, 'start_line') else 'unknown',
                    'description': f'Unused function: {func.name}'
                })
        
        # Dead classes
        for cls in self.codebase.classes:
            if len(cls.usages) == 0:
                dead_code_items.append({
                    'type': 'class',
                    'name': cls.name,
                    'location': cls.file.filepath if hasattr(cls, 'file') else 'unknown',
                    'range': f"line {cls.start_line}-{cls.end_line}" if hasattr(cls, 'start_line') else 'unknown',
                    'description': f'Unused class: {cls.name}'
                })
        
        return dead_code_items
    
    def _detect_all_issues(self) -> List[CodeIssue]:
        """Detect various code issues"""
        issues = []
        
        # Dead code issues
        issues.extend(self._detect_dead_code_issues())
        
        # Complex inheritance issues
        issues.extend(self._detect_inheritance_issues())
        
        # Large function issues
        issues.extend(self._detect_large_function_issues())
        
        # Circular dependency issues
        issues.extend(self._detect_circular_dependencies())
        
        # Missing test issues
        issues.extend(self._detect_missing_tests())
        
        # Code smell issues
        issues.extend(self._detect_code_smells())
        
        return issues
    
    def _detect_dead_code_issues(self) -> List[CodeIssue]:
        """Detect dead code as issues"""
        issues = []
        
        for func in self.codebase.functions:
            if len(func.usages) == 0 and not func.name.startswith('test_'):
                issues.append(CodeIssue(
                    type=IssueType.DEAD_CODE,
                    severity="medium",
                    location=func.file.filepath if hasattr(func, 'file') else 'unknown',
                    range=f"line {func.start_line}-{func.end_line}" if hasattr(func, 'start_line') else 'unknown',
                    description=f"Function '{func.name}' is never used",
                    suggestion="Consider removing this function or verify if it should be used",
                    affected_symbols=[func.name]
                ))
        
        return issues
    
    def _detect_inheritance_issues(self) -> List[CodeIssue]:
        """Detect complex inheritance issues"""
        issues = []
        
        for cls in self.codebase.classes:
            if hasattr(cls, 'superclasses') and len(cls.superclasses) > 3:
                issues.append(CodeIssue(
                    type=IssueType.COMPLEX_INHERITANCE,
                    severity="high",
                    location=cls.file.filepath if hasattr(cls, 'file') else 'unknown',
                    range=f"line {cls.start_line}-{cls.end_line}" if hasattr(cls, 'start_line') else 'unknown',
                    description=f"Class '{cls.name}' has deep inheritance chain ({len(cls.superclasses)} levels)",
                    suggestion="Consider composition over inheritance or refactor the hierarchy",
                    affected_symbols=[cls.name] + [s.name for s in cls.superclasses if hasattr(s, 'name')]
                ))
        
        return issues
    
    def _detect_large_function_issues(self) -> List[CodeIssue]:
        """Detect large function issues"""
        issues = []
        
        for func in self.codebase.functions:
            if hasattr(func, 'source') and len(func.source.split('\n')) > 50:
                issues.append(CodeIssue(
                    type=IssueType.LARGE_FUNCTION,
                    severity="medium",
                    location=func.file.filepath if hasattr(func, 'file') else 'unknown',
                    range=f"line {func.start_line}-{func.end_line}" if hasattr(func, 'start_line') else 'unknown',
                    description=f"Function '{func.name}' is too large ({len(func.source.split('\n'))} lines)",
                    suggestion="Consider breaking this function into smaller, more focused functions",
                    affected_symbols=[func.name]
                ))
        
        return issues
    
    def _detect_circular_dependencies(self) -> List[CodeIssue]:
        """Detect circular dependency issues"""
        issues = []
        # This would require more complex graph analysis
        # For now, return empty list as placeholder
        return issues
    
    def _detect_missing_tests(self) -> List[CodeIssue]:
        """Detect functions/classes without tests"""
        issues = []
        
        test_functions = {f.name for f in self.codebase.functions if f.name.startswith('test_')}
        
        for func in self.codebase.functions:
            if not func.name.startswith('test_') and not func.name.startswith('_'):
                # Simple heuristic: check if there's a test function with similar name
                potential_test_names = [f"test_{func.name}", f"test_{func.name.lower()}"]
                if not any(test_name in test_functions for test_name in potential_test_names):
                    issues.append(CodeIssue(
                        type=IssueType.MISSING_TESTS,
                        severity="low",
                        location=func.file.filepath if hasattr(func, 'file') else 'unknown',
                        range=f"line {func.start_line}-{func.end_line}" if hasattr(func, 'start_line') else 'unknown',
                        description=f"Function '{func.name}' appears to lack test coverage",
                        suggestion="Consider adding unit tests for this function",
                        affected_symbols=[func.name]
                    ))
        
        return issues
    
    def _detect_code_smells(self) -> List[CodeIssue]:
        """Detect various code smells"""
        issues = []
        
        # Detect functions with too many parameters
        for func in self.codebase.functions:
            if hasattr(func, 'parameters') and len(func.parameters) > 5:
                issues.append(CodeIssue(
                    type=IssueType.CODE_SMELL,
                    severity="medium",
                    location=func.file.filepath if hasattr(func, 'file') else 'unknown',
                    range=f"line {func.start_line}-{func.end_line}" if hasattr(func, 'start_line') else 'unknown',
                    description=f"Function '{func.name}' has too many parameters ({len(func.parameters)})",
                    suggestion="Consider using a configuration object or breaking the function down",
                    affected_symbols=[func.name]
                ))
        
        return issues
    
    def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        test_functions = [f for f in self.codebase.functions if f.name.startswith('test_')]
        test_classes = [c for c in self.codebase.classes if c.name.startswith('Test')]
        
        total_functions = len(list(self.codebase.functions))
        total_files = len(list(self.codebase.files))
        
        # Find files with most tests
        file_test_counts = Counter([f.file for f in test_classes if hasattr(f, 'file')])
        top_test_files = file_test_counts.most_common(5)
        
        return {
            'total_test_functions': len(test_functions),
            'total_test_classes': len(test_classes),
            'tests_per_file': len(test_functions) / total_files if total_files > 0 else 0,
            'test_coverage_ratio': len(test_functions) / total_functions if total_functions > 0 else 0,
            'top_test_files': [
                {
                    'file': file.filepath if hasattr(file, 'filepath') else str(file),
                    'test_count': count,
                    'file_length': len(file.source.split('\n')) if hasattr(file, 'source') else 0
                }
                for file, count in top_test_files
            ]
        }
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        # Find most complex functions (by line count as proxy)
        complex_functions = []
        for func in self.codebase.functions:
            if hasattr(func, 'source'):
                line_count = len(func.source.split('\n'))
                if line_count > 20:  # Threshold for complexity
                    complex_functions.append({
                        'name': func.name,
                        'line_count': line_count,
                        'location': func.file.filepath if hasattr(func, 'file') else 'unknown'
                    })
        
        # Sort by complexity (line count)
        complex_functions.sort(key=lambda x: x['line_count'], reverse=True)
        
        # Find recursive functions
        recursive_functions = []
        for func in self.codebase.functions:
            if hasattr(func, 'function_calls'):
                if any(call.name == func.name for call in func.function_calls if hasattr(call, 'name')):
                    recursive_functions.append({
                        'name': func.name,
                        'location': func.file.filepath if hasattr(func, 'file') else 'unknown'
                    })
        
        return {
            'complex_functions': complex_functions[:10],  # Top 10 most complex
            'recursive_functions': recursive_functions,
            'average_function_length': sum(
                len(f.source.split('\n')) for f in self.codebase.functions 
                if hasattr(f, 'source')
            ) / len(list(self.codebase.functions)) if len(list(self.codebase.functions)) > 0 else 0
        }
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency relationships"""
        # Analyze import patterns
        import_counts = Counter()
        for imp in self.codebase.imports:
            if hasattr(imp, 'module_name'):
                import_counts[imp.module_name] += 1
        
        # Find files with most imports
        file_import_counts = Counter()
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                file_import_counts[file.filepath if hasattr(file, 'filepath') else str(file)] = len(file.imports)
        
        return {
            'most_imported_modules': import_counts.most_common(10),
            'files_with_most_imports': file_import_counts.most_common(10),
            'total_unique_imports': len(import_counts)
        }
    
    def _analyze_inheritance(self) -> Dict[str, Any]:
        """Analyze inheritance patterns"""
        inheritance_data = []
        
        for cls in self.codebase.classes:
            if hasattr(cls, 'superclasses'):
                inheritance_depth = len(cls.superclasses)
                if inheritance_depth > 0:
                    inheritance_data.append({
                        'class_name': cls.name,
                        'inheritance_depth': inheritance_depth,
                        'superclasses': [s.name for s in cls.superclasses if hasattr(s, 'name')],
                        'location': cls.file.filepath if hasattr(cls, 'file') else 'unknown'
                    })
        
        # Find deepest inheritance
        deepest_inheritance = max(inheritance_data, key=lambda x: x['inheritance_depth']) if inheritance_data else None
        
        return {
            'classes_with_inheritance': len(inheritance_data),
            'deepest_inheritance': deepest_inheritance,
            'average_inheritance_depth': sum(x['inheritance_depth'] for x in inheritance_data) / len(inheritance_data) if inheritance_data else 0,
            'inheritance_chains': inheritance_data
        }
    
    def print_analysis_results(self, result: AnalysisResult):
        """Print comprehensive analysis results"""
        print("\n🔍 ENHANCED CODEBASE ANALYSIS RESULTS")
        print("=" * 60)
        
        # Basic metrics
        print(f"📚 Total Files: {result.total_files}")
        print(f"⚡ Total Functions: {result.total_functions}")
        print(f"🏗️  Total Classes: {result.total_classes}")
        print(f"🔄 Total Imports: {result.total_imports}")
        
        # Dead code analysis
        print(f"\n💀 DEAD CODE ANALYSIS")
        print("-" * 40)
        print(f"🗑️  Dead Code Items: {len(result.dead_code_items)}")
        for item in result.dead_code_items[:5]:  # Show first 5
            print(f"   📍 {item['type']}: {item['name']}")
            print(f"      📂 Location: {item['location']}")
            print(f"      📏 Range: {item['range']}")
        
        # Issues analysis
        print(f"\n⚠️  ISSUES DETECTED")
        print("-" * 40)
        print(f"🚨 Total Issues: {len(result.issues)}")
        
        # Group issues by severity
        severity_counts = Counter(issue.severity for issue in result.issues)
        for severity, count in severity_counts.items():
            print(f"   {severity.upper()}: {count}")
        
        # Show sample issues
        for issue in result.issues[:5]:  # Show first 5 issues
            print(f"\n   🔸 {issue.type.value.upper()}: {issue.description}")
            print(f"      📂 {issue.location} ({issue.range})")
            print(f"      💡 {issue.suggestion}")
        
        # Test coverage
        print(f"\n🧪 TEST COVERAGE ANALYSIS")
        print("-" * 40)
        print(f"📝 Test Functions: {result.test_coverage['total_test_functions']}")
        print(f"🔬 Test Classes: {result.test_coverage['total_test_classes']}")
        print(f"📊 Tests per File: {result.test_coverage['tests_per_file']:.2f}")
        print(f"📈 Coverage Ratio: {result.test_coverage['test_coverage_ratio']:.2%}")
        
        # Complexity metrics
        print(f"\n🧮 COMPLEXITY ANALYSIS")
        print("-" * 40)
        print(f"🔄 Recursive Functions: {len(result.complexity_metrics['recursive_functions'])}")
        print(f"📏 Avg Function Length: {result.complexity_metrics['average_function_length']:.1f} lines")
        
        if result.complexity_metrics['complex_functions']:
            print("🔥 Most Complex Functions:")
            for func in result.complexity_metrics['complex_functions'][:3]:
                print(f"   - {func['name']}: {func['line_count']} lines")
        
        # Inheritance analysis
        print(f"\n🌳 INHERITANCE ANALYSIS")
        print("-" * 40)
        print(f"🏗️  Classes with Inheritance: {result.inheritance_analysis['classes_with_inheritance']}")
        print(f"📊 Average Inheritance Depth: {result.inheritance_analysis['average_inheritance_depth']:.1f}")
        
        if result.inheritance_analysis['deepest_inheritance']:
            deepest = result.inheritance_analysis['deepest_inheritance']
            print(f"🌲 Deepest Inheritance: {deepest['class_name']} ({deepest['inheritance_depth']} levels)")
        
        print(f"\n✅ Analysis Complete!")

def main():
    """Main function to demonstrate the enhanced analyzer"""
    # Example usage
    analyzer = EnhancedCodebaseAnalyzer("./")  # Analyze current directory
    result = analyzer.analyze()
    analyzer.print_analysis_results(result)
    
    # Save results to JSON for further processing
    with open('analysis_results.json', 'w') as f:
        json.dump({
            'total_files': result.total_files,
            'total_functions': result.total_functions,
            'total_classes': result.total_classes,
            'dead_code_items': result.dead_code_items,
            'issues': [
                {
                    'type': issue.type.value,
                    'severity': issue.severity,
                    'location': issue.location,
                    'description': issue.description,
                    'suggestion': issue.suggestion
                }
                for issue in result.issues
            ],
            'test_coverage': result.test_coverage,
            'complexity_metrics': result.complexity_metrics,
            'dependency_analysis': result.dependency_analysis,
            'inheritance_analysis': result.inheritance_analysis
        }, indent=2)

if __name__ == "__main__":
    main()
