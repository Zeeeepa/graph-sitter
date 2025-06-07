"""
AI-Powered Analysis Module

Provides AI-enhanced code analysis capabilities including automated issue detection,
context gathering, and intelligent code improvement suggestions.
Based on features from README4.md.
"""

from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.file import SourceFile
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    # Create dummy classes for type hints
    class Codebase: pass
    class Function: pass
    class Class: pass
    class Symbol: pass
    class Import: pass
    class ExternalModule: pass
    class SourceFile: pass
    GRAPH_SITTER_AVAILABLE = False


def analyze_codebase(codebase: Codebase) -> Dict[str, Any]:
    """
    Perform automated codebase analysis to identify potential issues.
    Based on the analyze_codebase function from README4.md.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with analysis results and flagged issues
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis_results = {
            "flagged_functions": [],
            "flagged_classes": [],
            "code_quality_issues": [],
            "documentation_issues": [],
            "error_handling_issues": [],
            "performance_issues": [],
            "total_issues": 0
        }
        
        # Analyze functions
        for function in codebase.functions:
            issues = analyze_function_issues(function)
            if issues:
                analysis_results["flagged_functions"].append({
                    "function": function.name,
                    "file": function.file.filepath if hasattr(function, 'file') else "unknown",
                    "issues": issues
                })
        
        # Analyze classes
        for cls in codebase.classes:
            issues = analyze_class_issues(cls)
            if issues:
                analysis_results["flagged_classes"].append({
                    "class": cls.name,
                    "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "issues": issues
                })
        
        # Categorize issues
        for func_result in analysis_results["flagged_functions"]:
            for issue in func_result["issues"]:
                categorize_issue(issue, analysis_results)
        
        for class_result in analysis_results["flagged_classes"]:
            for issue in class_result["issues"]:
                categorize_issue(issue, analysis_results)
        
        # Calculate total issues
        analysis_results["total_issues"] = (
            len(analysis_results["code_quality_issues"]) +
            len(analysis_results["documentation_issues"]) +
            len(analysis_results["error_handling_issues"]) +
            len(analysis_results["performance_issues"])
        )
        
        return analysis_results
        
    except Exception as e:
        return {"error": f"Error analyzing codebase: {str(e)}"}


def analyze_function_issues(function: Function) -> List[Dict[str, Any]]:
    """
    Analyze a function for potential issues.
    
    Args:
        function: The function to analyze
        
    Returns:
        List of issues found
    """
    issues = []
    
    try:
        # Check documentation
        if not hasattr(function, 'docstring') or not function.docstring:
            issues.append({
                "type": "documentation",
                "severity": "medium",
                "message": "Missing docstring",
                "suggestion": "Add a docstring describing the function's purpose, parameters, and return value"
            })
        
        # Check error handling for async functions
        if hasattr(function, 'is_async') and function.is_async:
            if not has_try_catch(function):
                issues.append({
                    "type": "error_handling",
                    "severity": "high",
                    "message": "Async function missing error handling",
                    "suggestion": "Add try-catch blocks to handle potential async errors"
                })
        
        # Check function complexity
        if hasattr(function, 'parameters') and len(function.parameters) > 7:
            issues.append({
                "type": "code_quality",
                "severity": "medium",
                "message": f"Function has too many parameters ({len(function.parameters)})",
                "suggestion": "Consider using a configuration object or breaking the function into smaller parts"
            })
        
        # Check function length
        if hasattr(function, 'source'):
            line_count = len(function.source.split('\\n'))
            if line_count > 50:
                issues.append({
                    "type": "code_quality",
                    "severity": "medium",
                    "message": f"Function is too long ({line_count} lines)",
                    "suggestion": "Consider breaking this function into smaller, more focused functions"
                })
        
        # Check for potential performance issues
        if hasattr(function, 'function_calls'):
            # Look for nested loops or recursive calls
            if any(call.name == function.name for call in function.function_calls):
                if not has_base_case_check(function):
                    issues.append({
                        "type": "performance",
                        "severity": "high",
                        "message": "Recursive function may lack proper base case",
                        "suggestion": "Ensure recursive function has a clear base case to prevent infinite recursion"
                    })
        
        # Check return statement consistency
        if hasattr(function, 'return_statements'):
            if len(function.return_statements) > 5:
                issues.append({
                    "type": "code_quality",
                    "severity": "low",
                    "message": "Function has many return statements",
                    "suggestion": "Consider consolidating return logic for better readability"
                })
        
        return issues
        
    except Exception as e:
        return [{"type": "error", "message": f"Error analyzing function: {str(e)}"}]


def analyze_class_issues(cls: Class) -> List[Dict[str, Any]]:
    """
    Analyze a class for potential issues.
    
    Args:
        cls: The class to analyze
        
    Returns:
        List of issues found
    """
    issues = []
    
    try:
        # Check documentation
        if not hasattr(cls, 'docstring') or not cls.docstring:
            issues.append({
                "type": "documentation",
                "severity": "medium",
                "message": "Missing class docstring",
                "suggestion": "Add a docstring describing the class's purpose and usage"
            })
        
        # Check class size
        if hasattr(cls, 'methods') and len(cls.methods) > 20:
            issues.append({
                "type": "code_quality",
                "severity": "medium",
                "message": f"Class has too many methods ({len(cls.methods)})",
                "suggestion": "Consider breaking this class into smaller, more focused classes"
            })
        
        # Check for god object pattern
        if hasattr(cls, 'attributes') and len(cls.attributes) > 15:
            issues.append({
                "type": "code_quality",
                "severity": "high",
                "message": f"Class has too many attributes ({len(cls.attributes)})",
                "suggestion": "This may be a 'god object'. Consider decomposing into smaller classes"
            })
        
        # Check inheritance depth
        if hasattr(cls, 'superclasses') and len(cls.superclasses) > 4:
            issues.append({
                "type": "code_quality",
                "severity": "medium",
                "message": f"Deep inheritance chain ({len(cls.superclasses)} levels)",
                "suggestion": "Consider using composition instead of deep inheritance"
            })
        
        # Check for missing __init__ method
        if hasattr(cls, 'methods'):
            has_init = any(method.name == '__init__' for method in cls.methods)
            if not has_init and hasattr(cls, 'attributes') and cls.attributes:
                issues.append({
                    "type": "code_quality",
                    "severity": "low",
                    "message": "Class has attributes but no __init__ method",
                    "suggestion": "Consider adding an __init__ method to properly initialize attributes"
                })
        
        return issues
        
    except Exception as e:
        return [{"type": "error", "message": f"Error analyzing class: {str(e)}"}]


def has_try_catch(function: Function) -> bool:
    """Check if a function has try-catch blocks."""
    if not hasattr(function, 'source'):
        return False
    
    source = function.source.lower()
    return 'try:' in source and ('except' in source or 'finally' in source)


def has_base_case_check(function: Function) -> bool:
    """Check if a recursive function has a base case."""
    if not hasattr(function, 'source'):
        return False
    
    source = function.source.lower()
    # Simple heuristic: look for return statements with conditions
    return 'if' in source and 'return' in source


def categorize_issue(issue: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
    """Categorize an issue into the appropriate category."""
    issue_type = issue.get("type", "unknown")
    
    if issue_type == "documentation":
        analysis_results["documentation_issues"].append(issue)
    elif issue_type == "error_handling":
        analysis_results["error_handling_issues"].append(issue)
    elif issue_type == "performance":
        analysis_results["performance_issues"].append(issue)
    elif issue_type == "code_quality":
        analysis_results["code_quality_issues"].append(issue)


def get_function_context(function: Function) -> Dict[str, Any]:
    """
    Get comprehensive context for a function including implementation, dependencies, and usages.
    Based on the get_function_context function from README4.md.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary with function context
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        context = {
            "implementation": {
                "source": getattr(function, 'source', ''),
                "filepath": function.file.filepath if hasattr(function, 'file') else "unknown"
            },
            "dependencies": [],
            "usages": [],
            "metadata": {
                "name": function.name,
                "parameter_count": 0,
                "return_type": getattr(function, 'return_type', 'unknown'),
                "is_async": getattr(function, 'is_async', False),
                "line_number": getattr(function, 'line_number', None)
            }
        }
        
        # Add parameter information
        if hasattr(function, 'parameters'):
            context["metadata"]["parameter_count"] = len(function.parameters)
            context["metadata"]["parameters"] = [
                {
                    "name": param.name,
                    "type": getattr(param, 'type', 'unknown'),
                    "default": getattr(param, 'default', None)
                }
                for param in function.parameters
            ]
        
        # Add dependencies
        if hasattr(function, 'dependencies'):
            for dep in function.dependencies:
                # Hop through imports to find the root symbol source
                if isinstance(dep, Import):
                    dep = hop_through_imports(dep)
                
                dep_info = {
                    "source": getattr(dep, 'source', ''),
                    "filepath": dep.file.filepath if hasattr(dep, 'file') else "unknown",
                    "name": getattr(dep, 'name', 'unknown'),
                    "type": type(dep).__name__
                }
                context["dependencies"].append(dep_info)
        
        # Add usages
        if hasattr(function, 'usages'):
            for usage in function.usages:
                if hasattr(usage, 'usage_symbol'):
                    usage_info = {
                        "source": getattr(usage.usage_symbol, 'source', ''),
                        "filepath": usage.usage_symbol.file.filepath if hasattr(usage.usage_symbol, 'file') else "unknown",
                        "name": getattr(usage.usage_symbol, 'name', 'unknown'),
                        "context": getattr(usage, 'context', '')
                    }
                    context["usages"].append(usage_info)
        
        return context
        
    except Exception as e:
        return {"error": f"Error getting function context: {str(e)}"}


