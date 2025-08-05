"""
Dependency Analyzer for Graph-Sitter Analytics

Analyzes dependency relationships and identifies issues:
- Circular dependencies
- Dependency coupling metrics
- Unused dependencies
- Dependency security issues
- Architecture violations
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, deque
import networkx as nx

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.shared.logging.logger import get_logger

from ..core.base_analyzer import BaseAnalyzer
from ..core.analysis_result import AnalysisResult, Finding, Severity, FindingType

logger = get_logger(__name__)


class DependencyAnalyzer(BaseAnalyzer):
    """
    Analyzes dependency relationships and architecture quality.
    
    Leverages Graph-Sitter's dependency tracking and networkx for
    graph analysis to identify dependency issues and violations.
    """
    
    def __init__(self):
        super().__init__("dependency")
        self.supported_languages = {"python", "typescript", "javascript", "java", "cpp", "rust", "go"}
        
        # Dependency thresholds
        self.coupling_thresholds = {
            "low": 5,
            "medium": 10,
            "high": 15,
            "critical": 25
        }
        
        # Known problematic dependencies (security/maintenance issues)
        self.problematic_dependencies = {
            "python": [
                "pickle", "eval", "exec", "input",  # Security risks
                "imp",  # Deprecated
            ],
            "javascript": [
                "eval", "Function",  # Security risks
                "lodash",  # Often over-used
            ],
            "java": [
                "sun.misc.Unsafe",  # Internal API
                "java.awt.Desktop",  # Platform-specific
            ]
        }
        
        # Architecture layer definitions
        self.architecture_layers = {
            "presentation": ["ui", "view", "component", "controller", "handler"],
            "business": ["service", "logic", "domain", "model", "entity"],
            "data": ["repository", "dao", "database", "storage", "persistence"],
            "infrastructure": ["config", "util", "helper", "common", "shared"]
        }
    
    @BaseAnalyzer.measure_execution_time
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """Perform comprehensive dependency analysis."""
        if not self.validate_codebase(codebase):
            result = self.create_result("failed")
            result.error_message = "Invalid codebase provided"
            return result
        
        result = self.create_result()
        
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(codebase)
            
            # Analyze different aspects
            circular_dependencies = self._find_circular_dependencies(dependency_graph)
            coupling_issues = self._analyze_coupling(codebase, dependency_graph)
            architecture_violations = self._check_architecture_violations(codebase, dependency_graph)
            external_dependency_issues = self._analyze_external_dependencies(codebase)
            dependency_metrics = self._calculate_dependency_metrics(dependency_graph)
            
            # Create findings
            all_issues = (circular_dependencies + coupling_issues + 
                         architecture_violations + external_dependency_issues)
            
            for issue in all_issues:
                finding = Finding(
                    type=FindingType.DEPENDENCY,
                    severity=issue["severity"],
                    title=issue["title"],
                    description=issue["description"],
                    file_path=issue["file_path"],
                    line_number=issue.get("line_number"),
                    recommendation=issue["recommendation"],
                    rule_id=issue["rule_id"],
                    metadata=issue.get("metadata", {})
                )
                result.add_finding(finding)
            
            # Calculate metrics
            result.metrics.files_analyzed = len([f for f in files if self.is_supported_file(str(f.filepath))])
            result.metrics.quality_score = self._calculate_dependency_score(all_issues, dependency_metrics)
            
            # Store detailed dependency metrics
            result.metrics.dependency_metrics = {
                "total_dependencies": dependency_graph.number_of_edges(),
                "total_modules": dependency_graph.number_of_nodes(),
                "circular_dependency_count": len(circular_dependencies),
                "average_coupling": dependency_metrics["average_coupling"],
                "max_coupling": dependency_metrics["max_coupling"],
                "dependency_depth": dependency_metrics["max_depth"],
                "external_dependencies": dependency_metrics["external_count"],
                "architecture_violations": len(architecture_violations),
                "dependency_distribution": dependency_metrics["distribution"],
                "most_coupled_modules": dependency_metrics["most_coupled"][:10]
            }
            
            # Generate recommendations
            result.recommendations = self._generate_dependency_recommendations(
                all_issues, dependency_metrics
            )
            
            logger.info(f"Dependency analysis completed: {len(all_issues)} issues found, "
                       f"{dependency_graph.number_of_edges()} dependencies analyzed")
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {str(e)}")
            result.status = "failed"
            result.error_message = str(e)
        
        return result
    
    def _build_dependency_graph(self, codebase: Codebase) -> nx.DiGraph:
        """Build a directed graph of dependencies."""
        graph = nx.DiGraph()
        
        # Add nodes for all files/modules
        for file in codebase.files:
            file_path = str(file.filepath)
            graph.add_node(file_path, type="file", file=file)
        
        # Add edges for imports and dependencies
        for file in codebase.files:
            file_path = str(file.filepath)
            
            # Add import dependencies
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    
                    # Handle different types of imported symbols
                    if isinstance(imported_symbol, ExternalModule):
                        # External dependency
                        ext_name = getattr(imported_symbol, 'name', str(imported_symbol))
                        if not graph.has_node(ext_name):
                            graph.add_node(ext_name, type="external", module=imported_symbol)
                        graph.add_edge(file_path, ext_name, type="import")
                    
                    elif hasattr(imported_symbol, 'filepath'):
                        # Internal dependency
                        target_path = str(imported_symbol.filepath)
                        if graph.has_node(target_path):
                            graph.add_edge(file_path, target_path, type="import")
            
            # Add function call dependencies
            for func in file.functions:
                if hasattr(func, 'function_calls'):
                    for call in func.function_calls:
                        if hasattr(call, 'filepath') and call.filepath != func.filepath:
                            target_path = str(call.filepath)
                            if graph.has_node(target_path):
                                graph.add_edge(file_path, target_path, type="call")
        
        return graph
    
    def _find_circular_dependencies(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Find circular dependencies in the dependency graph."""
        circular_deps = []
        
        try:
            # Find strongly connected components with more than one node
            sccs = list(nx.strongly_connected_components(graph))
            
            for scc in sccs:
                if len(scc) > 1:
                    # This is a circular dependency
                    cycle_nodes = list(scc)
                    
                    # Try to find the actual cycle path
                    try:
                        cycle = nx.find_cycle(graph.subgraph(scc), orientation='original')
                        cycle_path = [edge[0] for edge in cycle] + [cycle[-1][1]]
                    except nx.NetworkXNoCycle:
                        cycle_path = cycle_nodes
                    
                    circular_deps.append({
                        "severity": Severity.HIGH,
                        "title": f"Circular Dependency Detected",
                        "description": f"Circular dependency found between {len(cycle_nodes)} modules",
                        "file_path": cycle_path[0] if cycle_path else "unknown",
                        "recommendation": "Break circular dependency by introducing interfaces or restructuring code",
                        "rule_id": "DEP_CIRCULAR",
                        "metadata": {
                            "cycle_nodes": cycle_nodes,
                            "cycle_path": cycle_path,
                            "cycle_length": len(cycle_nodes)
                        }
                    })
        
        except Exception as e:
            logger.warning(f"Error finding circular dependencies: {str(e)}")
        
        return circular_deps
    
    def _analyze_coupling(self, codebase: Codebase, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Analyze coupling between modules."""
        coupling_issues = []
        
        # Calculate coupling metrics for each node
        for node in graph.nodes():
            if graph.nodes[node].get("type") == "file":
                # Efferent coupling (outgoing dependencies)
                efferent = graph.out_degree(node)
                
                # Afferent coupling (incoming dependencies)
                afferent = graph.in_degree(node)
                
                # Total coupling
                total_coupling = efferent + afferent
                
                # Check thresholds
                if total_coupling >= self.coupling_thresholds["critical"]:
                    severity = Severity.CRITICAL
                elif total_coupling >= self.coupling_thresholds["high"]:
                    severity = Severity.HIGH
                elif total_coupling >= self.coupling_thresholds["medium"]:
                    severity = Severity.MEDIUM
                elif total_coupling >= self.coupling_thresholds["low"]:
                    severity = Severity.LOW
                else:
                    continue  # No issue
                
                coupling_issues.append({
                    "severity": severity,
                    "title": f"High Coupling: {self._get_module_name(node)}",
                    "description": f"Module has high coupling (efferent: {efferent}, afferent: {afferent})",
                    "file_path": node,
                    "recommendation": "Reduce coupling by applying dependency inversion or breaking down the module",
                    "rule_id": "DEP_COUPLING",
                    "metadata": {
                        "efferent_coupling": efferent,
                        "afferent_coupling": afferent,
                        "total_coupling": total_coupling,
                        "instability": efferent / (efferent + afferent) if (efferent + afferent) > 0 else 0
                    }
                })
        
        return coupling_issues
    
    def _check_architecture_violations(self, codebase: Codebase, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Check for architecture layer violations."""
        violations = []
        
        # Classify modules into layers
        module_layers = {}
        for node in graph.nodes():
            if graph.nodes[node].get("type") == "file":
                layer = self._classify_module_layer(node)
                module_layers[node] = layer
        
        # Check for violations (e.g., data layer depending on presentation layer)
        layer_hierarchy = ["presentation", "business", "data", "infrastructure"]
        
        for edge in graph.edges():
            source, target = edge
            source_layer = module_layers.get(source)
            target_layer = module_layers.get(target)
            
            if source_layer and target_layer and source_layer != target_layer:
                source_level = layer_hierarchy.index(source_layer) if source_layer in layer_hierarchy else -1
                target_level = layer_hierarchy.index(target_layer) if target_layer in layer_hierarchy else -1
                
                # Violation: lower layer depending on higher layer
                if source_level > target_level and source_level != -1 and target_level != -1:
                    violations.append({
                        "severity": Severity.MEDIUM,
                        "title": f"Architecture Layer Violation",
                        "description": f"{source_layer} layer module depends on {target_layer} layer module",
                        "file_path": source,
                        "recommendation": "Restructure dependencies to follow proper layered architecture",
                        "rule_id": "DEP_ARCH_VIOLATION",
                        "metadata": {
                            "source_module": source,
                            "target_module": target,
                            "source_layer": source_layer,
                            "target_layer": target_layer
                        }
                    })
        
        return violations
    
    def _analyze_external_dependencies(self, codebase: Codebase) -> List[Dict[str, Any]]:
        """Analyze external dependencies for issues."""
        issues = []
        
        # Track external dependencies
        external_deps = defaultdict(list)
        
        for file in codebase.files:
            file_language = self._detect_language(str(file.filepath))
            
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, ExternalModule):
                    module_name = getattr(imp.imported_symbol, 'name', str(imp.imported_symbol))
                    external_deps[module_name].append(str(file.filepath))
                    
                    # Check for problematic dependencies
                    problematic = self.problematic_dependencies.get(file_language, [])
                    if any(prob in module_name.lower() for prob in problematic):
                        issues.append({
                            "severity": Severity.MEDIUM,
                            "title": f"Problematic Dependency: {module_name}",
                            "description": f"Dependency '{module_name}' may have security or maintenance issues",
                            "file_path": str(file.filepath),
                            "line_number": getattr(imp, 'line_number', None),
                            "recommendation": "Consider alternative libraries or additional security measures",
                            "rule_id": "DEP_PROBLEMATIC",
                            "metadata": {
                                "dependency_name": module_name,
                                "language": file_language
                            }
                        })
        
        # Check for unused external dependencies (simplified heuristic)
        for dep_name, files in external_deps.items():
            if len(files) == 1:
                # Dependency used in only one file - might be over-engineering
                issues.append({
                    "severity": Severity.LOW,
                    "title": f"Single-Use External Dependency: {dep_name}",
                    "description": f"External dependency '{dep_name}' is only used in one file",
                    "file_path": files[0],
                    "recommendation": "Consider if this dependency is necessary or if functionality can be implemented locally",
                    "rule_id": "DEP_SINGLE_USE",
                    "metadata": {
                        "dependency_name": dep_name,
                        "usage_count": len(files)
                    }
                })
        
        return issues
    
    def _calculate_dependency_metrics(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Calculate various dependency metrics."""
        metrics = {}
        
        # Basic graph metrics
        metrics["total_nodes"] = graph.number_of_nodes()
        metrics["total_edges"] = graph.number_of_edges()
        
        # Coupling metrics
        file_nodes = [n for n in graph.nodes() if graph.nodes[n].get("type") == "file"]
        
        if file_nodes:
            couplings = []
            most_coupled = []
            
            for node in file_nodes:
                coupling = graph.in_degree(node) + graph.out_degree(node)
                couplings.append(coupling)
                most_coupled.append({
                    "module": self._get_module_name(node),
                    "coupling": coupling,
                    "efferent": graph.out_degree(node),
                    "afferent": graph.in_degree(node)
                })
            
            metrics["average_coupling"] = sum(couplings) / len(couplings)
            metrics["max_coupling"] = max(couplings) if couplings else 0
            metrics["most_coupled"] = sorted(most_coupled, key=lambda x: x["coupling"], reverse=True)
        else:
            metrics["average_coupling"] = 0
            metrics["max_coupling"] = 0
            metrics["most_coupled"] = []
        
        # Depth metrics (longest path)
        try:
            if nx.is_directed_acyclic_graph(graph):
                metrics["max_depth"] = nx.dag_longest_path_length(graph)
            else:
                metrics["max_depth"] = 0  # Has cycles
        except:
            metrics["max_depth"] = 0
        
        # External dependency count
        external_nodes = [n for n in graph.nodes() if graph.nodes[n].get("type") == "external"]
        metrics["external_count"] = len(external_nodes)
        
        # Distribution of dependencies
        in_degrees = [graph.in_degree(n) for n in file_nodes]
        out_degrees = [graph.out_degree(n) for n in file_nodes]
        
        metrics["distribution"] = {
            "in_degree_avg": sum(in_degrees) / len(in_degrees) if in_degrees else 0,
            "out_degree_avg": sum(out_degrees) / len(out_degrees) if out_degrees else 0,
            "in_degree_max": max(in_degrees) if in_degrees else 0,
            "out_degree_max": max(out_degrees) if out_degrees else 0
        }
        
        return metrics
    
    def _classify_module_layer(self, module_path: str) -> str:
        """Classify a module into an architecture layer."""
        module_path_lower = module_path.lower()
        
        for layer, keywords in self.architecture_layers.items():
            if any(keyword in module_path_lower for keyword in keywords):
                return layer
        
        return "unknown"
    
    def _get_module_name(self, module_path: str) -> str:
        """Get a readable module name from path."""
        from pathlib import Path
        return Path(module_path).stem
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        from pathlib import Path
        
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go"
        }
        
        return lang_map.get(ext, "unknown")
    
    def _calculate_dependency_score(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> float:
        """Calculate overall dependency quality score."""
        base_score = 100.0
        
        # Penalty for issues
        severity_weights = {
            Severity.CRITICAL: 20,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3
        }
        
        penalty = 0
        for issue in issues:
            penalty += severity_weights.get(issue["severity"], 1)
        
        # Additional penalty for high coupling
        avg_coupling = metrics.get("average_coupling", 0)
        if avg_coupling > self.coupling_thresholds["medium"]:
            penalty += (avg_coupling - self.coupling_thresholds["medium"]) * 2
        
        # Penalty for circular dependencies
        circular_count = len([i for i in issues if i["rule_id"] == "DEP_CIRCULAR"])
        penalty += circular_count * 25
        
        score = base_score - penalty
        return max(0, min(100, score))
    
    def _generate_dependency_recommendations(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable dependency recommendations."""
        recommendations = []
        
        # Count issue types
        issue_counts = defaultdict(int)
        for issue in issues:
            issue_counts[issue["rule_id"]] += 1
        
        # Circular dependency recommendations
        if issue_counts.get("DEP_CIRCULAR", 0) > 0:
            recommendations.append(f"Break {issue_counts['DEP_CIRCULAR']} circular dependencies using dependency inversion")
        
        # Coupling recommendations
        if issue_counts.get("DEP_COUPLING", 0) > 0:
            recommendations.append(f"Reduce coupling in {issue_counts['DEP_COUPLING']} highly coupled modules")
        
        # Architecture recommendations
        if issue_counts.get("DEP_ARCH_VIOLATION", 0) > 0:
            recommendations.append(f"Fix {issue_counts['DEP_ARCH_VIOLATION']} architecture layer violations")
        
        # External dependency recommendations
        if issue_counts.get("DEP_PROBLEMATIC", 0) > 0:
            recommendations.append(f"Review {issue_counts['DEP_PROBLEMATIC']} problematic external dependencies")
        
        # General recommendations based on metrics
        avg_coupling = metrics.get("average_coupling", 0)
        if avg_coupling > self.coupling_thresholds["medium"]:
            recommendations.append(f"Reduce average coupling from {avg_coupling:.1f} to below {self.coupling_thresholds['medium']}")
        
        external_count = metrics.get("external_count", 0)
        if external_count > 20:
            recommendations.append(f"Consider reducing {external_count} external dependencies to improve maintainability")
        
        return recommendations[:5]  # Return top 5 recommendations

