"""Enhanced Codebase Analysis for Dashboard Views with Issue Detection and Impact Analysis."""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels for dashboard display."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    """Categories of code issues for organization."""
    IMPLEMENTATION = "implementation"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    DEAD_CODE = "dead_code"
    DEPENDENCIES = "dependencies"
    PARAMETERS = "parameters"
    ERROR_HANDLING = "error_handling"


@dataclass
class CodeIssue:
    """Represents a code issue with context and impact information."""
    id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    impact_score: float = 0.0
    affected_symbols: List[str] = None
    suggested_fix: Optional[str] = None
    ai_analysis: Optional[str] = None
    
    def __post_init__(self):
        if self.affected_symbols is None:
            self.affected_symbols = []


@dataclass
class AnalysisNode:
    """Hierarchical node for expandable dashboard display."""
    id: str
    name: str
    type: str
    summary: Dict[str, Any]
    issues: List[CodeIssue]
    children: List['AnalysisNode']
    metadata: Dict[str, Any]
    expandable: bool = True
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


class CodebaseAnalyzer:
    """Comprehensive codebase analyzer for dashboard views."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.issues: List[CodeIssue] = []
        self.impact_graph: Dict[str, Set[str]] = defaultdict(set)
        self._build_impact_graph()
    
    def _build_impact_graph(self):
        """Build impact graph for blast radius analysis."""
        try:
            # Build dependency relationships
            for symbol in self.codebase.symbols:
                symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
                
                # Add dependencies
                if hasattr(symbol, 'dependencies'):
                    for dep in symbol.dependencies:
                        dep_id = f"{dep.__class__.__name__}:{getattr(dep, 'name', str(dep))}"
                        self.impact_graph[dep_id].add(symbol_id)
                
                # Add usages
                if hasattr(symbol, 'usages'):
                    for usage in symbol.usages:
                        usage_id = f"{usage.__class__.__name__}:{getattr(usage, 'name', str(usage))}"
                        self.impact_graph[symbol_id].add(usage_id)
        except Exception as e:
            logger.warning(f"Error building impact graph: {e}")
    
    def calculate_impact_score(self, symbol: Symbol) -> float:
        """Calculate impact score based on usage and dependencies."""
        try:
            symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
            
            # Base score from direct usages
            direct_usages = len(getattr(symbol, 'usages', []))
            
            # Amplify score based on transitive impact
            transitive_impact = len(self.impact_graph.get(symbol_id, set()))
            
            # Weight by symbol type
            type_weights = {
                'Function': 1.0,
                'Class': 1.5,
                'GlobalVar': 0.8,
                'Interface': 1.2
            }
            
            weight = type_weights.get(symbol.__class__.__name__, 1.0)
            
            return (direct_usages + transitive_impact * 0.5) * weight
        except Exception:
            return 0.0
    
    def detect_issues(self) -> List[CodeIssue]:
        """Detect various code issues across the codebase."""
        self.issues = []
        
        # Detect different types of issues
        self._detect_documentation_issues()
        self._detect_dead_code_issues()
        self._detect_parameter_issues()
        self._detect_error_handling_issues()
        self._detect_complexity_issues()
        self._detect_dependency_issues()
        
        return self.issues
    
    def _detect_documentation_issues(self):
        """Detect missing or poor documentation."""
        for func in self.codebase.functions:
            try:
                if not getattr(func, 'docstring', None):
                    impact_score = self.calculate_impact_score(func)
                    severity = IssueSeverity.HIGH if impact_score > 5 else IssueSeverity.MEDIUM
                    
                    self.issues.append(CodeIssue(
                        id=f"doc_missing_{func.name}",
                        title=f"Missing docstring: {func.name}",
                        description=f"Function '{func.name}' lacks documentation",
                        severity=severity,
                        category=IssueCategory.DOCUMENTATION,
                        file_path=getattr(func, 'filepath', 'unknown'),
                        line_start=getattr(func, 'line_start', None),
                        symbol_name=func.name,
                        symbol_type="Function",
                        impact_score=impact_score,
                        suggested_fix="Add a comprehensive docstring describing the function's purpose, parameters, and return value"
                    ))
            except Exception as e:
                logger.warning(f"Error analyzing function {getattr(func, 'name', 'unknown')}: {e}")
    
    def _detect_dead_code_issues(self):
        """Detect unused functions and classes."""
        for func in self.codebase.functions:
            try:
                usages = getattr(func, 'usages', [])
                call_sites = getattr(func, 'call_sites', [])
                
                if not usages and not call_sites:
                    self.issues.append(CodeIssue(
                        id=f"dead_code_{func.name}",
                        title=f"Unused function: {func.name}",
                        description=f"Function '{func.name}' is never called",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.DEAD_CODE,
                        file_path=getattr(func, 'filepath', 'unknown'),
                        line_start=getattr(func, 'line_start', None),
                        symbol_name=func.name,
                        symbol_type="Function",
                        impact_score=0.0,
                        suggested_fix="Consider removing this function if it's truly unused, or add tests if it's meant to be a public API"
                    ))
            except Exception as e:
                logger.warning(f"Error analyzing dead code for {getattr(func, 'name', 'unknown')}: {e}")
    
    def _detect_parameter_issues(self):
        """Detect parameter-related issues."""
        for func in self.codebase.functions:
            try:
                parameters = getattr(func, 'parameters', [])
                function_calls = getattr(func, 'function_calls', [])
                
                # Check for functions with too many parameters
                if len(parameters) > 7:
                    self.issues.append(CodeIssue(
                        id=f"param_count_{func.name}",
                        title=f"Too many parameters: {func.name}",
                        description=f"Function '{func.name}' has {len(parameters)} parameters (recommended: ≤7)",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.PARAMETERS,
                        file_path=getattr(func, 'filepath', 'unknown'),
                        line_start=getattr(func, 'line_start', None),
                        symbol_name=func.name,
                        symbol_type="Function",
                        impact_score=self.calculate_impact_score(func),
                        suggested_fix="Consider grouping related parameters into a configuration object or data class"
                    ))
                
                # Check for missing type annotations
                untyped_params = [p for p in parameters if not getattr(p, 'type_annotation', None)]
                if untyped_params and len(parameters) > 0:
                    self.issues.append(CodeIssue(
                        id=f"param_types_{func.name}",
                        title=f"Missing type annotations: {func.name}",
                        description=f"Function '{func.name}' has {len(untyped_params)} parameters without type annotations",
                        severity=IssueSeverity.LOW,
                        category=IssueCategory.PARAMETERS,
                        file_path=getattr(func, 'filepath', 'unknown'),
                        line_start=getattr(func, 'line_start', None),
                        symbol_name=func.name,
                        symbol_type="Function",
                        impact_score=self.calculate_impact_score(func),
                        suggested_fix="Add type annotations to improve code clarity and enable better IDE support"
                    ))
            except Exception as e:
                logger.warning(f"Error analyzing parameters for {getattr(func, 'name', 'unknown')}: {e}")
    
    def _detect_error_handling_issues(self):
        """Detect missing error handling."""
        for func in self.codebase.functions:
            try:
                is_async = getattr(func, 'is_async', False)
                
                # Check for async functions without try-catch
                if is_async:
                    # This is a simplified check - in practice, you'd analyze the AST
                    source = getattr(func, 'source', '')
                    if 'try:' not in source and 'except' not in source:
                        self.issues.append(CodeIssue(
                            id=f"error_handling_{func.name}",
                            title=f"Missing error handling: {func.name}",
                            description=f"Async function '{func.name}' lacks error handling",
                            severity=IssueSeverity.HIGH,
                            category=IssueCategory.ERROR_HANDLING,
                            file_path=getattr(func, 'filepath', 'unknown'),
                            line_start=getattr(func, 'line_start', None),
                            symbol_name=func.name,
                            symbol_type="Function",
                            impact_score=self.calculate_impact_score(func),
                            suggested_fix="Add try-except blocks to handle potential exceptions in async operations"
                        ))
            except Exception as e:
                logger.warning(f"Error analyzing error handling for {getattr(func, 'name', 'unknown')}: {e}")
    
    def _detect_complexity_issues(self):
        """Detect overly complex functions."""
        for func in self.codebase.functions:
            try:
                source = getattr(func, 'source', '')
                lines = source.split('\n') if source else []
                
                # Simple complexity heuristics
                if len(lines) > 50:
                    self.issues.append(CodeIssue(
                        id=f"complexity_{func.name}",
                        title=f"Function too long: {func.name}",
                        description=f"Function '{func.name}' has {len(lines)} lines (recommended: ≤50)",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.MAINTAINABILITY,
                        file_path=getattr(func, 'filepath', 'unknown'),
                        line_start=getattr(func, 'line_start', None),
                        symbol_name=func.name,
                        symbol_type="Function",
                        impact_score=self.calculate_impact_score(func),
                        suggested_fix="Consider breaking this function into smaller, more focused functions"
                    ))
            except Exception as e:
                logger.warning(f"Error analyzing complexity for {getattr(func, 'name', 'unknown')}: {e}")
    
    def _detect_dependency_issues(self):
        """Detect dependency-related issues."""
        try:
            # Detect circular dependencies
            visited = set()
            rec_stack = set()
            
            def has_cycle(symbol_id: str) -> bool:
                if symbol_id in rec_stack:
                    return True
                if symbol_id in visited:
                    return False
                
                visited.add(symbol_id)
                rec_stack.add(symbol_id)
                
                for dependent in self.impact_graph.get(symbol_id, set()):
                    if has_cycle(dependent):
                        return True
                
                rec_stack.remove(symbol_id)
                return False
            
            for symbol_id in self.impact_graph:
                if symbol_id not in visited and has_cycle(symbol_id):
                    self.issues.append(CodeIssue(
                        id=f"circular_dep_{symbol_id}",
                        title=f"Circular dependency detected",
                        description=f"Symbol '{symbol_id}' is part of a circular dependency",
                        severity=IssueSeverity.HIGH,
                        category=IssueCategory.DEPENDENCIES,
                        file_path="multiple",
                        symbol_name=symbol_id.split(':')[-1],
                        symbol_type=symbol_id.split(':')[0],
                        impact_score=5.0,
                        suggested_fix="Refactor code to break circular dependencies, possibly by introducing interfaces or dependency injection"
                    ))
        except Exception as e:
            logger.warning(f"Error detecting dependency issues: {e}")

    async def analyze_with_ai(self, issue: CodeIssue) -> str:
        """Use AI to provide deeper analysis of an issue."""
        try:
            if hasattr(self.codebase, 'ai'):
                # Get the symbol for context
                symbol = None
                if issue.symbol_name:
                    if issue.symbol_type == "Function":
                        symbol = next((f for f in self.codebase.functions if f.name == issue.symbol_name), None)
                    elif issue.symbol_type == "Class":
                        symbol = next((c for c in self.codebase.classes if c.name == issue.symbol_name), None)
                
                if symbol:
                    prompt = f"""Analyze this code issue and provide specific recommendations:

Issue: {issue.title}
Description: {issue.description}
Category: {issue.category.value}
Severity: {issue.severity.value}

Please provide:
1. Root cause analysis
2. Specific code improvements
3. Best practices to prevent similar issues
4. Impact assessment if not fixed
"""
                    
                    result = await self.codebase.ai(prompt, target=symbol)
                    return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            logger.warning(f"Error in AI analysis: {e}")
        
        return "AI analysis not available"

    def get_blast_radius(self, symbol_name: str, symbol_type: str) -> List[str]:
        """Calculate blast radius for a symbol change."""
        symbol_id = f"{symbol_type}:{symbol_name}"
        affected = set()
        
        def collect_affected(current_id: str, depth: int = 0):
            if depth > 10 or current_id in affected:  # Prevent infinite recursion
                return
            affected.add(current_id)
            
            for dependent in self.impact_graph.get(current_id, set()):
                collect_affected(dependent, depth + 1)
        
        collect_affected(symbol_id)
        return list(affected)

    def generate_dashboard_data(self) -> AnalysisNode:
        """Generate hierarchical data structure for dashboard display."""
        # Detect all issues first
        issues = self.detect_issues()
        
        # Create root node
        root = AnalysisNode(
            id="codebase_root",
            name="Codebase Analysis",
            type="codebase",
            summary=self._get_codebase_summary_dict(),
            issues=[],
            children=[],
            metadata={
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.severity == IssueSeverity.CRITICAL]),
                "high_issues": len([i for i in issues if i.severity == IssueSeverity.HIGH]),
                "analysis_timestamp": "now"  # You'd use actual timestamp
            }
        )
        
        # Group issues by category
        issues_by_category = defaultdict(list)
        for issue in issues:
            issues_by_category[issue.category].append(issue)
        
        # Create category nodes
        for category, category_issues in issues_by_category.items():
            category_node = AnalysisNode(
                id=f"category_{category.value}",
                name=category.value.replace('_', ' ').title(),
                type="category",
                summary={
                    "total_issues": len(category_issues),
                    "severity_breakdown": {
                        severity.value: len([i for i in category_issues if i.severity == severity])
                        for severity in IssueSeverity
                    }
                },
                issues=category_issues,
                children=[],
                metadata={"category": category.value}
            )
            root.children.append(category_node)
        
        # Create file-based analysis nodes
        files_node = self._create_files_analysis_node()
        root.children.append(files_node)
        
        # Create function flow analysis nodes
        flows_node = self._create_function_flows_node()
        root.children.append(flows_node)
        
        return root

    def _get_codebase_summary_dict(self) -> Dict[str, Any]:
        """Get codebase summary as dictionary."""
        try:
            return {
                "total_files": len(list(self.codebase.files)),
                "total_functions": len(list(self.codebase.functions)),
                "total_classes": len(list(self.codebase.classes)),
                "total_symbols": len(list(self.codebase.symbols)),
                "total_imports": len(list(self.codebase.imports)),
                "total_nodes": len(self.codebase.ctx.get_nodes()),
                "total_edges": len(self.codebase.ctx.edges)
            }
        except Exception as e:
            logger.warning(f"Error getting codebase summary: {e}")
            return {"error": str(e)}

    def _create_files_analysis_node(self) -> AnalysisNode:
        """Create file-based analysis node."""
        files_node = AnalysisNode(
            id="files_analysis",
            name="Files Analysis",
            type="files",
            summary={"total_files": len(list(self.codebase.files))},
            issues=[],
            children=[],
            metadata={}
        )
        
        # Add file nodes
        for file in list(self.codebase.files)[:20]:  # Limit for performance
            try:
                file_issues = [i for i in self.issues if i.file_path == getattr(file, 'filepath', '')]
                
                file_node = AnalysisNode(
                    id=f"file_{getattr(file, 'filepath', 'unknown').replace('/', '_')}",
                    name=getattr(file, 'name', 'unknown'),
                    type="file",
                    summary={
                        "functions": len(getattr(file, 'functions', [])),
                        "classes": len(getattr(file, 'classes', [])),
                        "imports": len(getattr(file, 'imports', [])),
                        "issues": len(file_issues)
                    },
                    issues=file_issues,
                    children=[],
                    metadata={"filepath": getattr(file, 'filepath', 'unknown')}
                )
                files_node.children.append(file_node)
            except Exception as e:
                logger.warning(f"Error creating file node: {e}")
        
        return files_node

    def _create_function_flows_node(self) -> AnalysisNode:
        """Create function flow analysis node."""
        flows_node = AnalysisNode(
            id="function_flows",
            name="Function Flows",
            type="flows",
            summary={"total_functions": len(list(self.codebase.functions))},
            issues=[],
            children=[],
            metadata={}
        )
        
        # Find functions with high call complexity
        for func in list(self.codebase.functions)[:10]:  # Limit for performance
            try:
                call_sites = getattr(func, 'call_sites', [])
                function_calls = getattr(func, 'function_calls', [])
                
                if len(call_sites) > 5 or len(function_calls) > 10:
                    flow_node = AnalysisNode(
                        id=f"flow_{func.name}",
                        name=f"Flow: {func.name}",
                        type="function_flow",
                        summary={
                            "incoming_calls": len(call_sites),
                            "outgoing_calls": len(function_calls),
                            "complexity_score": len(call_sites) + len(function_calls)
                        },
                        issues=[i for i in self.issues if i.symbol_name == func.name],
                        children=[],
                        metadata={
                            "function_name": func.name,
                            "blast_radius": len(self.get_blast_radius(func.name, "Function"))
                        }
                    )
                    flows_node.children.append(flow_node)
            except Exception as e:
                logger.warning(f"Error creating flow node for {getattr(func, 'name', 'unknown')}: {e}")
        
        return flows_node

    def to_json(self, root_node: AnalysisNode) -> str:
        """Convert analysis tree to JSON for dashboard consumption."""
        def convert_node(node: AnalysisNode) -> Dict[str, Any]:
            return {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "summary": node.summary,
                "issues": [asdict(issue) for issue in node.issues],
                "children": [convert_node(child) for child in node.children],
                "metadata": node.metadata,
                "expandable": node.expandable
            }
        
        return json.dumps(convert_node(root_node), indent=2, default=str)


