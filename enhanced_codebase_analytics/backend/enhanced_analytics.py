"""
Enhanced Codebase Analytics with Visualization, File Tree, Error Detection & Resolution
"""

import json
import math
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import networkx as nx

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
class ErrorInfo:
    """Represents a code error with resolution information"""
    error_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    symbol_name: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    blast_radius: List[str] = None  # List of affected files/symbols


@dataclass
class FileTreeNode:
    """Represents a node in the file tree"""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    lines_of_code: Optional[int] = None
    complexity_score: Optional[float] = None
    error_count: int = 0
    children: List['FileTreeNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class VisualizationData:
    """Contains all data needed for visualization"""
    dependency_graph: Dict[str, Any]
    call_graph: Dict[str, Any]
    complexity_heatmap: Dict[str, Any]
    error_blast_radius: Dict[str, Any]
    file_tree: FileTreeNode
    metrics_summary: Dict[str, Any]


class EnhancedCodebaseAnalyzer:
    """Enhanced analyzer with visualization, error detection, and resolution capabilities"""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.dependency_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.errors: List[ErrorInfo] = []
        self.metrics = {}
        
    def analyze_complete(self) -> VisualizationData:
        """Perform complete analysis and return visualization data"""
        print("🔍 Starting enhanced codebase analysis...")
        
        # Core analysis
        self._analyze_dependencies()
        self._analyze_call_relationships()
        self._detect_errors()
        self._calculate_metrics()
        
        # Generate visualizations
        file_tree = self._build_file_tree()
        dependency_viz = self._generate_dependency_visualization()
        call_viz = self._generate_call_visualization()
        complexity_heatmap = self._generate_complexity_heatmap()
        error_blast_radius = self._generate_error_blast_radius()
        
        print(f"✅ Analysis complete! Found {len(self.errors)} issues")
        
        return VisualizationData(
            dependency_graph=dependency_viz,
            call_graph=call_viz,
            complexity_heatmap=complexity_heatmap,
            error_blast_radius=error_blast_radius,
            file_tree=file_tree,
            metrics_summary=self.metrics
        )
    
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
    
    def _detect_errors(self):
        """Detect various types of errors in the codebase"""
        print("🚨 Detecting errors...")
        
        self._detect_import_errors()
        self._detect_symbol_resolution_errors()
        self._detect_dead_code()
        self._detect_complexity_issues()
        self._detect_configuration_errors()
    
    def _detect_import_errors(self):
        """Detect import-related errors"""
        for file in self.codebase.files:
            for imp in file.imports:
                if not imp.resolved_symbol and not isinstance(imp.imported_symbol, ExternalModule):
                    error = ErrorInfo(
                        error_type="ImportError",
                        severity="high",
                        message=f"Unresolved import: {imp.name}",
                        file_path=file.filepath,
                        line_number=getattr(imp, 'line_number', None),
                        symbol_name=imp.name,
                        suggested_fix=f"Add missing import or check module path",
                        auto_fixable=True,
                        blast_radius=self._calculate_import_blast_radius(imp)
                    )
                    self.errors.append(error)
    
    def _detect_symbol_resolution_errors(self):
        """Detect symbol resolution issues"""
        for symbol in self.codebase.symbols:
            # Check for undefined references
            if hasattr(symbol, 'usages'):
                for usage in symbol.usages:
                    if not usage.usage_symbol:
                        error = ErrorInfo(
                            error_type="SymbolError",
                            severity="medium",
                            message=f"Undefined symbol reference: {symbol.name}",
                            file_path=symbol.filepath,
                            symbol_name=symbol.name,
                            suggested_fix="Define the symbol or add proper import",
                            auto_fixable=False,
                            blast_radius=[symbol.filepath]
                        )
                        self.errors.append(error)
    
    def _detect_dead_code(self):
        """Detect unused functions and variables"""
        for func in self.codebase.functions:
            if hasattr(func, 'usages') and len(func.usages) == 0:
                # Check if it's not a main function or special method
                if not (func.name in ['main', '__init__', '__main__'] or 
                       func.name.startswith('test_')):
                    error = ErrorInfo(
                        error_type="DeadCode",
                        severity="low",
                        message=f"Unused function: {func.name}",
                        file_path=func.filepath,
                        symbol_name=func.name,
                        suggested_fix="Remove unused function or add usage",
                        auto_fixable=True,
                        blast_radius=[func.filepath]
                    )
                    self.errors.append(error)
    
    def _detect_complexity_issues(self):
        """Detect high complexity functions"""
        for func in self.codebase.functions:
            complexity = self._calculate_cyclomatic_complexity(func)
            if complexity > 20:  # High complexity threshold
                error = ErrorInfo(
                    error_type="ComplexityError",
                    severity="medium" if complexity <= 30 else "high",
                    message=f"High cyclomatic complexity: {complexity}",
                    file_path=func.filepath,
                    symbol_name=func.name,
                    suggested_fix="Refactor function to reduce complexity",
                    auto_fixable=False,
                    blast_radius=self._calculate_function_blast_radius(func)
                )
                self.errors.append(error)
    
    def _detect_configuration_errors(self):
        """Detect configuration and parameter errors"""
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
    
    def _calculate_metrics(self):
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
    
    def _build_file_tree(self) -> FileTreeNode:
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

