"""
Enhanced Codebase Analysis System
Based on comprehensive graph-sitter documentation analysis and advanced visualization features

Features implemented:
- Core Quality Metrics (Maintainability Index, Halstead Volume, Cyclomatic Complexity, DOI)
- Advanced Function Analysis with issue detection
- Call Trace Visualization
- Function Dependency Graph
- Blast Radius Visualization
- Import Cycle Detection
- Test Coverage Analysis
- Dead Code Detection
- Comprehensive Reporting
"""

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from collections import Counter
from typing import List, Dict, Any, Optional
import json
import math
import networkx as nx
import os
from dataclasses import dataclass, asdict
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
    maintainability_metrics: Dict[str, Any]
    visualization_data: Dict[str, Any]
    health_score: float

@dataclass
class VisualizationData:
    call_graph: Dict[str, Any]
    dependency_graph: Dict[str, Any]
    blast_radius_graph: Dict[str, Any]
    import_cycle_graph: Dict[str, Any]

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
        
        # Maintainability metrics
        maintainability_metrics = self._analyze_maintainability()
        
        # Visualization data
        visualization_data = self._generate_visualization_data()
        
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
            inheritance_analysis=inheritance_analysis,
            maintainability_metrics=maintainability_metrics,
            visualization_data=visualization_data,
            health_score=self._calculate_health_score()
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
            'test_coverage_percentage': len(test_functions) / total_functions if total_functions > 0 else 0,
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
    
    def _analyze_maintainability(self) -> Dict[str, Any]:
        """Analyze maintainability metrics based on graph-sitter documentation"""
        maintainability_data = {}
        
        total_maintainability = 0
        function_count = 0
        
        for function in self.codebase.functions:
            try:
                # Calculate Halstead Volume
                halstead_volume = self._calculate_halstead_volume(function)
                
                # Calculate Cyclomatic Complexity
                cyclomatic_complexity = self._calculate_cyclomatic_complexity(function)
                
                # Calculate Lines of Code
                loc = self._count_lines(function)
                
                # Calculate Maintainability Index
                maintainability_index = self._calculate_maintainability_index(
                    halstead_volume, cyclomatic_complexity, loc
                )
                
                total_maintainability += maintainability_index
                function_count += 1
                
            except Exception as e:
                continue
        
        avg_maintainability = total_maintainability / function_count if function_count > 0 else 0
        
        maintainability_data = {
            'average_maintainability_index': avg_maintainability,
            'total_functions_analyzed': function_count,
            'maintainability_distribution': self._get_maintainability_distribution()
        }
        
        return maintainability_data
    
    def _calculate_halstead_volume(self, function) -> float:
        """Calculate Halstead Volume: V = (N1 + N2) * log2(n1 + n2)"""
        try:
            operators = []
            operands = []
            
            # Extract operators and operands from function source
            source_lines = function.source.split('\n')
            for line in source_lines:
                # Simple operator extraction
                for op in ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not']:
                    if op in line:
                        operators.append(op)
                
                # Simple operand extraction (variables, numbers, strings)
                import re
                operands.extend(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', line))
                operands.extend(re.findall(r'\b\d+\b', line))
            
            n1 = len(set(operators))  # Unique operators
            n2 = len(set(operands))   # Unique operands
            N1 = len(operators)       # Total operators
            N2 = len(operands)        # Total operands
            
            N = N1 + N2
            n = n1 + n2
            
            if n > 0:
                volume = N * math.log2(n)
                return volume
            return 0
        except:
            return 0
    
    def _calculate_cyclomatic_complexity(self, function) -> int:
        """Calculate Cyclomatic Complexity based on control flow statements"""
        try:
            complexity = 1  # Base complexity
            source = function.source.lower()
            
            # Count decision points
            complexity += source.count('if ')
            complexity += source.count('elif ')
            complexity += source.count('for ')
            complexity += source.count('while ')
            complexity += source.count('except ')
            complexity += source.count(' and ')
            complexity += source.count(' or ')
            
            return complexity
        except:
            return 1
    
    def _count_lines(self, function) -> int:
        """Count lines of code excluding blank lines and comments"""
        try:
            lines = function.source.split('\n')
            loc = 0
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    loc += 1
            return loc
        except:
            return 0
    
    def _calculate_maintainability_index(self, halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
        """Calculate the normalized maintainability index: M = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(SLOC)"""
        if loc <= 0:
            return 100
        
        try:
            raw_mi = (
                171
                - 5.2 * math.log(max(1, halstead_volume))
                - 0.23 * cyclomatic_complexity
                - 16.2 * math.log(max(1, loc))
            )
            normalized_mi = max(0, min(100, raw_mi * 100 / 171))
            return int(normalized_mi)
        except (ValueError, TypeError):
            return 0
    
    def _calculate_doi(self, cls) -> int:
        """Calculate Depth of Inheritance (DOI)"""
        try:
            return len(cls.superclasses) if hasattr(cls, 'superclasses') else 0
        except:
            return 0
    
    def _get_maintainability_distribution(self) -> Dict[str, int]:
        """Get distribution of maintainability scores"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for function in self.codebase.functions:
            try:
                halstead_volume = self._calculate_halstead_volume(function)
                cyclomatic_complexity = self._calculate_cyclomatic_complexity(function)
                loc = self._count_lines(function)
                mi = self._calculate_maintainability_index(halstead_volume, cyclomatic_complexity, loc)
                
                if mi >= 70:
                    distribution['high'] += 1
                elif mi >= 40:
                    distribution['medium'] += 1
                else:
                    distribution['low'] += 1
            except:
                continue
        
        return distribution
    
    def _generate_visualization_data(self) -> Dict[str, Any]:
        """Generate visualization data"""
        visualization_data = VisualizationData(
            call_graph=self._generate_call_graph(),
            dependency_graph=self._generate_dependency_graph(),
            blast_radius_graph=self._generate_blast_radius_graph(),
            import_cycle_graph=self._generate_import_cycle_graph()
        )
        
        return asdict(visualization_data)
    
    def _generate_call_graph(self) -> Dict[str, Any]:
        """Generate call graph data based on graph-sitter documentation"""
        call_graph_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_functions': 0,
                'max_depth': 0,
                'circular_calls': 0
            }
        }
        
        try:
            G = nx.DiGraph()
            
            # Color palette from documentation
            COLOR_PALETTE = {
                "StartFunction": "#9cdcfe",
                "PyFunction": "#a277ff", 
                "PyClass": "#ffca85",
                "ExternalModule": "#f694ff"
            }
            
            for function in self.codebase.functions:
                try:
                    # Add function node
                    node_data = {
                        'id': function.name,
                        'name': function.name,
                        'type': 'PyFunction',
                        'color': COLOR_PALETTE.get('PyFunction'),
                        'file_path': getattr(function, 'file_path', ''),
                        'line_count': len(function.source.split('\n')) if hasattr(function, 'source') else 0
                    }
                    call_graph_data['nodes'].append(node_data)
                    G.add_node(function.name, **node_data)
                    
                    # Add function calls as edges
                    if hasattr(function, 'function_calls'):
                        for call in function.function_calls:
                            try:
                                edge_data = {
                                    'source': function.name,
                                    'target': call.name,
                                    'type': 'function_call'
                                }
                                call_graph_data['edges'].append(edge_data)
                                G.add_edge(function.name, call.name)
                            except:
                                continue
                except:
                    continue
            
            # Calculate metadata
            call_graph_data['metadata']['total_functions'] = len(call_graph_data['nodes'])
            call_graph_data['metadata']['total_edges'] = len(call_graph_data['edges'])
            
            # Detect circular calls
            try:
                cycles = list(nx.simple_cycles(G))
                call_graph_data['metadata']['circular_calls'] = len(cycles)
                call_graph_data['metadata']['cycles'] = cycles[:5]  # First 5 cycles
            except:
                call_graph_data['metadata']['circular_calls'] = 0
                
        except Exception as e:
            call_graph_data['error'] = str(e)
        
        return call_graph_data
    
    def _generate_dependency_graph(self) -> Dict[str, Any]:
        """Generate dependency graph data based on graph-sitter documentation"""
        dependency_graph_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_dependencies': 0,
                'external_dependencies': 0,
                'internal_dependencies': 0
            }
        }
        
        try:
            for function in self.codebase.functions:
                try:
                    # Add function node
                    node_data = {
                        'id': function.name,
                        'name': function.name,
                        'type': 'function'
                    }
                    dependency_graph_data['nodes'].append(node_data)
                    
                    # Add dependencies as edges
                    if hasattr(function, 'dependencies'):
                        for dep in function.dependencies:
                            try:
                                edge_data = {
                                    'source': function.name,
                                    'target': getattr(dep, 'name', str(dep)),
                                    'type': 'dependency'
                                }
                                dependency_graph_data['edges'].append(edge_data)
                            except:
                                continue
                except:
                    continue
            
            dependency_graph_data['metadata']['total_dependencies'] = len(dependency_graph_data['edges'])
            
        except Exception as e:
            dependency_graph_data['error'] = str(e)
        
        return dependency_graph_data
    
    def _generate_blast_radius_graph(self) -> Dict[str, Any]:
        """Generate blast radius graph data based on graph-sitter documentation"""
        blast_radius_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_usages': 0,
                'high_impact_functions': []
            }
        }
        
        try:
            for function in self.codebase.functions:
                try:
                    usage_count = 0
                    
                    # Add function node
                    node_data = {
                        'id': function.name,
                        'name': function.name,
                        'type': 'function'
                    }
                    
                    # Add usages as edges (blast radius)
                    if hasattr(function, 'usages'):
                        for usage in function.usages:
                            try:
                                edge_data = {
                                    'source': function.name,
                                    'target': getattr(usage, 'name', str(usage)),
                                    'type': 'usage'
                                }
                                blast_radius_data['edges'].append(edge_data)
                                usage_count += 1
                            except:
                                continue
                    
                    node_data['usage_count'] = usage_count
                    blast_radius_data['nodes'].append(node_data)
                    
                    # Track high impact functions
                    if usage_count > 5:  # Functions used more than 5 times
                        blast_radius_data['metadata']['high_impact_functions'].append({
                            'name': function.name,
                            'usage_count': usage_count
                        })
                        
                except:
                    continue
            
            blast_radius_data['metadata']['total_usages'] = len(blast_radius_data['edges'])
            
        except Exception as e:
            blast_radius_data['error'] = str(e)
        
        return blast_radius_data
    
    def _generate_import_cycle_graph(self) -> Dict[str, Any]:
        """Generate import cycle graph data based on graph-sitter documentation"""
        import_cycle_data = {
            'nodes': [],
            'edges': [],
            'cycles': [],
            'metadata': {
                'total_imports': 0,
                'circular_imports': 0,
                'problematic_cycles': []
            }
        }
        
        try:
            G = nx.MultiDiGraph()
            
            # Add import relationships
            for imp in self.codebase.imports:
                try:
                    if hasattr(imp, 'from_file') and hasattr(imp, 'to_file'):
                        from_file = getattr(imp.from_file, 'filepath', str(imp.from_file))
                        to_file = getattr(imp.to_file, 'filepath', str(imp.to_file))
                        
                        # Add nodes
                        if from_file not in [n['id'] for n in import_cycle_data['nodes']]:
                            import_cycle_data['nodes'].append({
                                'id': from_file,
                                'name': from_file,
                                'type': 'file'
                            })
                        
                        if to_file not in [n['id'] for n in import_cycle_data['nodes']]:
                            import_cycle_data['nodes'].append({
                                'id': to_file,
                                'name': to_file,
                                'type': 'file'
                            })
                        
                        # Add edge
                        edge_data = {
                            'source': from_file,
                            'target': to_file,
                            'type': 'import',
                            'is_dynamic': getattr(imp, 'is_dynamic', False)
                        }
                        import_cycle_data['edges'].append(edge_data)
                        G.add_edge(from_file, to_file)
                        
                except:
                    continue
            
            # Find strongly connected components (import cycles)
            try:
                cycles = list(nx.strongly_connected_components(G))
                import_cycle_data['cycles'] = [list(cycle) for cycle in cycles if len(cycle) > 1]
                import_cycle_data['metadata']['circular_imports'] = len(import_cycle_data['cycles'])
            except:
                import_cycle_data['metadata']['circular_imports'] = 0
            
            import_cycle_data['metadata']['total_imports'] = len(import_cycle_data['edges'])
            
        except Exception as e:
            import_cycle_data['error'] = str(e)
        
        return import_cycle_data
    
    def _calculate_health_score(self) -> float:
        """Calculate comprehensive health score based on all metrics"""
        try:
            # Get maintainability metrics
            maintainability_data = self._analyze_maintainability()
            avg_maintainability = maintainability_data.get('average_maintainability_index', 0)
            
            # Get issue severity weights
            issue_weights = {'critical': 0.4, 'high': 0.3, 'medium': 0.2, 'low': 0.1}
            total_issues = len(self._detect_all_issues())
            issue_penalty = min(total_issues * 0.05, 0.5)  # Max 50% penalty
            
            # Get test coverage
            test_coverage = self._analyze_test_coverage()
            coverage_score = test_coverage.get('test_coverage_percentage', 0) / 100
            
            # Get dead code penalty
            dead_code_count = len(self._detect_dead_code())
            dead_code_penalty = min(dead_code_count * 0.02, 0.3)  # Max 30% penalty
            
            # Calculate composite health score
            health_score = (
                (avg_maintainability / 100) * 0.4 +  # 40% weight on maintainability
                coverage_score * 0.3 +                # 30% weight on test coverage
                (1 - issue_penalty) * 0.2 +          # 20% weight on issues
                (1 - dead_code_penalty) * 0.1        # 10% weight on dead code
            )
            
            return min(max(health_score, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            return 0.5  # Default middle score if calculation fails
    
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
        print(f"📈 Coverage Ratio: {result.test_coverage['test_coverage_percentage']:.2%}")
        
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
        
        # Maintainability metrics
        print(f"\n🔧 MAINTAINABILITY METRICS")
        print("-" * 40)
        print(f"🔧 Maintainability Index: {result.maintainability_metrics['average_maintainability_index']:.2f}")
        print(f"🔧 Total Functions Analyzed: {result.maintainability_metrics['total_functions_analyzed']}")
        print(f"🔧 Maintainability Distribution: {result.maintainability_metrics['maintainability_distribution']}")
        
        # Visualization data
        print(f"\n📈 VISUALIZATION DATA")
        print("-" * 40)
        print(f"📈 Call Graph: {result.visualization_data['call_graph']}")
        print(f"📈 Dependency Graph: {result.visualization_data['dependency_graph']}")
        print(f"📈 Blast Radius Graph: {result.visualization_data['blast_radius_graph']}")
        print(f"📈 Import Cycle Graph: {result.visualization_data['import_cycle_graph']}")
        
        # Health score
        print(f"\n📊 HEALTH SCORE")
        print("-" * 40)
        print(f"📊 Health Score: {result.health_score:.2f}")
        
        print(f"\n✅ Analysis Complete!")

    def export_to_json(self, result: AnalysisResult) -> str:
        """Export analysis results to JSON format"""
        return json.dumps({
            'total_files': result.total_files,
            'total_functions': result.total_functions,
            'total_classes': result.total_classes,
            'total_imports': result.total_imports,
            'dead_code_items': result.dead_code_items,
            'issues': [
                {
                    'type': issue.type.value,
                    'severity': issue.severity,
                    'location': issue.location,
                    'range': issue.range,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'affected_symbols': issue.affected_symbols
                }
                for issue in result.issues
            ],
            'test_coverage': result.test_coverage,
            'complexity_metrics': result.complexity_metrics,
            'dependency_analysis': result.dependency_analysis,
            'inheritance_analysis': result.inheritance_analysis,
            'maintainability_metrics': result.maintainability_metrics,
            'visualization_data': result.visualization_data,
            'health_score': result.health_score
        }, indent=2)

def main():
    """Main CLI interface for enhanced codebase analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Codebase Analysis with Visualization')
    parser.add_argument('--path', type=str, help='Path to local codebase')
    parser.add_argument('--repo', type=str, help='GitHub repository (owner/repo)')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for reports')
    parser.add_argument('--format', choices=['json', 'console'], default='console', help='Output format')
    parser.add_argument('--save-visualizations', action='store_true', help='Save visualization data to files')
    
    args = parser.parse_args()
    
    if not args.path and not args.repo:
        print("❌ Error: Please provide either --path or --repo")
        return
    
    try:
        print("🚀 Starting Enhanced Codebase Analysis...")
        
        # Initialize codebase
        if args.repo:
            print(f"📥 Analyzing GitHub repository: {args.repo}")
            codebase = Codebase.from_repo(args.repo)
        else:
            print(f"📁 Analyzing local codebase: {args.path}")
            codebase = Codebase(args.path)
        
        # Run analysis
        analyzer = EnhancedCodebaseAnalyzer(args.path or args.repo)
        analyzer.codebase = codebase
        result = analyzer.analyze()
        
        # Output results
        if args.format == 'console':
            analyzer.print_analysis_results(result)
        
        # Save JSON report
        report_path = os.path.join(args.output_dir, 'enhanced_analysis_report.json')
        with open(report_path, 'w') as f:
            f.write(analyzer.export_to_json(result))
        print(f"📄 Analysis report saved to: {report_path}")
        
        # Save visualization data if requested
        if args.save_visualizations:
            viz_dir = os.path.join(args.output_dir, 'visualizations')
            os.makedirs(viz_dir, exist_ok=True)
            
            # Save individual visualization files
            for viz_type, viz_data in result.visualization_data.items():
                viz_path = os.path.join(viz_dir, f'{viz_type}.json')
                with open(viz_path, 'w') as f:
                    json.dump(viz_data, f, indent=2)
                print(f"📊 {viz_type} data saved to: {viz_path}")
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"📊 Overall Health Score: {result.health_score:.2%}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