def hop_through_imports(imp: Import) -> Union[Symbol, ExternalModule]:
    """
    Find the root symbol for an import by following the import chain.
    Based on the hop_through_imports function from README4.md.
    
    Args:
        imp: The import to resolve
        
    Returns:
        The root symbol or external module
    """
    try:
        if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, Import):
            return hop_through_imports(imp.imported_symbol)
        return imp.imported_symbol if hasattr(imp, 'imported_symbol') else imp
        
    except Exception:
        return imp


def flag_code_issues(codebase: Codebase, auto_fix: bool = False) -> Dict[str, Any]:
    """
    Flag code issues and optionally attempt automatic fixes.
    
    Args:
        codebase: The codebase to analyze
        auto_fix: Whether to attempt automatic fixes
        
    Returns:
        Dictionary with flagged issues and fix results
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        results = {
            "flagged_issues": [],
            "auto_fixes_applied": [],
            "manual_fixes_needed": [],
            "total_issues": 0
        }
        
        analysis = analyze_codebase(codebase)
        
        if "error" in analysis:
            return analysis
        
        # Process flagged functions
        for func_result in analysis["flagged_functions"]:
            for issue in func_result["issues"]:
                issue_info = {
                    "type": "function",
                    "name": func_result["function"],
                    "file": func_result["file"],
                    "issue": issue
                }
                results["flagged_issues"].append(issue_info)
                
                # Attempt auto-fix for simple issues
                if auto_fix and can_auto_fix(issue):
                    fix_result = attempt_auto_fix(codebase, issue_info)
                    if fix_result["success"]:
                        results["auto_fixes_applied"].append(fix_result)
                    else:
                        results["manual_fixes_needed"].append(issue_info)
                else:
                    results["manual_fixes_needed"].append(issue_info)
        
        # Process flagged classes
        for class_result in analysis["flagged_classes"]:
            for issue in class_result["issues"]:
                issue_info = {
                    "type": "class",
                    "name": class_result["class"],
                    "file": class_result["file"],
                    "issue": issue
                }
                results["flagged_issues"].append(issue_info)
                results["manual_fixes_needed"].append(issue_info)  # Class issues typically need manual fixes
        
        results["total_issues"] = len(results["flagged_issues"])
        
        return results
        
    except Exception as e:
        return {"error": f"Error flagging code issues: {str(e)}"}


def can_auto_fix(issue: Dict[str, Any]) -> bool:
    """Check if an issue can be automatically fixed."""
    auto_fixable_types = [
        "Missing docstring",
        "Function has many return statements"
    ]
    
    return issue.get("message", "") in auto_fixable_types


def attempt_auto_fix(codebase: Codebase, issue_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to automatically fix a code issue.
    
    Args:
        codebase: The codebase to modify
        issue_info: Information about the issue to fix
        
    Returns:
        Dictionary with fix results
    """
    try:
        fix_result = {
            "success": False,
            "issue": issue_info,
            "fix_applied": "",
            "error": None
        }
        
        issue = issue_info["issue"]
        
        if issue.get("message") == "Missing docstring":
            # Attempt to add a basic docstring
            if issue_info["type"] == "function":
                function = codebase.get_function(issue_info["name"])
                if function and hasattr(function, 'set_docstring'):
                    basic_docstring = f'"""{function.name} function.\\n\\nTODO: Add proper documentation."""'
                    function.set_docstring(basic_docstring)
                    fix_result["success"] = True
                    fix_result["fix_applied"] = f"Added basic docstring to {function.name}"
        
        return fix_result
        
    except Exception as e:
        return {
            "success": False,
            "issue": issue_info,
            "fix_applied": "",
            "error": str(e)
        }


