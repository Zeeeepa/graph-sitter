"""Advanced call graph analysis following graph-sitter.com patterns."""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.function_call import FunctionCall

logger = logging.getLogger(__name__)


@dataclass
class CallGraphNode:
    """Node in the call graph."""
    function: Function
    incoming_calls: List['CallGraphEdge']
    outgoing_calls: List['CallGraphEdge']
    depth: int = 0
    strongly_connected_component: Optional[int] = None


@dataclass
class CallGraphEdge:
    """Edge in the call graph representing a function call."""
    caller: Function
    callee: Function
    call_site: FunctionCall
    call_count: int = 1


@dataclass
class CallPath:
    """Path between two functions in the call graph."""
    start_function: Function
    end_function: Function
    path: List[Function]
    total_calls: int
    max_depth: int


class CallGraphAnalyzer:
    """Advanced call graph analysis and traversal."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.nodes: Dict[str, CallGraphNode] = {}
        self.edges: List[CallGraphEdge] = []
        self._build_call_graph()
    
    def _build_call_graph(self):
        """Build the complete call graph."""
        try:
            # Create nodes for all functions
            for function in self.codebase.functions:
                self.nodes[function.name] = CallGraphNode(
                    function=function,
                    incoming_calls=[],
                    outgoing_calls=[]
                )
            
            # Create edges for all function calls
            for function in self.codebase.functions:
                function_calls = getattr(function, 'function_calls', [])
                
                for call in function_calls:
                    callee_name = getattr(call, 'name', '')
                    if callee_name in self.nodes:
                        edge = CallGraphEdge(
                            caller=function,
                            callee=self.nodes[callee_name].function,
                            call_site=call
                        )
                        
                        self.edges.append(edge)
                        self.nodes[function.name].outgoing_calls.append(edge)
                        self.nodes[callee_name].incoming_calls.append(edge)
            
            # Calculate depths and strongly connected components
            self._calculate_depths()
            self._find_strongly_connected_components()
            
        except Exception as e:
            logger.error(f"Error building call graph: {e}")
    
    def _calculate_depths(self):
        """Calculate call depth for each function."""
        try:
            # Find root functions (no incoming calls)
            roots = [node for node in self.nodes.values() if not node.incoming_calls]
            
            # BFS to calculate depths
            queue = deque([(node, 0) for node in roots])
            visited = set()
            
            while queue:
                node, depth = queue.popleft()
                
                if node.function.name in visited:
                    continue
                
                visited.add(node.function.name)
                node.depth = depth
                
                # Add children to queue
                for edge in node.outgoing_calls:
                    callee_node = self.nodes[edge.callee.name]
                    if edge.callee.name not in visited:
                        queue.append((callee_node, depth + 1))
        except Exception as e:
            logger.warning(f"Error calculating depths: {e}")
    
    def _find_strongly_connected_components(self):
        """Find strongly connected components using Tarjan's algorithm."""
        try:
            index_counter = [0]
            stack = []
            lowlinks = {}
            index = {}
            on_stack = {}
            components = []
            
            def strongconnect(node_name):
                index[node_name] = index_counter[0]
                lowlinks[node_name] = index_counter[0]
                index_counter[0] += 1
                stack.append(node_name)
                on_stack[node_name] = True
                
                # Consider successors
                node = self.nodes[node_name]
                for edge in node.outgoing_calls:
                    successor = edge.callee.name
                    if successor not in index:
                        strongconnect(successor)
                        lowlinks[node_name] = min(lowlinks[node_name], lowlinks[successor])
                    elif on_stack.get(successor, False):
                        lowlinks[node_name] = min(lowlinks[node_name], index[successor])
                
                # If node is a root node, pop the stack and create component
                if lowlinks[node_name] == index[node_name]:
                    component = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        component.append(w)
                        if w == node_name:
                            break
                    components.append(component)
            
            # Run algorithm on all nodes
            for node_name in self.nodes:
                if node_name not in index:
                    strongconnect(node_name)
            
            # Assign component IDs
            for i, component in enumerate(components):
                for node_name in component:
                    self.nodes[node_name].strongly_connected_component = i
                    
        except Exception as e:
            logger.warning(f"Error finding strongly connected components: {e}")
    
    def find_most_called_function(self) -> Optional[Function]:
        """Find function with most call sites."""
        try:
            max_calls = 0
            most_called = None
            
            for node in self.nodes.values():
                call_count = len(node.incoming_calls)
                if call_count > max_calls:
                    max_calls = call_count
                    most_called = node.function
            
            return most_called
        except Exception as e:
            logger.error(f"Error finding most called function: {e}")
            return None
    
    def find_most_calling_function(self) -> Optional[Function]:
        """Find function making most calls."""
        try:
            max_calls = 0
            most_calling = None
            
            for node in self.nodes.values():
                call_count = len(node.outgoing_calls)
                if call_count > max_calls:
                    max_calls = call_count
                    most_calling = node.function
            
            return most_calling
        except Exception as e:
            logger.error(f"Error finding most calling function: {e}")
            return None
    
    def find_unused_functions(self) -> List[Function]:
        """Find functions with no call sites."""
        try:
            unused = []
            for node in self.nodes.values():
                if not node.incoming_calls:
                    # Check if it's a potential entry point
                    if not self._is_entry_point(node.function):
                        unused.append(node.function)
            return unused
        except Exception as e:
            logger.error(f"Error finding unused functions: {e}")
            return []
    
    def find_recursive_functions(self) -> List[Function]:
        """Find recursive functions."""
        try:
            recursive = []
            for node in self.nodes.values():
                # Check direct recursion
                for edge in node.outgoing_calls:
                    if edge.callee.name == node.function.name:
                        recursive.append(node.function)
                        break
                else:
                    # Check indirect recursion (same SCC with size > 1)
                    scc_id = node.strongly_connected_component
                    if scc_id is not None:
                        scc_size = sum(
                            1 for n in self.nodes.values()
                            if n.strongly_connected_component == scc_id
                        )
                        if scc_size > 1:
                            recursive.append(node.function)
            
            return recursive
        except Exception as e:
            logger.error(f"Error finding recursive functions: {e}")
            return []
    
    def analyze_call_patterns(self) -> Dict[str, Any]:
        """Analyze function usage patterns."""
        try:
            patterns = {
                'total_functions': len(self.nodes),
                'total_calls': len(self.edges),
                'average_calls_per_function': len(self.edges) / len(self.nodes) if self.nodes else 0,
                'max_call_depth': max((node.depth for node in self.nodes.values()), default=0),
                'strongly_connected_components': len(set(
                    node.strongly_connected_component for node in self.nodes.values()
                    if node.strongly_connected_component is not None
                )),
                'entry_points': len([
                    node for node in self.nodes.values()
                    if not node.incoming_calls and self._is_entry_point(node.function)
                ]),
                'leaf_functions': len([
                    node for node in self.nodes.values()
                    if not node.outgoing_calls
                ]),
                'hub_functions': len([
                    node for node in self.nodes.values()
                    if len(node.incoming_calls) > 5 and len(node.outgoing_calls) > 5
                ])
            }
            
            # Call distribution
            call_counts = [len(node.incoming_calls) for node in self.nodes.values()]
            if call_counts:
                patterns['call_distribution'] = {
                    'min': min(call_counts),
                    'max': max(call_counts),
                    'median': sorted(call_counts)[len(call_counts) // 2],
                    'functions_with_no_calls': sum(1 for c in call_counts if c == 0),
                    'functions_with_many_calls': sum(1 for c in call_counts if c > 10)
                }
            
            return patterns
        except Exception as e:
            logger.error(f"Error analyzing call patterns: {e}")
            return {}
    
    def create_call_graph(self, start_func: str, end_func: str) -> Dict[str, Any]:
        """Build targeted call graph between two functions."""
        try:
            if start_func not in self.nodes or end_func not in self.nodes:
                return {'error': 'Function not found'}
            
            # Find all paths between start and end
            paths = self.find_call_paths(start_func, end_func)
            
            # Extract relevant nodes and edges
            relevant_nodes = set()
            relevant_edges = []
            
            for path in paths:
                for func in path.path:
                    relevant_nodes.add(func.name)
                
                # Add edges along the path
                for i in range(len(path.path) - 1):
                    current = path.path[i]
                    next_func = path.path[i + 1]
                    
                    # Find the edge
                    for edge in self.nodes[current.name].outgoing_calls:
                        if edge.callee.name == next_func.name:
                            relevant_edges.append(edge)
                            break
            
            return {
                'nodes': list(relevant_nodes),
                'edges': [
                    {
                        'caller': edge.caller.name,
                        'callee': edge.callee.name,
                        'call_count': edge.call_count
                    }
                    for edge in relevant_edges
                ],
                'paths': [
                    {
                        'functions': [f.name for f in path.path],
                        'total_calls': path.total_calls,
                        'max_depth': path.max_depth
                    }
                    for path in paths
                ]
            }
        except Exception as e:
            logger.error(f"Error creating call graph: {e}")
            return {'error': str(e)}
    
    def find_call_paths(self, start: str, end: str, max_depth: int = 10) -> List[CallPath]:
        """Find paths between two functions."""
        try:
            if start not in self.nodes or end not in self.nodes:
                return []
            
            paths = []
            visited = set()
            
            def dfs(current: str, target: str, path: List[Function], depth: int):
                if depth > max_depth:
                    return
                
                if current == target:
                    paths.append(CallPath(
                        start_function=self.nodes[start].function,
                        end_function=self.nodes[end].function,
                        path=path.copy(),
                        total_calls=len(path) - 1,
                        max_depth=depth
                    ))
                    return
                
                if current in visited:
                    return
                
                visited.add(current)
                
                for edge in self.nodes[current].outgoing_calls:
                    callee_name = edge.callee.name
                    path.append(edge.callee)
                    dfs(callee_name, target, path, depth + 1)
                    path.pop()
                
                visited.remove(current)
            
            dfs(start, end, [self.nodes[start].function], 0)
            return paths
            
        except Exception as e:
            logger.error(f"Error finding call paths: {e}")
            return []
    
    def get_function_call_depth(self, function_name: str) -> int:
        """Calculate call depth for a function."""
        try:
            if function_name in self.nodes:
                return self.nodes[function_name].depth
            return 0
        except Exception as e:
            logger.error(f"Error getting call depth: {e}")
            return 0
    
    def analyze_call_chains(self) -> Dict[str, Any]:
        """Analyze method chaining patterns."""
        try:
            chains = []
            
            for function in self.codebase.functions:
                function_calls = getattr(function, 'function_calls', [])
                
                # Look for chained calls (calls with predecessors)
                for call in function_calls:
                    predecessor = getattr(call, 'predecessor', None)
                    if predecessor:
                        # Build the chain
                        chain = [call]
                        current = predecessor
                        
                        while current and len(chain) < 10:  # Prevent infinite loops
                            chain.insert(0, current)
                            current = getattr(current, 'predecessor', None)
                        
                        if len(chain) > 2:  # Only consider chains of 3+ calls
                            chains.append({
                                'function': function.name,
                                'chain_length': len(chain),
                                'calls': [getattr(c, 'name', str(c)) for c in chain]
                            })
            
            return {
                'total_chains': len(chains),
                'average_chain_length': sum(c['chain_length'] for c in chains) / len(chains) if chains else 0,
                'longest_chain': max(chains, key=lambda x: x['chain_length']) if chains else None,
                'chains': chains[:10]  # Return top 10 chains
            }
        except Exception as e:
            logger.error(f"Error analyzing call chains: {e}")
            return {}
    
    def visualize_call_graph(self, output_format: str = 'dict') -> Dict[str, Any]:
        """Create call graph visualization data."""
        try:
            # Prepare nodes for visualization
            vis_nodes = []
            for node in self.nodes.values():
                vis_nodes.append({
                    'id': node.function.name,
                    'label': node.function.name,
                    'incoming_calls': len(node.incoming_calls),
                    'outgoing_calls': len(node.outgoing_calls),
                    'depth': node.depth,
                    'scc': node.strongly_connected_component,
                    'size': len(node.incoming_calls) + len(node.outgoing_calls),
                    'type': self._classify_function_type(node)
                })
            
            # Prepare edges for visualization
            vis_edges = []
            for edge in self.edges:
                vis_edges.append({
                    'source': edge.caller.name,
                    'target': edge.callee.name,
                    'weight': edge.call_count,
                    'type': 'call'
                })
            
            return {
                'nodes': vis_nodes,
                'edges': vis_edges,
                'metadata': {
                    'total_nodes': len(vis_nodes),
                    'total_edges': len(vis_edges),
                    'max_depth': max((node['depth'] for node in vis_nodes), default=0),
                    'strongly_connected_components': len(set(
                        node['scc'] for node in vis_nodes if node['scc'] is not None
                    ))
                }
            }
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return {'nodes': [], 'edges': [], 'metadata': {}}
    
    def find_strongly_connected_components(self) -> List[List[str]]:
        """Find strongly connected components in the call graph."""
        try:
            components = defaultdict(list)
            for node in self.nodes.values():
                if node.strongly_connected_component is not None:
                    components[node.strongly_connected_component].append(node.function.name)
            
            # Return only components with more than one function
            return [comp for comp in components.values() if len(comp) > 1]
        except Exception as e:
            logger.error(f"Error finding SCCs: {e}")
            return []
    
    def _is_entry_point(self, function: Function) -> bool:
        """Check if function is a potential entry point."""
        try:
            # Common entry point patterns
            entry_patterns = [
                'main', '__main__', 'run', 'start', 'execute',
                'test_', 'setup', 'teardown', '__init__'
            ]
            
            func_name = function.name.lower()
            return any(pattern in func_name for pattern in entry_patterns)
        except Exception:
            return False
    
    def _classify_function_type(self, node: CallGraphNode) -> str:
        """Classify function type based on call patterns."""
        try:
            incoming = len(node.incoming_calls)
            outgoing = len(node.outgoing_calls)
            
            if incoming == 0 and outgoing > 0:
                return 'entry_point'
            elif incoming > 0 and outgoing == 0:
                return 'leaf'
            elif incoming > 5 and outgoing > 5:
                return 'hub'
            elif incoming > outgoing * 2:
                return 'utility'
            elif outgoing > incoming * 2:
                return 'orchestrator'
            else:
                return 'regular'
        except Exception:
            return 'unknown'


# Convenience functions
def build_call_graph(codebase: Codebase) -> CallGraphAnalyzer:
    """Create call graph representation."""
    return CallGraphAnalyzer(codebase)


def traverse_call_graph(codebase: Codebase, start_function: str) -> Dict[str, Any]:
    """Navigate call relationships from a starting function."""
    analyzer = CallGraphAnalyzer(codebase)
    
    if start_function not in analyzer.nodes:
        return {'error': 'Function not found'}
    
    # Traverse from the starting function
    visited = set()
    result = {'nodes': [], 'edges': []}
    
    def traverse(func_name: str, depth: int = 0, max_depth: int = 5):
        if depth > max_depth or func_name in visited:
            return
        
        visited.add(func_name)
        node = analyzer.nodes[func_name]
        
        result['nodes'].append({
            'name': func_name,
            'depth': depth,
            'incoming_calls': len(node.incoming_calls),
            'outgoing_calls': len(node.outgoing_calls)
        })
        
        # Add outgoing calls
        for edge in node.outgoing_calls:
            result['edges'].append({
                'caller': edge.caller.name,
                'callee': edge.callee.name,
                'depth': depth
            })
            traverse(edge.callee.name, depth + 1, max_depth)
    
    traverse(start_function)
    return result

