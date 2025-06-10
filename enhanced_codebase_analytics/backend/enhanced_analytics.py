"""
Enhanced Codebase Analytics with Comprehensive Error Context & Analysis
"""

import json
import math
import re
import ast
import inspect
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import networkx as nx
from collections import defaultdict, Counter

from graph_sitter import Codebase
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.core.expressions.binary_expression import BinaryExpression
from graph_sitter.core.expressions.unary_expression import UnaryExpression
from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.external_module import ExternalModule


@dataclass
class CodeContext:
    """Detailed code context for errors and analysis"""
    file_path: str
    line_number: int
    column_number: int
    source_code: str
    surrounding_lines: List[str]
    function_context: Optional[str] = None
    class_context: Optional[str] = None
    module_context: Optional[str] = None
    ast_node_type: Optional[str] = None
    scope_variables: List[str] = field(default_factory=list)
    imports_in_scope: List[str] = field(default_factory=list)


@dataclass
class ErrorSuggestion:
    """Detailed error fix suggestion"""
    suggestion_type: str  # 'auto_fix', 'manual_fix', 'refactor', 'documentation'
    description: str
    code_example: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0
    estimated_effort: str = "low"  # 'low', 'medium', 'high'
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)


@dataclass
class ErrorInfo:
    """Comprehensive error information with detailed context"""
    error_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    detailed_description: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    symbol_name: Optional[str] = None
    
    # Enhanced context
    code_context: Optional[CodeContext] = None
    root_cause: Optional[str] = None
    impact_analysis: Optional[str] = None
    
    # Fix suggestions
    suggestions: List[ErrorSuggestion] = field(default_factory=list)
    auto_fixable: bool = False
    
    # Relationships
    blast_radius: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    
    # Metrics
    frequency: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    external_references: List[str] = field(default_factory=list)


@dataclass
class FileTreeNode:
    """Enhanced file tree node with comprehensive metrics"""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    lines_of_code: Optional[int] = None
    complexity_score: Optional[float] = None
    error_count: int = 0
    warning_count: int = 0
    
    # Enhanced metrics
    maintainability_index: Optional[float] = None
    technical_debt_ratio: Optional[float] = None
    test_coverage: Optional[float] = None
    last_modified: Optional[str] = None
    author_count: int = 0
    
    # Relationships
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    children: List['FileTreeNode'] = field(default_factory=list)


@dataclass
class SymbolInfo:
    """Comprehensive symbol information"""
    name: str
    type: str  # 'function', 'class', 'variable', 'constant'
    file_path: str
    line_number: int
    definition: str
    docstring: Optional[str] = None
    
    # Usage information
    usage_count: int = 0
    usage_locations: List[Tuple[str, int]] = field(default_factory=list)
    
    # Complexity metrics
    complexity: Optional[int] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    
    # Relationships
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    inherited_by: List[str] = field(default_factory=list)


@dataclass
class VisualizationData:
    """Enhanced visualization data with comprehensive context"""
    dependency_graph: Dict[str, Any]
    call_graph: Dict[str, Any]
    complexity_heatmap: Dict[str, Any]
    error_blast_radius: Dict[str, Any]
    file_tree: FileTreeNode
    metrics_summary: Dict[str, Any]
    
    # Enhanced visualizations
    symbol_usage_graph: Dict[str, Any] = field(default_factory=dict)
    error_timeline: Dict[str, Any] = field(default_factory=dict)
    quality_trends: Dict[str, Any] = field(default_factory=dict)
    hotspot_analysis: Dict[str, Any] = field(default_factory=dict)


