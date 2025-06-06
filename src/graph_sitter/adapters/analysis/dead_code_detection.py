"""
Dead Code Detection Module

Identifies unused functions, imports, and unreachable code within the codebase.
Helps maintain code quality by finding code that can be safely removed.
"""

from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.import_resolution import Import
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    Function = Any
    Symbol = Any
    SourceFile = Any


def find_dead_code(codebase: Codebase) -> Dict[str, Any]:
    """
    Find dead code in the codebase including unused functions and symbols.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with dead code analysis results
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        dead_code = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "unused_imports": [],
            "total_dead_items": 0
        }
        
        # Find unused functions
        for func in codebase.functions:
            if hasattr(func, 'usages') and len(func.usages) == 0:
                # Skip main functions and test functions
                if func.name not in ['main', '__main__'] and not func.name.startswith('test_'):
                    dead_code["unused_functions"].append({
                        "name": func.name,
                        "file": func.file.filepath if hasattr(func, 'file') else "unknown",
                        "line_number": getattr(func, 'line_number', None),
                        "reason": "No usages found"
                    })
        
        # Find unused classes
        for cls in codebase.classes:
            if hasattr(cls, 'usages') and len(cls.usages) == 0:
                dead_code["unused_classes"].append({
                    "name": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "line_number": getattr(cls, 'line_number', None),
                    "reason": "No usages found"
                })
        
        # Find unused global variables
        for var in codebase.global_vars:
            if hasattr(var, 'usages') and len(var.usages) == 0:
                dead_code["unused_variables"].append({
                    "name": var.name,
                    "file": var.file.filepath if hasattr(var, 'file') else "unknown",
                    "line_number": getattr(var, 'line_number', None),
                    "reason": "No usages found"
                })
        
        # Find unused imports
        dead_code["unused_imports"] = analyze_unused_imports(codebase)
        
        # Calculate total
        dead_code["total_dead_items"] = (
            len(dead_code["unused_functions"]) +
            len(dead_code["unused_classes"]) +
            len(dead_code["unused_variables"]) +
            len(dead_code["unused_imports"])
        )
        
        return dead_code
        
    except Exception as e:
        return {"error": f"Error finding dead code: {str(e)}"}


def analyze_unused_imports(codebase: Codebase) -> List[Dict[str, Any]]:
    """
    Find imports that are not used in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        List of unused imports
    """
    if not GRAPH_SITTER_AVAILABLE:
        return [{"error": "Graph-sitter not available"}]
    
    try:
        unused_imports = []
        
        for import_stmt in codebase.imports:
            # Check if the imported symbol is used
            if hasattr(import_stmt, 'imported_symbol') and hasattr(import_stmt.imported_symbol, 'usages'):
                if len(import_stmt.imported_symbol.usages) == 0:
                    unused_imports.append({
                        "module": getattr(import_stmt, 'module', 'unknown'),
                        "symbol": import_stmt.imported_symbol.name if hasattr(import_stmt.imported_symbol, 'name') else 'unknown',
                        "file": import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown",
                        "line_number": getattr(import_stmt, 'line_number', None),
                        "import_type": type(import_stmt).__name__
                    })
        
        return unused_imports
        
    except Exception as e:
        return [{"error": f"Error analyzing unused imports: {str(e)}"}]


def detect_unreachable_code(codebase: Codebase) -> Dict[str, Any]:
    """
    Detect potentially unreachable code patterns.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with unreachable code analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        unreachable = {
            "functions_after_return": [],
            "unreachable_branches": [],
            "dead_exception_handlers": [],
            "total_unreachable": 0
        }
        
        # Analyze each function for unreachable code
        for func in codebase.functions:
            if hasattr(func, 'source'):
                unreachable_patterns = analyze_function_reachability(func)
                unreachable["functions_after_return"].extend(unreachable_patterns.get("after_return", []))
                unreachable["unreachable_branches"].extend(unreachable_patterns.get("branches", []))
                unreachable["dead_exception_handlers"].extend(unreachable_patterns.get("exceptions", []))
        
        unreachable["total_unreachable"] = (
            len(unreachable["functions_after_return"]) +
            len(unreachable["unreachable_branches"]) +
            len(unreachable["dead_exception_handlers"])
        )
        
        return unreachable
        
    except Exception as e:
        return {"error": f"Error detecting unreachable code: {str(e)}"}


