#!/usr/bin/env python3
"""
Type Resolution Example for Safe Dead Code Analysis

Demonstrates how to use graph-sitter's type resolution features
for safer dependency analysis before removing dead code.
"""

from graph_sitter import Codebase
from typing import List, Dict, Set, Optional, Any

def analyze_with_type_resolution(codebase: Codebase, verbose: bool = True) -> Dict:
    """
    Demonstrate type resolution techniques for safer code analysis.
    
    Args:
        codebase: Graph-sitter Codebase object
        verbose: Whether to print detailed analysis
        
    Returns:
        Dict with type resolution analysis results
    """
    
    def log(message: str, emoji: str = "🔍"):
        if verbose:
            print(f"{emoji} {message}")
    
    results = {
        "functions_analyzed": 0,
        "type_resolutions": 0,
        "resolved_dependencies": [],
        "safe_to_remove": [],
        "keep_due_to_types": [],
        "resolution_errors": []
    }
    
    log("Starting type resolution analysis...", "🚀")
    
    for file in codebase.files:
        if not file.filepath.endswith('.py'):
            continue
            
        log(f"Analyzing file: {file.filepath}", "📄")
        
        for function in file.functions:
            results["functions_analyzed"] += 1
            
            try:
                log(f"  Function: {function.name}", "🔧")
                
                # ==================== RETURN TYPE RESOLUTION ====================
                if hasattr(function, 'return_type') and function.return_type:
                    log(f"    Analyzing return type...", "🎯")
                    
                    return_type = function.return_type
                    
                    # Method 1: Using resolved_types (returns Symbol objects)
                    if hasattr(return_type, 'resolved_types'):
                        try:
                            resolved_symbols = return_type.resolved_types
                            if resolved_symbols:
                                log(f"      Resolved symbols: {[str(s) for s in resolved_symbols]}", "✅")
                                results["resolved_dependencies"].extend([str(s) for s in resolved_symbols])
                                results["type_resolutions"] += 1
                        except Exception as e:
                            results["resolution_errors"].append(f"resolved_types failed for {function.name}: {e}")
                    
                    # Method 2: Using resolved_value (returns Expression/Symbol)
                    if hasattr(return_type, 'resolved_value'):
                        try:
                            resolved_types = return_type.resolved_value
                            if resolved_types:
                                log(f"      Resolved value: {resolved_types}", "✅")
                                results["resolved_dependencies"].append(str(resolved_types))
                                results["type_resolutions"] += 1
                        except Exception as e:
                            results["resolution_errors"].append(f"resolved_value failed for {function.name}: {e}")
                    
                    # Handle generic types with parameters
                    if hasattr(return_type, "parameters"):
                        log(f"      Analyzing generic parameters...", "🔗")
                        for param in return_type.parameters:
                            try:
                                # Method 1: resolved_types for parameters
                                if hasattr(param, 'resolved_types'):
                                    resolved_param = param.resolved_types
                                    if resolved_param:
                                        log(f"        Parameter symbols: {[str(s) for s in resolved_param]}", "✅")
                                        results["resolved_dependencies"].extend([str(s) for s in resolved_param])
                                
                                # Method 2: resolved_value for parameters
                                if hasattr(param, 'resolved_value'):
                                    param_types = param.resolved_value
                                    if param_types:
                                        log(f"        Parameter value: {param_types}", "✅")
                                        results["resolved_dependencies"].append(str(param_types))
                                        
                            except Exception as e:
                                results["resolution_errors"].append(f"Parameter resolution failed for {function.name}: {e}")
                    
                    # Handle union types
                    if hasattr(return_type, "options"):
                        log(f"      Analyzing union type options...", "🔀")
                        for option in return_type.options:
                            try:
                                if hasattr(option, 'resolved_value'):
                                    option_types = option.resolved_value
                                    if option_types:
                                        log(f"        Union option: {option_types}", "✅")
                                        results["resolved_dependencies"].append(str(option_types))
                            except Exception as e:
                                results["resolution_errors"].append(f"Union option resolution failed for {function.name}: {e}")
                
                # ==================== ASSIGNMENT TYPE RESOLUTION ====================
                if hasattr(function, 'code_block'):
                    for assignment in function.code_block.assignments:
                        try:
                            if hasattr(assignment, 'type') and assignment.type:
                                log(f"    Assignment {assignment.name} type analysis...", "📝")
                                
                                assignment_type = assignment.type
                                if hasattr(assignment_type, 'resolved_types'):
                                    resolved_type = assignment_type.resolved_types
                                    if resolved_type:
                                        log(f"      Assignment resolved: {[str(s) for s in resolved_type]}", "✅")
                                        results["resolved_dependencies"].extend([str(s) for s in resolved_type])
                                        results["type_resolutions"] += 1
                        except Exception as e:
                            results["resolution_errors"].append(f"Assignment type resolution failed for {assignment.name}: {e}")
                
                # ==================== DEAD CODE SAFETY ANALYSIS ====================
                # Use type resolution to determine if function is safe to remove
                has_external_dependencies = False
                has_complex_types = False
                
                # Check if function has resolved type dependencies
                if results["resolved_dependencies"]:
                    # Look for external or complex type dependencies
                    for dep in results["resolved_dependencies"]:
                        if any(keyword in dep.lower() for keyword in ['external', 'api', 'interface', 'protocol']):
                            has_external_dependencies = True
                        if any(keyword in dep.lower() for keyword in ['generic', 'union', 'optional', 'callable']):
                            has_complex_types = True
                
                # Determine safety based on usage and type analysis
                if not function.usages and not function.call_sites:
                    if has_external_dependencies:
                        results["keep_due_to_types"].append({
                            "function": function.name,
                            "reason": "Has external type dependencies",
                            "dependencies": results["resolved_dependencies"][-5:]  # Last 5 deps
                        })
                        log(f"      KEEP: {function.name} has external dependencies", "⚠️")
                    elif has_complex_types:
                        results["keep_due_to_types"].append({
                            "function": function.name,
                            "reason": "Has complex type annotations",
                            "dependencies": results["resolved_dependencies"][-5:]
                        })
                        log(f"      KEEP: {function.name} has complex types", "⚠️")
                    else:
                        results["safe_to_remove"].append({
                            "function": function.name,
                            "reason": "No usage and simple/no type dependencies",
                            "file": function.file.filepath
                        })
                        log(f"      SAFE TO REMOVE: {function.name}", "🗑️")
                
            except Exception as e:
                results["resolution_errors"].append(f"Function analysis failed for {function.name}: {e}")
                log(f"    ERROR analyzing {function.name}: {e}", "❌")
    
    # ==================== SUMMARY ====================
    log("\n" + "=" * 60, "📊")
    log("TYPE RESOLUTION ANALYSIS COMPLETE", "📊")
    log("=" * 60, "📊")
    
    log(f"Functions analyzed: {results['functions_analyzed']}", "📈")
    log(f"Type resolutions performed: {results['type_resolutions']}", "🎯")
    log(f"Dependencies resolved: {len(results['resolved_dependencies'])}", "🔗")
    log(f"Safe to remove: {len(results['safe_to_remove'])}", "🗑️")
    log(f"Keep due to types: {len(results['keep_due_to_types'])}", "⚠️")
    log(f"Resolution errors: {len(results['resolution_errors'])}", "❌")
    
    if results['safe_to_remove']:
        log("\nSafe to remove:", "🗑️")
        for item in results['safe_to_remove'][:5]:
            log(f"  • {item['function']} - {item['reason']}", "  ")
    
    if results['keep_due_to_types']:
        log("\nKeep due to type dependencies:", "⚠️")
        for item in results['keep_due_to_types'][:5]:
            log(f"  • {item['function']} - {item['reason']}", "  ")
    
    if results['resolution_errors']:
        log("\nResolution errors (sample):", "❌")
        for error in results['resolution_errors'][:3]:
            log(f"  • {error}", "  ")
    
    return results