class EnhancedCodebaseAnalyzer:
    """Enhanced analyzer with comprehensive error context and resolution capabilities"""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.dependency_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.errors: List[ErrorInfo] = []
        self.symbols: Dict[str, SymbolInfo] = {}
        self.metrics = {}
        self.error_patterns = defaultdict(int)
        self.file_contents_cache = {}
        
    def analyze_complete(self) -> VisualizationData:
        """Perform complete analysis with comprehensive error context"""
        print("🔍 Starting enhanced codebase analysis with comprehensive error context...")
        
        # Core analysis
        self._cache_file_contents()
        self._analyze_symbols()
        self._analyze_dependencies()
        self._analyze_call_relationships()
        self._detect_comprehensive_errors()
        self._calculate_enhanced_metrics()
        
        # Generate enhanced visualizations
        file_tree = self._build_enhanced_file_tree()
        dependency_viz = self._generate_dependency_visualization()
        call_viz = self._generate_call_visualization()
        complexity_heatmap = self._generate_complexity_heatmap()
        error_blast_radius = self._generate_error_blast_radius()
        symbol_usage_graph = self._generate_symbol_usage_graph()
        error_timeline = self._generate_error_timeline()
        quality_trends = self._generate_quality_trends()
        hotspot_analysis = self._generate_hotspot_analysis()
        
        print(f"��� Enhanced analysis complete! Found {len(self.errors)} issues with comprehensive context")
        
        return VisualizationData(
            dependency_graph=dependency_viz,
            call_graph=call_viz,
            complexity_heatmap=complexity_heatmap,
            error_blast_radius=error_blast_radius,
            file_tree=file_tree,
            metrics_summary=self.metrics,
            symbol_usage_graph=symbol_usage_graph,
            error_timeline=error_timeline,
            quality_trends=quality_trends,
            hotspot_analysis=hotspot_analysis
        )
    
    def _cache_file_contents(self):
        """Cache file contents for detailed analysis"""
        print("📁 Caching file contents for detailed analysis...")
        for file in self.codebase.files:
            try:
                self.file_contents_cache[file.filepath] = {
                    'content': file.source,
                    'lines': file.source.split('\n'),
                    'ast': None
                }
                
                # Try to parse AST for Python files
                if file.filepath.endswith('.py'):
                    try:
                        self.file_contents_cache[file.filepath]['ast'] = ast.parse(file.source)
                    except SyntaxError as e:
                        # Record syntax error
                        self._add_syntax_error(file.filepath, e)
                    except Exception:
                        pass  # Skip AST parsing for problematic files
                        
            except Exception as e:
                print(f"⚠️ Warning: Could not cache content for {file.filepath}: {e}")
    
    def _analyze_symbols(self):
        """Comprehensive symbol analysis"""
        print("🔍 Analyzing symbols comprehensively...")
        
        for func in self.codebase.functions:
            symbol_info = SymbolInfo(
                name=func.name,
                type='function',
                file_path=func.filepath,
                line_number=getattr(func, 'line_number', 0),
                definition=getattr(func, 'source', ''),
                docstring=getattr(func, 'docstring', None),
                complexity=self._calculate_cyclomatic_complexity(func),
                parameters=self._extract_function_parameters(func),
                return_type=self._extract_return_type(func)
            )
            
            # Analyze function calls and usage
            if hasattr(func, 'function_calls'):
                symbol_info.calls = [call.name for call in func.function_calls if hasattr(call, 'name')]
            
            if hasattr(func, 'usages'):
                symbol_info.usage_count = len(func.usages)
                symbol_info.usage_locations = [
                    (usage.filepath, getattr(usage, 'line_number', 0)) 
                    for usage in func.usages 
                    if hasattr(usage, 'filepath')
                ]
            
            self.symbols[f"func:{func.name}@{func.filepath}"] = symbol_info
        
        # Analyze classes
        for cls in self.codebase.classes:
            symbol_info = SymbolInfo(
                name=cls.name,
                type='class',
                file_path=cls.filepath,
                line_number=getattr(cls, 'line_number', 0),
                definition=getattr(cls, 'source', ''),
                docstring=getattr(cls, 'docstring', None)
            )
            
            # Analyze inheritance
            if hasattr(cls, 'superclasses'):
                symbol_info.inherits_from = [sc.name for sc in cls.superclasses if hasattr(sc, 'name')]
            
            self.symbols[f"class:{cls.name}@{cls.filepath}"] = symbol_info

    def _analyze_dependencies(self):
        """Analyze module dependencies and build dependency graph"""
        print("📊 Analyzing dependencies...")
        
        for file in self.codebase.files:
            file_node = f"file:{file.filepath}"
            self.dependency_graph.add_node(file_node, 
                                         type="file", 
                                         name=Path(file.filepath).name,
                                         path=file.filepath)
            
            # Add import dependencies
            for imp in file.imports:
                if imp.resolved_symbol:
                    target_file = getattr(imp.resolved_symbol, 'filepath', None)
                    if target_file:
                        target_node = f"file:{target_file}"
                        self.dependency_graph.add_node(target_node,
                                                     type="file",
                                                     name=Path(target_file).name,
                                                     path=target_file)
                        self.dependency_graph.add_edge(file_node, target_node,
                                                     type="import",
                                                     symbol=imp.name)
    
    def _analyze_call_relationships(self):
        """Analyze function call relationships"""
        print("🔗 Analyzing call relationships...")
        
        for func in self.codebase.functions:
            func_node = f"func:{func.name}@{func.filepath}"
            self.call_graph.add_node(func_node,
                                   type="function",
                                   name=func.name,
                                   filepath=func.filepath,
                                   complexity=self._calculate_cyclomatic_complexity(func))
            
            # Add function calls
            if hasattr(func, 'function_calls'):
                for call in func.function_calls:
                    if call.function_definition:
                        target_func = call.function_definition
                        target_node = f"func:{target_func.name}@{target_func.filepath}"
                        self.call_graph.add_node(target_node,
                                               type="function",
                                               name=target_func.name,
                                               filepath=target_func.filepath)
                        self.call_graph.add_edge(func_node, target_node,
                                               type="calls")
    
    def _detect_comprehensive_errors(self):
        """Detect various types of errors with comprehensive context"""
        print("🚨 Detecting errors with comprehensive context...")
        
        self._detect_import_errors_with_context()
        self._detect_symbol_resolution_errors_with_context()
        self._detect_dead_code_with_context()
        self._detect_complexity_issues_with_context()
        self._detect_configuration_errors_with_context()
        self._detect_syntax_errors()
        self._detect_code_smells()
        self._detect_security_issues()
        self._analyze_error_patterns()
    
    def _detect_import_errors_with_context(self):
        """Detect import-related errors with comprehensive context"""
        print("🔍 Analyzing import errors with context...")
        
        for file in self.codebase.files:
            for imp in file.imports:
                if not imp.resolved_symbol and not isinstance(imp.imported_symbol, ExternalModule):
                    # Get detailed context
                    context = self._get_code_context(file.filepath, getattr(imp, 'line_number', 1))
                    
                    # Analyze root cause
                    root_cause = self._analyze_import_root_cause(imp, file)
                    
                    # Generate suggestions
                    suggestions = self._generate_import_fix_suggestions(imp, file)
                    
                    error = ErrorInfo(
                        error_type="ImportError",
                        severity="high",
                        message=f"Unresolved import: {imp.name}",
                        detailed_description=f"The import '{imp.name}' could not be resolved. This may indicate a missing dependency, incorrect module path, or circular import.",
                        file_path=file.filepath,
                        line_number=getattr(imp, 'line_number', None),
                        symbol_name=imp.name,
                        code_context=context,
                        root_cause=root_cause,
                        impact_analysis=f"This import error affects {len(self._find_dependent_files(file.filepath))} dependent files",
                        suggestions=suggestions,
                        auto_fixable=any(s.suggestion_type == 'auto_fix' for s in suggestions),
                        blast_radius=self._calculate_import_blast_radius(imp),
                        tags=['import', 'dependency', 'resolution'],
                        external_references=self._find_external_references(imp.name)
                    )
                    self.errors.append(error)
    
    def _detect_symbol_resolution_errors_with_context(self):
        """Detect symbol resolution issues with comprehensive context"""
        print("🔍 Analyzing symbol resolution errors with context...")
        
        for symbol in self.codebase.symbols:
            if hasattr(symbol, 'usages'):
                for usage in symbol.usages:
                    if not usage.usage_symbol:
                        context = self._get_code_context(symbol.filepath, getattr(usage, 'line_number', 1))
                        
                        suggestions = [
                            ErrorSuggestion(
                                suggestion_type='manual_fix',
                                description=f"Define the symbol '{symbol.name}' or add proper import",
                                confidence_score=0.8,
                                estimated_effort='medium'
                            )
                        ]
                        
                        error = ErrorInfo(
                            error_type="SymbolError",
                            severity="medium",
                            message=f"Undefined symbol reference: {symbol.name}",
                            detailed_description=f"The symbol '{symbol.name}' is referenced but not defined in the current scope.",
                            file_path=symbol.filepath,
                            symbol_name=symbol.name,
                            code_context=context,
                            root_cause="Symbol not defined in current scope or missing import",
                            suggestions=suggestions,
                            auto_fixable=False,
                            blast_radius=[symbol.filepath],
                            tags=['symbol', 'undefined', 'scope']
                        )
                        self.errors.append(error)
    
    def _detect_dead_code_with_context(self):
        """Detect unused functions and variables with comprehensive context"""
        print("🔍 Analyzing dead code with context...")
        
        for func in self.codebase.functions:
            if hasattr(func, 'usages') and len(func.usages) == 0:
                # Check if it's not a main function or special method
                if not (func.name in ['main', '__init__', '__main__'] or 
                       func.name.startswith('test_') or
                       func.name.startswith('_')):  # Private methods might be intentionally unused
                    
                    context = self._get_code_context(func.filepath, getattr(func, 'line_number', 1))
                    
                    suggestions = [
                        ErrorSuggestion(
                            suggestion_type='auto_fix',
                            description=f"Remove unused function '{func.name}'",
                            confidence_score=0.9,
                            estimated_effort='low',
                            side_effects=['Function will be permanently deleted']
                        ),
                        ErrorSuggestion(
                            suggestion_type='manual_fix',
                            description=f"Add usage of function '{func.name}' if it's needed",
                            confidence_score=0.7,
                            estimated_effort='medium'
                        )
                    ]
                    
                    error = ErrorInfo(
                        error_type="DeadCode",
                        severity="low",
                        message=f"Unused function: {func.name}",
                        detailed_description=f"The function '{func.name}' is defined but never called. This may indicate dead code that can be removed.",
                        file_path=func.filepath,
                        symbol_name=func.name,
                        code_context=context,
                        root_cause="Function is defined but never called",
                        impact_analysis="Removing this function will reduce code complexity and maintenance burden",
                        suggestions=suggestions,
                        auto_fixable=True,
                        blast_radius=[func.filepath],
                        tags=['dead_code', 'unused', 'function']
                    )
                    self.errors.append(error)
    
    def _detect_complexity_issues_with_context(self):
        """Detect high complexity functions with comprehensive context"""
        print("🔍 Analyzing complexity issues with context...")
        
        for func in self.codebase.functions:
            complexity = self._calculate_cyclomatic_complexity(func)
            if complexity > 20:  # High complexity threshold
                context = self._get_code_context(func.filepath, getattr(func, 'line_number', 1))
                
                suggestions = [
                    ErrorSuggestion(
                        suggestion_type='refactor',
                        description=f"Break down '{func.name}' into smaller functions",
                        code_example=self._generate_refactor_example(func),
                        confidence_score=0.8,
                        estimated_effort='high',
                        prerequisites=['Understanding of function logic', 'Test coverage']
                    ),
                    ErrorSuggestion(
                        suggestion_type='documentation',
                        description=f"Add comprehensive documentation to '{func.name}'",
                        confidence_score=0.9,
                        estimated_effort='medium'
                    )
                ]
                
                error = ErrorInfo(
                    error_type="ComplexityError",
                    severity="medium" if complexity <= 30 else "high",
                    message=f"High cyclomatic complexity: {complexity}",
                    detailed_description=f"The function '{func.name}' has a cyclomatic complexity of {complexity}, which exceeds the recommended threshold of 20. High complexity makes code harder to understand, test, and maintain.",
                    file_path=func.filepath,
                    symbol_name=func.name,
                    code_context=context,
                    root_cause="Function contains too many decision points (if/else, loops, etc.)",
                    impact_analysis=f"High complexity increases maintenance cost and bug probability",
                    suggestions=suggestions,
                    auto_fixable=False,
                    blast_radius=self._calculate_function_blast_radius(func),
                    tags=['complexity', 'maintainability', 'refactor']
                )
                self.errors.append(error)
    
    def _detect_syntax_errors(self):
        """Detect syntax errors from AST parsing"""
        print("🔍 Analyzing syntax errors...")
        # Syntax errors are already detected in _cache_file_contents
        pass
    
    def _detect_code_smells(self):
        """Detect code smells and anti-patterns"""
        print("🔍 Analyzing code smells...")
        
        for file_path, file_data in self.file_contents_cache.items():
            if file_path.endswith('.py') and file_data['ast']:
                self._detect_long_functions(file_path, file_data['ast'])
                self._detect_long_parameter_lists(file_path, file_data['ast'])
                self._detect_duplicate_code(file_path, file_data['content'])
    
    def _detect_security_issues(self):
        """Detect potential security issues"""
        print("🔍 Analyzing security issues...")
        
        security_patterns = [
            (r'eval\s*\(', 'Use of eval() can be dangerous'),
            (r'exec\s*\(', 'Use of exec() can be dangerous'),
            (r'input\s*\(', 'Use of input() without validation'),
            (r'os\.system\s*\(', 'Use of os.system() can be dangerous'),
            (r'subprocess\.call\s*\(.*shell=True', 'Shell injection vulnerability'),
        ]
        
        for file_path, file_data in self.file_contents_cache.items():
            content = file_data['content']
            lines = file_data['lines']
            
            for pattern, description in security_patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        context = self._get_code_context(file_path, line_num)
                        
                        error = ErrorInfo(
                            error_type="SecurityIssue",
                            severity="high",
                            message=description,
                            detailed_description=f"Potential security vulnerability detected: {description}",
                            file_path=file_path,
                            line_number=line_num,
                            code_context=context,
                            root_cause="Use of potentially dangerous function",
                            suggestions=[
                                ErrorSuggestion(
                                    suggestion_type='manual_fix',
                                    description="Review and replace with safer alternative",
                                    confidence_score=0.9,
                                    estimated_effort='medium'
                                )
                            ],
                            auto_fixable=False,
                            tags=['security', 'vulnerability', 'dangerous_function']
                        )
                        self.errors.append(error)
    
    def _detect_configuration_errors_with_context(self):
        """Detect configuration and parameter errors with comprehensive context"""
        # This is a placeholder for configuration error detection
        # In a real implementation, this would check for:
        # - Invalid file paths in config files
        # - Wrong parameter types
        # - Missing environment variables
        # - Deprecated settings
        pass
    
    def _calculate_import_blast_radius(self, imp: Import) -> List[str]:
        """Calculate the blast radius of an import error"""
        affected_files = [imp.filepath] if hasattr(imp, 'filepath') else []
        
        # Find files that might be affected by this import
        for file in self.codebase.files:
            for file_imp in file.imports:
                if file_imp.name == imp.name:
                    affected_files.append(file.filepath)
        
        return list(set(affected_files))
    
    def _calculate_function_blast_radius(self, func: Function) -> List[str]:
        """Calculate the blast radius of a function"""
        affected_files = [func.filepath]
        
        # Find files that use this function
        if hasattr(func, 'usages'):
            for usage in func.usages:
                if hasattr(usage, 'usage_symbol') and hasattr(usage.usage_symbol, 'filepath'):
                    affected_files.append(usage.usage_symbol.filepath)
        
        return list(set(affected_files))
    
    def _calculate_cyclomatic_complexity(self, function: Function) -> int:
        """Calculate cyclomatic complexity for a function"""
        def analyze_statement(statement):
            complexity = 0
            
            if isinstance(statement, IfBlockStatement):
                complexity += 1
                if hasattr(statement, "elif_statements"):
                    complexity += len(statement.elif_statements)
            
            elif isinstance(statement, (ForLoopStatement, WhileStatement)):
                complexity += 1
            
            elif isinstance(statement, TryCatchStatement):
                complexity += len(getattr(statement, "except_blocks", []))
            
            if hasattr(statement, "condition") and isinstance(statement.condition, str):
                complexity += statement.condition.count(" and ") + statement.condition.count(" or ")
            
            if hasattr(statement, "nested_code_blocks"):
                for block in statement.nested_code_blocks:
                    complexity += analyze_block(block)
            
            return complexity
        
        def analyze_block(block):
            if not block or not hasattr(block, "statements"):
                return 0
            return sum(analyze_statement(stmt) for stmt in block.statements)
        
        return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1
    
    def _calculate_enhanced_metrics(self):
        """Calculate comprehensive metrics"""
        print("📈 Calculating metrics...")
        
        total_files = len(self.codebase.files)
        total_functions = len(self.codebase.functions)
        total_classes = len(self.codebase.classes)
        total_lines = sum(len(file.source.split('\n')) for file in self.codebase.files)
        
        # Complexity metrics
        complexities = [self._calculate_cyclomatic_complexity(func) for func in self.codebase.functions]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        
        # Error metrics
        error_counts = {}
        for error in self.errors:
            error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
        
        self.metrics = {
            "total_files": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_lines": total_lines,
            "average_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "total_errors": len(self.errors),
            "error_breakdown": error_counts,
            "dependency_count": self.dependency_graph.number_of_edges(),
            "call_relationship_count": self.call_graph.number_of_edges()
        }
    
    def _build_enhanced_file_tree(self) -> FileTreeNode:
        """Build hierarchical file tree structure"""
        print("🌳 Building file tree...")
        
        root = FileTreeNode(name="root", path="", type="directory")
        path_to_node = {"": root}
        
        for file in self.codebase.files:
            path_parts = Path(file.filepath).parts
            current_path = ""
            
            for i, part in enumerate(path_parts):
                parent_path = current_path
                current_path = str(Path(current_path) / part) if current_path else part
                
                if current_path not in path_to_node:
                    is_file = i == len(path_parts) - 1
                    node_type = "file" if is_file else "directory"
                    
                    node = FileTreeNode(
                        name=part,
                        path=current_path,
                        type=node_type,
                        size=len(file.source) if is_file else None,
                        lines_of_code=len(file.source.split('\n')) if is_file else None,
                        error_count=len([e for e in self.errors if e.file_path == file.filepath]) if is_file else 0
                    )
                    
                    if is_file:
                        # Calculate complexity score for file
                        file_functions = [f for f in self.codebase.functions if f.filepath == file.filepath]
                        if file_functions:
                            complexities = [self._calculate_cyclomatic_complexity(f) for f in file_functions]
                            node.complexity_score = sum(complexities) / len(complexities)
                    
                    path_to_node[current_path] = node
                    path_to_node[parent_path].children.append(node)
        
        return root
    
    def _generate_dependency_visualization(self) -> Dict[str, Any]:
        """Generate dependency graph visualization data"""
        nodes = []
        edges = []
        
        for node_id, data in self.dependency_graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data.get("name", node_id),
                "type": data.get("type", "unknown"),
                "path": data.get("path", ""),
                "group": data.get("type", "unknown")
            })
        
        for source, target, data in self.dependency_graph.edges(data=True):
            edges.append({
                "from": source,
                "to": target,
                "label": data.get("symbol", ""),
                "type": data.get("type", "dependency")
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical"
        }
    
    def _generate_call_visualization(self) -> Dict[str, Any]:
        """Generate call graph visualization data"""
        nodes = []
        edges = []
        
        for node_id, data in self.call_graph.nodes(data=True):
            complexity = data.get("complexity", 1)
            color = self._get_complexity_color(complexity)
            
            nodes.append({
                "id": node_id,
                "label": data.get("name", node_id),
                "type": data.get("type", "function"),
                "filepath": data.get("filepath", ""),
                "complexity": complexity,
                "color": color,
                "size": min(complexity * 2, 50)  # Size based on complexity
            })
        
        for source, target, data in self.call_graph.edges(data=True):
            edges.append({
                "from": source,
                "to": target,
                "type": data.get("type", "calls")
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force"
        }
    
    def _generate_complexity_heatmap(self) -> Dict[str, Any]:
        """Generate complexity heatmap data"""
        heatmap_data = []
        
        for file in self.codebase.files:
            file_functions = [f for f in self.codebase.functions if f.filepath == file.filepath]
            
            if file_functions:
                complexities = [self._calculate_cyclomatic_complexity(f) for f in file_functions]
                avg_complexity = sum(complexities) / len(complexities)
                max_complexity = max(complexities)
                
                heatmap_data.append({
                    "file": file.filepath,
                    "name": Path(file.filepath).name,
                    "avg_complexity": round(avg_complexity, 2),
                    "max_complexity": max_complexity,
                    "function_count": len(file_functions),
                    "color": self._get_complexity_color(avg_complexity)
                })
        
        return {
            "data": heatmap_data,
            "color_scale": {
                "low": "#00ff00",
                "medium": "#ffff00", 
                "high": "#ff8800",
                "critical": "#ff0000"
            }
        }
    
    def _generate_error_blast_radius(self) -> Dict[str, Any]:
        """Generate error blast radius visualization"""
        nodes = []
        edges = []
        
        # Group errors by type
        error_groups = {}
        for error in self.errors:
            if error.error_type not in error_groups:
                error_groups[error.error_type] = []
            error_groups[error.error_type].append(error)
        
        # Create nodes for each error
        for error_type, errors in error_groups.items():
            for i, error in enumerate(errors):
                error_id = f"error:{error_type}:{i}"
                nodes.append({
                    "id": error_id,
                    "label": f"{error.error_type}: {error.symbol_name or 'Unknown'}",
                    "type": "error",
                    "severity": error.severity,
                    "message": error.message,
                    "file_path": error.file_path,
                    "auto_fixable": error.auto_fixable,
                    "color": self._get_severity_color(error.severity),
                    "size": self._get_severity_size(error.severity)
                })
                
                # Add affected files as nodes
                if error.blast_radius:
                    for affected_file in error.blast_radius:
                        file_id = f"file:{affected_file}"
                        if not any(node["id"] == file_id for node in nodes):
                            nodes.append({
                                "id": file_id,
                                "label": Path(affected_file).name,
                                "type": "affected_file",
                                "path": affected_file,
                                "color": "#ffcccc"
                            })
                        
                        edges.append({
                            "from": error_id,
                            "to": file_id,
                            "type": "affects"
                        })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force"
        }
    
    def _generate_symbol_usage_graph(self) -> Dict[str, Any]:
        """Generate symbol usage graph visualization data"""
        nodes = []
        edges = []
        
        for symbol_id, symbol_info in self.symbols.items():
            nodes.append({
                "id": symbol_id,
                "label": symbol_info.name,
                "type": symbol_info.type,
                "file_path": symbol_info.file_path,
                "line_number": symbol_info.line_number,
                "definition": symbol_info.definition,
                "docstring": symbol_info.docstring,
                "complexity": symbol_info.complexity,
                "parameters": symbol_info.parameters,
                "return_type": symbol_info.return_type,
                "usage_count": symbol_info.usage_count,
                "usage_locations": symbol_info.usage_locations,
                "color": "#00ff00"  # Green - low
            })
        
        for node_id, data in self.symbols.items():
            if data.calls:
                for call in data.calls:
                    edge = {
                        "from": node_id,
                        "to": f"func:{call}@{data.file_path}",
                        "type": "calls"
                    }
                    edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "force"
        }
    
    def _generate_error_timeline(self) -> Dict[str, Any]:
        """Generate error timeline visualization data"""
        error_timeline = []
        
        for error in self.errors:
            error_timeline.append({
                "error_type": error.error_type,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "message": error.message,
                "severity": error.severity,
                "auto_fixable": error.auto_fixable
            })
        
        return {
            "data": error_timeline
        }
    
    def _generate_quality_trends(self) -> Dict[str, Any]:
        """Generate quality trends visualization data"""
        quality_trends = []
        
        for file in self.codebase.files:
            file_functions = [f for f in self.codebase.functions if f.filepath == file.filepath]
            if file_functions:
                complexities = [self._calculate_cyclomatic_complexity(f) for f in file_functions]
                avg_complexity = sum(complexities) / len(complexities)
                max_complexity = max(complexities)
                
                quality_trends.append({
                    "file": file.filepath,
                    "name": Path(file.filepath).name,
                    "avg_complexity": round(avg_complexity, 2),
                    "max_complexity": max_complexity,
                    "function_count": len(file_functions),
                    "color": self._get_complexity_color(avg_complexity)
                })
        
        return {
            "data": quality_trends,
            "color_scale": {
                "low": "#00ff00",
                "medium": "#ffff00", 
                "high": "#ff8800",
                "critical": "#ff0000"
            }
        }
    
    def _generate_hotspot_analysis(self) -> Dict[str, Any]:
        """Generate hotspot analysis visualization data"""
        hotspot_analysis = []
        
        for error in self.errors:
            hotspot_analysis.append({
                "error_type": error.error_type,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "message": error.message,
                "severity": error.severity,
                "auto_fixable": error.auto_fixable
            })
        
        return {
            "data": hotspot_analysis
        }
    
    def _get_complexity_color(self, complexity: float) -> str:
        """Get color based on complexity level"""
        if complexity <= 5:
            return "#00ff00"  # Green - low
        elif complexity <= 10:
            return "#ffff00"  # Yellow - medium
        elif complexity <= 20:
            return "#ff8800"  # Orange - high
        else:
            return "#ff0000"  # Red - critical
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color based on error severity"""
        colors = {
            "low": "#ffff00",
            "medium": "#ff8800", 
            "high": "#ff4444",
            "critical": "#ff0000"
        }
        return colors.get(severity, "#888888")
    
    def _get_severity_size(self, severity: str) -> int:
        """Get node size based on error severity"""
        sizes = {
            "low": 10,
            "medium": 15,
            "high": 20,
            "critical": 25
        }
        return sizes.get(severity, 10)
    
    def get_fixable_errors(self) -> List[ErrorInfo]:
        """Get list of auto-fixable errors"""
        return [error for error in self.errors if error.auto_fixable]
    
    def apply_auto_fixes(self) -> Dict[str, Any]:
        """Apply automatic fixes to detected errors"""
        print("🔧 Applying automatic fixes...")
        
        fixed_errors = []
        failed_fixes = []
        
        for error in self.get_fixable_errors():
            try:
                if error.error_type == "ImportError":
                    # Attempt to fix import errors
                    success = self._fix_import_error(error)
                elif error.error_type == "DeadCode":
                    # Attempt to remove dead code
                    success = self._fix_dead_code(error)
                else:
                    success = False
                
                if success:
                    fixed_errors.append(error)
                else:
                    failed_fixes.append(error)
                    
            except Exception as e:
                failed_fixes.append(error)
                print(f"❌ Failed to fix {error.error_type}: {str(e)}")
        
        return {
            "fixed_count": len(fixed_errors),
            "failed_count": len(failed_fixes),
            "fixed_errors": [asdict(error) for error in fixed_errors],
            "failed_errors": [asdict(error) for error in failed_fixes]
        }
    
    def _fix_import_error(self, error: ErrorInfo) -> bool:
        """Attempt to fix an import error"""
        # This is a placeholder for import error fixing
        # In a real implementation, this would:
        # 1. Analyze the import statement
        # 2. Search for the correct module path
        # 3. Update the import statement
        # 4. Validate the fix
        print(f"🔧 Attempting to fix import error: {error.symbol_name}")
        return False  # Placeholder
    
    def _fix_dead_code(self, error: ErrorInfo) -> bool:
        """Attempt to remove dead code"""
        # This is a placeholder for dead code removal
        # In a real implementation, this would:
        # 1. Verify the code is truly unused
        # 2. Remove the function/variable
        # 3. Update any related documentation
        print(f"🔧 Attempting to remove dead code: {error.symbol_name}")
        return False  # Placeholder
    
    def _extract_function_parameters(self, func: Function) -> List[str]:
        """Extract function parameters from AST"""
        if hasattr(func, 'function_calls'):
            for call in func.function_calls:
                if call.function_definition:
                    return [call.name for call in call.function_definition.function_calls]
        return []
    
    def _extract_return_type(self, func: Function) -> Optional[str]:
        """Extract return type from AST"""
        if hasattr(func, 'function_calls'):
            for call in func.function_calls:
                if call.function_definition:
                    return call.function_definition.return_type
        return None
    
    def _get_code_context(self, file_path: str, line_number: int) -> CodeContext:
        """Get comprehensive code context for a specific location"""
        if file_path not in self.file_contents_cache:
            return CodeContext(
                file_path=file_path,
                line_number=line_number,
                column_number=0,
                source_code="",
                surrounding_lines=[]
            )
        
        file_data = self.file_contents_cache[file_path]
        lines = file_data['lines']
        
        # Get surrounding lines (5 before and after)
        start_line = max(0, line_number - 6)
        end_line = min(len(lines), line_number + 5)
        surrounding_lines = lines[start_line:end_line]
        
        # Get the specific line
        source_code = lines[line_number - 1] if line_number <= len(lines) else ""
        
        # Analyze context
        function_context = self._find_function_context(file_path, line_number)
        class_context = self._find_class_context(file_path, line_number)
        module_context = Path(file_path).stem
        
        # Get scope variables and imports
        scope_variables = self._get_scope_variables(file_path, line_number)
        imports_in_scope = self._get_imports_in_scope(file_path)
        
        return CodeContext(
            file_path=file_path,
            line_number=line_number,
            column_number=0,
            source_code=source_code,
            surrounding_lines=surrounding_lines,
            function_context=function_context,
            class_context=class_context,
            module_context=module_context,
            scope_variables=scope_variables,
            imports_in_scope=imports_in_scope
        )
    
    def _find_function_context(self, file_path: str, line_number: int) -> Optional[str]:
        """Find the function context for a given line"""
        for func in self.codebase.functions:
            if func.filepath == file_path:
                func_line = getattr(func, 'line_number', 0)
                if func_line <= line_number:
                    # Simple heuristic: if we're within reasonable distance, assume we're in this function
                    if line_number - func_line < 100:  # Adjust based on typical function length
                        return func.name
        return None
    
    def _find_class_context(self, file_path: str, line_number: int) -> Optional[str]:
        """Find the class context for a given line"""
        for cls in self.codebase.classes:
            if cls.filepath == file_path:
                cls_line = getattr(cls, 'line_number', 0)
                if cls_line <= line_number:
                    # Simple heuristic: if we're within reasonable distance, assume we're in this class
                    if line_number - cls_line < 200:  # Adjust based on typical class length
                        return cls.name
        return None
    
    def _get_scope_variables(self, file_path: str, line_number: int) -> List[str]:
        """Get variables in scope at a specific line"""
        variables = []
        
        if file_path in self.file_contents_cache:
            file_data = self.file_contents_cache[file_path]
            if file_data['ast']:
                try:
                    # Simple variable extraction from AST
                    for node in ast.walk(file_data['ast']):
                        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                            variables.append(node.id)
                except Exception:
                    pass
        
        return list(set(variables))
    
    def _get_imports_in_scope(self, file_path: str) -> List[str]:
        """Get all imports in the file"""
        imports = []
        
        for file in self.codebase.files:
            if file.filepath == file_path:
                for imp in file.imports:
                    imports.append(imp.name)
        
        return imports
    
    def _analyze_import_root_cause(self, imp: Import, file) -> str:
        """Analyze the root cause of an import error"""
        # Check if it's a typo
        similar_imports = self._find_similar_imports(imp.name)
        if similar_imports:
            return f"Possible typo. Similar imports found: {', '.join(similar_imports)}"
        
        # Check if it's a missing dependency
        if '.' not in imp.name:
            return "Possible missing external dependency"
        
        # Check if it's a circular import
        if self._is_circular_import(imp, file):
            return "Circular import detected"
        
        return "Module not found in current environment"
    
    def _generate_import_fix_suggestions(self, imp: Import, file) -> List[ErrorSuggestion]:
        """Generate fix suggestions for import errors"""
        suggestions = []
        
        # Auto-fix suggestion for common typos
        similar_imports = self._find_similar_imports(imp.name)
        if similar_imports:
            suggestions.append(ErrorSuggestion(
                suggestion_type='auto_fix',
                description=f"Replace '{imp.name}' with '{similar_imports[0]}'",
                code_example=f"import {similar_imports[0]}",
                confidence_score=0.8,
                estimated_effort='low'
            ))
        
        # Manual fix suggestions
        suggestions.append(ErrorSuggestion(
            suggestion_type='manual_fix',
            description=f"Install missing dependency: pip install {imp.name}",
            confidence_score=0.7,
            estimated_effort='low'
        ))
        
        suggestions.append(ErrorSuggestion(
            suggestion_type='manual_fix',
            description=f"Check if '{imp.name}' is the correct module name",
            confidence_score=0.6,
            estimated_effort='medium'
        ))
        
        return suggestions
    
    def _find_similar_imports(self, import_name: str) -> List[str]:
        """Find similar import names that might be typos"""
        similar = []
        all_imports = set()
        
        # Collect all successful imports
        for file in self.codebase.files:
            for imp in file.imports:
                if imp.resolved_symbol:
                    all_imports.add(imp.name)
        
        # Find similar names using simple string similarity
        for existing_import in all_imports:
            if self._string_similarity(import_name, existing_import) > 0.8:
                similar.append(existing_import)
        
        return similar[:3]  # Return top 3 matches
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (simple implementation)"""
        if not s1 or not s2:
            return 0.0
        
        # Simple Levenshtein-like similarity
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if len(s1) > len(s2) else s1
        
        if len(longer) == 0:
            return 1.0
        
        return (len(longer) - self._levenshtein_distance(longer, shorter)) / len(longer)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _is_circular_import(self, imp: Import, file) -> bool:
        """Check if this is a circular import"""
        # Simple circular import detection
        # This is a placeholder - real implementation would need more sophisticated analysis
        return False
    
    def _find_dependent_files(self, file_path: str) -> List[str]:
        """Find files that depend on the given file"""
        dependents = []
        
        for file in self.codebase.files:
            for imp in file.imports:
                if imp.resolved_symbol and hasattr(imp.resolved_symbol, 'filepath'):
                    if imp.resolved_symbol.filepath == file_path:
                        dependents.append(file.filepath)
        
        return list(set(dependents))
    
    def _find_external_references(self, symbol_name: str) -> List[str]:
        """Find external references for a symbol (documentation, etc.)"""
        # Placeholder for external reference finding
        # Could integrate with documentation APIs, Stack Overflow, etc.
        return []
    
    def _generate_refactor_example(self, func: Function) -> str:
        """Generate a refactoring example for complex functions"""
        return f"""
# Example refactoring for {func.name}:
def {func.name}_part1():
    # Extract first logical block
    pass

def {func.name}_part2():
    # Extract second logical block
    pass

def {func.name}():
    # Orchestrate the parts
    result1 = {func.name}_part1()
    result2 = {func.name}_part2()
    return combine_results(result1, result2)
"""
    
    def _detect_long_functions(self, file_path: str, ast_tree):
        """Detect functions that are too long"""
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    function_length = node.end_lineno - node.lineno
                    if function_length > 50:  # Threshold for long functions
                        context = self._get_code_context(file_path, node.lineno)
                        
                        error = ErrorInfo(
                            error_type="CodeSmell",
                            severity="medium",
                            message=f"Long function: {node.name} ({function_length} lines)",
                            detailed_description=f"The function '{node.name}' is {function_length} lines long, which exceeds the recommended maximum of 50 lines.",
                            file_path=file_path,
                            line_number=node.lineno,
                            symbol_name=node.name,
                            code_context=context,
                            root_cause="Function is too long and should be broken down",
                            suggestions=[
                                ErrorSuggestion(
                                    suggestion_type='refactor',
                                    description=f"Break down '{node.name}' into smaller functions",
                                    confidence_score=0.8,
                                    estimated_effort='high'
                                )
                            ],
                            auto_fixable=False,
                            tags=['code_smell', 'long_function', 'maintainability']
                        )
                        self.errors.append(error)
    
    def _detect_long_parameter_lists(self, file_path: str, ast_tree):
        """Detect functions with too many parameters"""
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:  # Threshold for too many parameters
                    context = self._get_code_context(file_path, node.lineno)
                    
                    error = ErrorInfo(
                        error_type="CodeSmell",
                        severity="medium",
                        message=f"Too many parameters: {node.name} ({param_count} parameters)",
                        detailed_description=f"The function '{node.name}' has {param_count} parameters, which exceeds the recommended maximum of 5.",
                        file_path=file_path,
                        line_number=node.lineno,
                        symbol_name=node.name,
                        code_context=context,
                        root_cause="Function has too many parameters",
                        suggestions=[
                            ErrorSuggestion(
                                suggestion_type='refactor',
                                description=f"Consider using a configuration object or breaking down '{node.name}'",
                                confidence_score=0.7,
                                estimated_effort='medium'
                            )
                        ],
                        auto_fixable=False,
                        tags=['code_smell', 'parameter_list', 'design']
                    )
                    self.errors.append(error)
    
    def _detect_duplicate_code(self, file_path: str, content: str):
        """Detect duplicate code blocks"""
        # Simple duplicate detection - look for repeated lines
        lines = content.split('\n')
        line_counts = Counter(line.strip() for line in lines if line.strip())
        
        for line, count in line_counts.items():
            if count > 3 and len(line) > 20:  # Threshold for duplication
                # Find line numbers where this duplication occurs
                line_numbers = [i + 1 for i, l in enumerate(lines) if l.strip() == line]
                
                if len(line_numbers) > 1:
                    context = self._get_code_context(file_path, line_numbers[0])
                    
                    error = ErrorInfo(
                        error_type="CodeSmell",
                        severity="low",
                        message=f"Duplicate code detected: '{line[:50]}...'",
                        detailed_description=f"The line '{line}' appears {count} times in the file, indicating possible code duplication.",
                        file_path=file_path,
                        line_number=line_numbers[0],
                        code_context=context,
                        root_cause="Code duplication detected",
                        suggestions=[
                            ErrorSuggestion(
                                suggestion_type='refactor',
                                description="Extract common code into a function or constant",
                                confidence_score=0.6,
                                estimated_effort='medium'
                            )
                        ],
                        auto_fixable=False,
                        tags=['code_smell', 'duplication', 'refactor']
                    )
                    self.errors.append(error)
    
    def _analyze_error_patterns(self):
        """Analyze patterns in detected errors"""
        print("🔍 Analyzing error patterns...")
        
        # Count error types
        for error in self.errors:
            self.error_patterns[error.error_type] += 1
        
        # Identify hotspot files (files with many errors)
        file_error_counts = defaultdict(int)
        for error in self.errors:
            file_error_counts[error.file_path] += 1
        
        # Add hotspot analysis to metrics
        self.metrics['error_hotspots'] = dict(sorted(
            file_error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])  # Top 10 files with most errors
    
    def _add_syntax_error(self, file_path: str, syntax_error: SyntaxError):
        """Add a syntax error to the error list"""
        context = self._get_code_context(file_path, syntax_error.lineno or 1)
        
        error = ErrorInfo(
            error_type="SyntaxError",
            severity="critical",
            message=f"Syntax error: {syntax_error.msg}",
            detailed_description=f"Python syntax error in file: {syntax_error.msg}",
            file_path=file_path,
            line_number=syntax_error.lineno,
            column_number=syntax_error.offset,
            code_context=context,
            root_cause="Invalid Python syntax",
            suggestions=[
                ErrorSuggestion(
                    suggestion_type='manual_fix',
                    description="Fix the syntax error according to Python grammar rules",
                    confidence_score=1.0,
                    estimated_effort='low'
                )
            ],
            auto_fixable=False,
            tags=['syntax', 'critical', 'python']
        )
        self.errors.append(error)


def analyze_codebase_enhanced(repo_path: str) -> VisualizationData:
    """Main function to perform enhanced codebase analysis"""
    print(f"🚀 Starting enhanced analysis of: {repo_path}")
    
    # Initialize codebase
    if repo_path.startswith("http") or "/" in repo_path:
        codebase = Codebase.from_repo(repo_path)
    else:
        codebase = Codebase.from_path(repo_path)
    
    # Perform analysis
    analyzer = EnhancedCodebaseAnalyzer(codebase)
    results = analyzer.analyze_complete()
    
    print("🎉 Enhanced analysis complete!")
    return results


if __name__ == "__main__":
    # Example usage
    results = analyze_codebase_enhanced("fastapi/fastapi")
    print(f"Analysis complete! Found {results.metrics_summary['total_errors']} errors")