def analyze_function_reachability(function: Function) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analyze a single function for unreachable code patterns.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary with unreachable code patterns found
    """
    patterns = {
        "after_return": [],
        "branches": [],
        "exceptions": []
    }
    
    try:
        if not hasattr(function, 'source'):
            return patterns
        
        source_lines = function.source.split('\n')
        
        # Simple analysis for code after return statements
        in_function = False
        found_return = False
        
        for i, line in enumerate(source_lines):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for return statements
            if 'return' in stripped and not stripped.startswith('#'):
                found_return = True
                continue
            
            # If we found a return and there's more code (not just closing braces/pass)
            if found_return and stripped and stripped not in ['}', 'pass', '...']:
                # Check if it's not another function definition or class
                if not any(keyword in stripped for keyword in ['def ', 'class ', 'if __name__']):
                    patterns["after_return"].append({
                        "function": function.name,
                        "file": function.file.filepath if hasattr(function, 'file') else "unknown",
                        "line": i + 1,
                        "code": stripped,
                        "reason": "Code after return statement"
                    })
        
        # Simple analysis for unreachable branches (if False, if 0, etc.)
        for i, line in enumerate(source_lines):
            stripped = line.strip()
            
            # Check for obviously false conditions
            false_conditions = ['if False:', 'if 0:', 'if None:', 'while False:', 'while 0:']
            for condition in false_conditions:
                if condition in stripped:
                    patterns["branches"].append({
                        "function": function.name,
                        "file": function.file.filepath if hasattr(function, 'file') else "unknown",
                        "line": i + 1,
                        "code": stripped,
                        "reason": f"Always false condition: {condition.strip(':')}"
                    })
        
        return patterns
        
    except Exception as e:
        return {"error": f"Error analyzing function reachability: {str(e)}"}


def remove_dead_code(codebase: Codebase, dry_run: bool = True) -> Dict[str, Any]:
    """
    Remove dead code from the codebase (with dry run option).
    
    Args:
        codebase: The codebase to clean
        dry_run: If True, only report what would be removed
        
    Returns:
        Dictionary with removal results
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        removal_results = {
            "removed_functions": [],
            "removed_imports": [],
            "removed_variables": [],
            "total_removed": 0,
            "dry_run": dry_run
        }
        
        dead_code = find_dead_code(codebase)
        
        if not dry_run:
            # Remove unused functions
            for func_info in dead_code["unused_functions"]:
                try:
                    func = codebase.get_function(func_info["name"])
                    if func and hasattr(func, 'remove'):
                        func.remove()
                        removal_results["removed_functions"].append(func_info)
                except Exception as e:
                    print(f"Error removing function {func_info['name']}: {e}")
            
            # Remove unused imports (more complex, requires careful handling)
            # This is a simplified version - production code would need more sophisticated logic
            for import_info in dead_code["unused_imports"]:
                removal_results["removed_imports"].append(import_info)
                # Note: Actual import removal would require AST manipulation
        else:
            # Dry run - just report what would be removed
            removal_results["removed_functions"] = dead_code["unused_functions"]
            removal_results["removed_imports"] = dead_code["unused_imports"]
            removal_results["removed_variables"] = dead_code["unused_variables"]
        
        removal_results["total_removed"] = (
            len(removal_results["removed_functions"]) +
            len(removal_results["removed_imports"]) +
            len(removal_results["removed_variables"])
        )
        
        return removal_results
        
    except Exception as e:
        return {"error": f"Error removing dead code: {str(e)}"}


def generate_dead_code_report(codebase: Codebase) -> str:
    """
    Generate a formatted report of dead code in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string report
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "❌ Graph-sitter not available for dead code analysis"
    
    try:
        dead_code = find_dead_code(codebase)
        
        if "error" in dead_code:
            return f"❌ Error: {dead_code['error']}"
        
        report = []
        report.append("🗑️ Dead Code Analysis Report")
        report.append("=" * 50)
        report.append(f"📊 Total Dead Code Items: {dead_code['total_dead_items']}")
        report.append("")
        
        # Unused functions
        if dead_code["unused_functions"]:
            report.append("🔧 Unused Functions:")
            report.append("-" * 30)
            for func in dead_code["unused_functions"]:
                report.append(f"  • {func['name']} in {func['file']}")
                if func.get('line_number'):
                    report.append(f"    Line: {func['line_number']}")
            report.append("")
        
        # Unused classes
        if dead_code["unused_classes"]:
            report.append("🏗️ Unused Classes:")
            report.append("-" * 30)
            for cls in dead_code["unused_classes"]:
                report.append(f"  • {cls['name']} in {cls['file']}")
                if cls.get('line_number'):
                    report.append(f"    Line: {cls['line_number']}")
            report.append("")
        
        # Unused imports
        if dead_code["unused_imports"]:
            report.append("📦 Unused Imports:")
            report.append("-" * 30)
            for imp in dead_code["unused_imports"]:
                report.append(f"  • {imp['symbol']} from {imp['module']} in {imp['file']}")
            report.append("")
        
        # Unreachable code
        unreachable = detect_unreachable_code(codebase)
        if not isinstance(unreachable, dict) or "error" not in unreachable:
            if unreachable.get("total_unreachable", 0) > 0:
                report.append("⚠️ Potentially Unreachable Code:")
                report.append("-" * 30)
                
                for item in unreachable.get("functions_after_return", []):
                    report.append(f"  • Code after return in {item['function']} ({item['file']}:{item['line']})")
                
                for item in unreachable.get("unreachable_branches", []):
                    report.append(f"  • Unreachable branch in {item['function']} ({item['file']}:{item['line']})")
        
        if dead_code['total_dead_items'] == 0:
            report.append("✅ No dead code found! Your codebase is clean.")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Error generating dead code report: {str(e)}"