def generate_ai_analysis_report(codebase: Codebase) -> str:
    """
    Generate a comprehensive AI analysis report.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string report
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "❌ Graph-sitter not available for AI analysis"
    
    try:
        analysis = analyze_codebase(codebase)
        
        if "error" in analysis:
            return f"❌ Error: {analysis['error']}"
        
        report = []
        report.append("🤖 AI-Powered Code Analysis Report")
        report.append("=" * 50)
        report.append(f"📊 Total Issues Found: {analysis['total_issues']}")
        report.append("")
        
        # Documentation issues
        if analysis["documentation_issues"]:
            report.append("📚 Documentation Issues:")
            report.append("-" * 30)
            for issue in analysis["documentation_issues"][:5]:
                report.append(f"  • {issue['message']} (Severity: {issue['severity']})")
            if len(analysis["documentation_issues"]) > 5:
                report.append(f"  ... and {len(analysis['documentation_issues']) - 5} more")
            report.append("")
        
        # Code quality issues
        if analysis["code_quality_issues"]:
            report.append("🔧 Code Quality Issues:")
            report.append("-" * 30)
            for issue in analysis["code_quality_issues"][:5]:
                report.append(f"  • {issue['message']} (Severity: {issue['severity']})")
            if len(analysis["code_quality_issues"]) > 5:
                report.append(f"  ... and {len(analysis['code_quality_issues']) - 5} more")
            report.append("")
        
        # Error handling issues
        if analysis["error_handling_issues"]:
            report.append("⚠️ Error Handling Issues:")
            report.append("-" * 30)
            for issue in analysis["error_handling_issues"][:5]:
                report.append(f"  • {issue['message']} (Severity: {issue['severity']})")
            if len(analysis["error_handling_issues"]) > 5:
                report.append(f"  ... and {len(analysis['error_handling_issues']) - 5} more")
            report.append("")
        
        # Performance issues
        if analysis["performance_issues"]:
            report.append("⚡ Performance Issues:")
            report.append("-" * 30)
            for issue in analysis["performance_issues"][:5]:
                report.append(f"  • {issue['message']} (Severity: {issue['severity']})")
            if len(analysis["performance_issues"]) > 5:
                report.append(f"  ... and {len(analysis['performance_issues']) - 5} more")
            report.append("")
        
        # Summary
        if analysis["total_issues"] == 0:
            report.append("✅ No issues found! Your code looks great.")
        else:
            high_severity = sum(1 for cat in [analysis["documentation_issues"], analysis["code_quality_issues"], 
                                            analysis["error_handling_issues"], analysis["performance_issues"]]
                              for issue in cat if issue.get("severity") == "high")
            
            if high_severity > 0:
                report.append(f"🚨 {high_severity} high-severity issues need immediate attention")
            else:
                report.append("👍 No high-severity issues found")
        
        return "\\n".join(report)
        
    except Exception as e:
        return f"❌ Error generating AI analysis report: {str(e)}"
