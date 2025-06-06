"""
Import Analysis Module

Analyzes import relationships, detects circular imports, and provides
insights into module dependencies and coupling.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.external_module import ExternalModule
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    SourceFile = Any
    Import = Any


def analyze_import_relationships(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze import relationships across the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with import relationship analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis = {
            "total_imports": 0,
            "internal_imports": 0,
            "external_imports": 0,
            "import_graph": {},
            "most_imported_modules": [],
            "files_with_most_imports": [],
            "import_patterns": {}
        }
        
        import_counts = defaultdict(int)
        file_import_counts = defaultdict(int)
        import_graph = defaultdict(set)
        
        # Analyze each import
        for import_stmt in codebase.imports:
            analysis["total_imports"] += 1
            
            # Get source file
            source_file = import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown"
            file_import_counts[source_file] += 1
            
            # Get imported module/symbol
            if hasattr(import_stmt, 'module'):
                module_name = import_stmt.module
                import_counts[module_name] += 1
                
                # Build import graph
                import_graph[source_file].add(module_name)
                
                # Classify as internal or external
                if hasattr(import_stmt, 'imported_symbol'):
                    if isinstance(import_stmt.imported_symbol, ExternalModule):
                        analysis["external_imports"] += 1
                    else:
                        analysis["internal_imports"] += 1
        
        # Convert sets to lists for JSON serialization
        analysis["import_graph"] = {k: list(v) for k, v in import_graph.items()}
        
        # Most imported modules
        analysis["most_imported_modules"] = [
            {"module": module, "import_count": count}
            for module, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Files with most imports
        analysis["files_with_most_imports"] = [
            {"file": file, "import_count": count}
            for file, count in sorted(file_import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Import patterns
        analysis["import_patterns"] = analyze_import_patterns(codebase)
        
        return analysis
        
    except Exception as e:
        return {"error": f"Error analyzing import relationships: {str(e)}"}


def detect_circular_imports(codebase: Codebase) -> Dict[str, Any]:
    """
    Detect circular import dependencies in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with circular import analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        circular_imports = {
            "cycles_found": [],
            "total_cycles": 0,
            "affected_files": set(),
            "cycle_lengths": []
        }
        
        # Build import graph
        import_graph = defaultdict(set)
        
        for import_stmt in codebase.imports:
            source_file = import_stmt.file.filepath if hasattr(import_stmt, 'file') else None
            
            if hasattr(import_stmt, 'imported_symbol') and hasattr(import_stmt.imported_symbol, 'file'):
                target_file = import_stmt.imported_symbol.file.filepath
                
                if source_file and target_file and source_file != target_file:
                    import_graph[source_file].add(target_file)
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs_find_cycles(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in import_graph.get(node, []):
                dfs_find_cycles(neighbor, path[:])
            
            rec_stack.remove(node)
            path.pop()
        
        # Run DFS from each unvisited node
        for node in import_graph:
            if node not in visited:
                dfs_find_cycles(node, [])
        
        # Process found cycles
        unique_cycles = []
        for cycle in cycles:
            # Normalize cycle (start from lexicographically smallest)
            min_idx = cycle.index(min(cycle[:-1]))  # Exclude last element (duplicate)
            normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
            
            if normalized not in unique_cycles:
                unique_cycles.append(normalized)
        
        circular_imports["cycles_found"] = unique_cycles
        circular_imports["total_cycles"] = len(unique_cycles)
        
        # Collect affected files and cycle lengths
        for cycle in unique_cycles:
            circular_imports["cycle_lengths"].append(len(cycle) - 1)  # Subtract 1 for duplicate
            circular_imports["affected_files"].update(cycle[:-1])  # Exclude duplicate
        
        circular_imports["affected_files"] = list(circular_imports["affected_files"])
        
        return circular_imports
        
    except Exception as e:
        return {"error": f"Error detecting circular imports: {str(e)}"}


def get_import_graph(codebase: Codebase) -> Dict[str, Any]:
    """
    Generate a comprehensive import dependency graph.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with import graph data
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        graph = {
            "nodes": [],
            "edges": [],
            "statistics": {
                "total_nodes": 0,
                "total_edges": 0,
                "max_in_degree": 0,
                "max_out_degree": 0,
                "isolated_nodes": []
            }
        }
        
        # Collect all files and modules
        nodes = set()
        edges = []
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for import_stmt in codebase.imports:
            source = import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown"
            
            if hasattr(import_stmt, 'module'):
                target = import_stmt.module
            elif hasattr(import_stmt, 'imported_symbol') and hasattr(import_stmt.imported_symbol, 'file'):
                target = import_stmt.imported_symbol.file.filepath
            else:
                target = "unknown"
            
            nodes.add(source)
            nodes.add(target)
            
            edge = {"source": source, "target": target}
            if edge not in edges:
                edges.append(edge)
                out_degree[source] += 1
                in_degree[target] += 1
        
        # Convert to lists
        graph["nodes"] = [{"id": node, "type": "file" if "/" in node else "module"} for node in nodes]
        graph["edges"] = edges
        
        # Calculate statistics
        graph["statistics"]["total_nodes"] = len(nodes)
        graph["statistics"]["total_edges"] = len(edges)
        graph["statistics"]["max_in_degree"] = max(in_degree.values()) if in_degree else 0
        graph["statistics"]["max_out_degree"] = max(out_degree.values()) if out_degree else 0
        
        # Find isolated nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])
        
        graph["statistics"]["isolated_nodes"] = list(nodes - connected_nodes)
        
        return graph
        
    except Exception as e:
        return {"error": f"Error generating import graph: {str(e)}"}


def analyze_import_patterns(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze common import patterns in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with import pattern analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        patterns = {
            "import_types": defaultdict(int),
            "common_modules": defaultdict(int),
            "import_styles": defaultdict(int),
            "relative_vs_absolute": {"relative": 0, "absolute": 0},
            "star_imports": []
        }
        
        for import_stmt in codebase.imports:
            # Analyze import type
            import_type = type(import_stmt).__name__
            patterns["import_types"][import_type] += 1
            
            # Analyze module patterns
            if hasattr(import_stmt, 'module'):
                module = import_stmt.module
                patterns["common_modules"][module] += 1
                
                # Check if relative or absolute
                if module.startswith('.'):
                    patterns["relative_vs_absolute"]["relative"] += 1
                else:
                    patterns["relative_vs_absolute"]["absolute"] += 1
            
            # Check for star imports (from module import *)
            if hasattr(import_stmt, 'imported_symbol'):
                symbol_name = getattr(import_stmt.imported_symbol, 'name', '')
                if symbol_name == '*':
                    patterns["star_imports"].append({
                        "module": getattr(import_stmt, 'module', 'unknown'),
                        "file": import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown"
                    })
        
        # Convert defaultdicts to regular dicts for JSON serialization
        patterns["import_types"] = dict(patterns["import_types"])
        patterns["common_modules"] = dict(patterns["common_modules"])
        patterns["import_styles"] = dict(patterns["import_styles"])
        
        return patterns
        
    except Exception as e:
        return {"error": f"Error analyzing import patterns: {str(e)}"}


def get_file_import_details(file: SourceFile) -> Dict[str, Any]:
    """
    Get detailed import information for a specific file.
    
    Args:
        file: The source file to analyze
        
    Returns:
        Dictionary with file import details
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        details = {
            "file_path": file.filepath,
            "inbound_imports": [],
            "outbound_imports": [],
            "import_summary": {
                "total_inbound": 0,
                "total_outbound": 0,
                "external_dependencies": 0,
                "internal_dependencies": 0
            }
        }
        
        # Analyze outbound imports (what this file imports)
        for import_stmt in file.imports:
            import_info = {
                "module": getattr(import_stmt, 'module', 'unknown'),
                "symbol": import_stmt.imported_symbol.name if hasattr(import_stmt.imported_symbol, 'name') else 'unknown',
                "type": type(import_stmt).__name__,
                "is_external": isinstance(import_stmt.imported_symbol, ExternalModule) if hasattr(import_stmt, 'imported_symbol') else False
            }
            details["outbound_imports"].append(import_info)
            
            if import_info["is_external"]:
                details["import_summary"]["external_dependencies"] += 1
            else:
                details["import_summary"]["internal_dependencies"] += 1
        
        # Analyze inbound imports (what imports this file)
        if hasattr(file, 'inbound_imports'):
            for import_stmt in file.inbound_imports:
                import_info = {
                    "importing_file": import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown",
                    "imported_symbol": import_stmt.imported_symbol.name if hasattr(import_stmt.imported_symbol, 'name') else 'unknown',
                    "type": type(import_stmt).__name__
                }
                details["inbound_imports"].append(import_info)
        
        details["import_summary"]["total_outbound"] = len(details["outbound_imports"])
        details["import_summary"]["total_inbound"] = len(details["inbound_imports"])
        
        return details
        
    except Exception as e:
        return {"error": f"Error getting file import details: {str(e)}"}


def generate_import_report(codebase: Codebase) -> str:
    """
    Generate a formatted report of import analysis.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string report
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "❌ Graph-sitter not available for import analysis"
    
    try:
        import_analysis = analyze_import_relationships(codebase)
        circular_analysis = detect_circular_imports(codebase)
        
        report = []
        report.append("📦 Import Analysis Report")
        report.append("=" * 50)
        
        if "error" not in import_analysis:
            report.append(f"📊 Total Imports: {import_analysis['total_imports']}")
            report.append(f"🏠 Internal Imports: {import_analysis['internal_imports']}")
            report.append(f"🌐 External Imports: {import_analysis['external_imports']}")
            report.append("")
            
            # Most imported modules
            if import_analysis["most_imported_modules"]:
                report.append("🔥 Most Imported Modules:")
                report.append("-" * 30)
                for item in import_analysis["most_imported_modules"][:5]:
                    report.append(f"  • {item['module']} ({item['import_count']} imports)")
                report.append("")
            
            # Files with most imports
            if import_analysis["files_with_most_imports"]:
                report.append("📁 Files with Most Imports:")
                report.append("-" * 30)
                for item in import_analysis["files_with_most_imports"][:5]:
                    report.append(f"  • {item['file']} ({item['import_count']} imports)")
                report.append("")
        
        # Circular imports
        if "error" not in circular_analysis:
            if circular_analysis["total_cycles"] > 0:
                report.append("⚠️ Circular Import Issues:")
                report.append("-" * 30)
                report.append(f"🔄 Total Cycles Found: {circular_analysis['total_cycles']}")
                report.append(f"📁 Affected Files: {len(circular_analysis['affected_files'])}")
                
                for i, cycle in enumerate(circular_analysis["cycles_found"][:3]):  # Show first 3 cycles
                    report.append(f"\n  Cycle {i+1}: {' → '.join(cycle)}")
                
                if circular_analysis["total_cycles"] > 3:
                    report.append(f"\n  ... and {circular_analysis['total_cycles'] - 3} more cycles")
            else:
                report.append("✅ No circular imports found!")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Error generating import report: {str(e)}"