def demonstrate_specific_resolution_patterns(codebase: Codebase):
    """
    Demonstrate specific type resolution patterns mentioned in the user's request.
    """
    print("\n🔍 SPECIFIC TYPE RESOLUTION PATTERNS")
    print("=" * 50)
    
    try:
        # Example 1: Function return type resolution
        print("1. Function Return Type Resolution:")
        for file in list(codebase.files)[:3]:  # Sample first 3 files
            for function in list(file.functions)[:2]:  # Sample first 2 functions
                if hasattr(function, 'return_type') and function.return_type:
                    print(f"   Function: {function.name}")
                    
                    return_type = function.return_type
                    
                    # Pattern 1: resolved_types
                    if hasattr(return_type, 'resolved_types'):
                        resolved_symbols = return_type.resolved_types
                        print(f"     resolved_types: {resolved_symbols}")
                    
                    # Pattern 2: resolved_value  
                    if hasattr(return_type, 'resolved_value'):
                        resolved_types = return_type.resolved_value
                        print(f"     resolved_value: {resolved_types}")
                    
                    # Generic type parameters
                    if hasattr(return_type, "parameters"):
                        print(f"     Generic parameters found: {len(return_type.parameters)}")
                        for i, param in enumerate(return_type.parameters[:2]):
                            if hasattr(param, 'resolved_value'):
                                param_types = param.resolved_value
                                print(f"       Parameter {i}: {param_types}")
                    
                    # Union type options
                    if hasattr(return_type, "options"):
                        print(f"     Union options found: {len(return_type.options)}")
                        for i, option in enumerate(return_type.options[:2]):
                            if hasattr(option, 'resolved_value'):
                                option_types = option.resolved_value
                                print(f"       Option {i}: {option_types}")
                    break
            break
        
        # Example 2: Assignment type resolution
        print("\n2. Assignment Type Resolution:")
        for file in list(codebase.files)[:2]:
            for assignment in list(file.assignments)[:3]:
                if hasattr(assignment, 'type') and assignment.type:
                    print(f"   Assignment: {assignment.name}")
                    assignment_type = assignment.type
                    if hasattr(assignment_type, 'resolved_types'):
                        resolved_type = assignment_type.resolved_types
                        print(f"     resolved_types: {resolved_type}")
                    break
            break
            
    except Exception as e:
        print(f"Error in demonstration: {e}")


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    """
    Example usage of type resolution for safe dead code analysis
    """
    print("🔍 Type Resolution for Safe Dead Code Analysis")
    print("=" * 60)
    
    # Initialize codebase with dependency graph
    print("📂 Loading codebase...")
    codebase = Codebase("./")  # Current directory
    
    # Run type resolution analysis
    print("\n🔍 Running type resolution analysis...")
    results = analyze_with_type_resolution(codebase, verbose=True)
    
    # Demonstrate specific patterns
    demonstrate_specific_resolution_patterns(codebase)
    
    print(f"\n🎉 Type resolution analysis complete!")
    print(f"Found {results['type_resolutions']} type resolutions")
    print(f"Identified {len(results['safe_to_remove'])} functions safe to remove")
    print(f"Preserved {len(results['keep_due_to_types'])} functions due to type dependencies")