# Enhanced utility functions for backward compatibility
def get_codebase_summary(codebase: Codebase) -> str:
    """Get basic codebase summary (backward compatibility)."""
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """


def hop_through_imports(imp: Import, max_hops: int = 10) -> Union[Symbol, ExternalModule]:
    """Finds the root symbol for an import by following the chain.
    
    Args:
        imp: The import to resolve
        max_hops: Maximum number of hops to prevent infinite loops
        
    Returns:
        The final resolved symbol or external module
    """
    current = imp
    hops = 0
    
    while isinstance(current, Import) and hops < max_hops:
        if hasattr(current, 'imported_symbol'):
            current = current.imported_symbol
        else:
            break
        hops += 1
    
    return current


def get_function_context(function: Function) -> Dict[str, Any]:
    """Get the implementation, dependencies, and usages of a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary containing implementation, dependencies, and usages
    """
    context = {
        "implementation": {
            "source": getattr(function, 'source', ''),
            "filepath": getattr(function, 'filepath', 'unknown'),
            "line_start": getattr(function, 'line_start', None),
            "line_end": getattr(function, 'line_end', None),
            "signature": getattr(function, 'signature', ''),
            "is_async": getattr(function, 'is_async', False),
            "parameters": [
                {
                    "name": getattr(p, 'name', ''),
                    "type": getattr(p, 'type_annotation', None),
                    "default": getattr(p, 'default', None)
                }
                for p in getattr(function, 'parameters', [])
            ]
        },
        "dependencies": [],
        "usages": [],
        "call_sites": [],
        "function_calls": []
    }

    # Add dependencies
    try:
        for dep in getattr(function, 'dependencies', []):
            # Hop through imports to find the root symbol source
            if isinstance(dep, Import):
                dep = hop_through_imports(dep)

            dep_info = {
                "name": getattr(dep, 'name', str(dep)),
                "source": getattr(dep, 'source', ''),
                "filepath": getattr(dep, 'filepath', 'unknown'),
                "type": dep.__class__.__name__
            }
            context["dependencies"].append(dep_info)
    except Exception as e:
        logger.warning(f"Error getting dependencies for {function.name}: {e}")

    # Add usages
    try:
        for usage in getattr(function, 'usages', []):
            usage_info = {
                "source": getattr(usage, 'source', ''),
                "filepath": getattr(usage, 'filepath', 'unknown'),
                "line_start": getattr(usage, 'line_start', None),
                "context": getattr(usage, 'usage_symbol', {})
            }
            context["usages"].append(usage_info)
    except Exception as e:
        logger.warning(f"Error getting usages for {function.name}: {e}")

    # Add call sites (where this function is called)
    try:
        for call_site in getattr(function, 'call_sites', []):
            call_site_info = {
                "source": getattr(call_site, 'source', ''),
                "filepath": getattr(call_site, 'filepath', 'unknown'),
                "line_start": getattr(call_site, 'line_start', None),
                "caller_function": getattr(call_site, 'parent_function', {})
            }
            context["call_sites"].append(call_site_info)
    except Exception as e:
        logger.warning(f"Error getting call sites for {function.name}: {e}")

    # Add function calls (functions this function calls)
    try:
        for func_call in getattr(function, 'function_calls', []):
            func_call_info = {
                "name": getattr(func_call, 'name', ''),
                "source": getattr(func_call, 'source', ''),
                "args": [
                    {
                        "value": getattr(arg, 'value', ''),
                        "name": getattr(arg, 'name', None),
                        "is_named": getattr(arg, 'is_named', False)
                    }
                    for arg in getattr(func_call, 'args', [])
                ],
                "line_start": getattr(func_call, 'line_start', None)
            }
            context["function_calls"].append(func_call_info)
    except Exception as e:
        logger.warning(f"Error getting function calls for {function.name}: {e}")

    return context


def analyze_codebase(codebase: Codebase) -> Dict[str, Any]:
    """Comprehensive codebase analysis with issue flagging.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary containing analysis results and flagged issues
    """
    analyzer = CodebaseAnalyzer(codebase)
    
    # Detect issues
    issues = analyzer.detect_issues()
    
    # Generate dashboard data
    dashboard_data = analyzer.generate_dashboard_data()
    
    # Create analysis summary
    analysis_result = {
        "summary": analyzer._get_codebase_summary_dict(),
        "issues": [asdict(issue) for issue in issues],
        "dashboard_data": asdict(dashboard_data),
        "metrics": {
            "total_issues": len(issues),
            "issues_by_severity": {
                severity.value: len([i for i in issues if i.severity == severity])
                for severity in IssueSeverity
            },
            "issues_by_category": {
                category.value: len([i for i in issues if i.category == category])
                for category in IssueCategory
            }
        }
    }
    
    return analysis_result


def run_training_data_generation(codebase: Codebase) -> Dict[str, Any]:
    """Generate training data using a node2vec-like approach for code embeddings.
    
    Args:
        codebase: The codebase to process
        
    Returns:
        Dictionary containing training data and metadata
    """
    # Track all function contexts
    training_data = {
        "functions": [],
        "metadata": {
            "total_functions": len(list(codebase.functions)),
            "total_processed": 0,
            "avg_dependencies": 0,
            "avg_usages": 0,
        },
    }

    # Process each function in the codebase
    for function in codebase.functions:
        try:
            # Skip if function is too small
            source = getattr(function, 'source', '')
            if len(source.split("\n")) < 2:
                continue

            # Get function context
            context = get_function_context(function)

            # Only keep functions with enough context
            if len(context["dependencies"]) + len(context["usages"]) > 0:
                training_data["functions"].append(context)
        except Exception as e:
            logger.warning(f"Error processing function {getattr(function, 'name', 'unknown')}: {e}")

    # Update metadata
    training_data["metadata"]["total_processed"] = len(training_data["functions"])
    if training_data["functions"]:
        training_data["metadata"]["avg_dependencies"] = sum(
            len(f["dependencies"]) for f in training_data["functions"]
        ) / len(training_data["functions"])
        training_data["metadata"]["avg_usages"] = sum(
            len(f["usages"]) for f in training_data["functions"]
        ) / len(training_data["functions"])

    return training_data


def create_training_example(function_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a masked prediction example from function data.
    
    Args:
        function_data: Function context data
        
    Returns:
        Training example with context and target
    """
    return {
        "context": {
            "dependencies": function_data["dependencies"],
            "usages": function_data["usages"],
            "call_sites": function_data["call_sites"],
            "function_calls": function_data["function_calls"]
        },
        "target": function_data["implementation"]
    }
