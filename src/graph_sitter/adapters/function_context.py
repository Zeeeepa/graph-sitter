"""Function context analysis for comprehensive codebase understanding."""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol

logger = logging.getLogger(__name__)


@dataclass
class FunctionContext:
    """Comprehensive function context information."""
    name: str
    filepath: str
    implementation: Dict[str, Any]
    dependencies: List[Dict[str, Any]]
    usages: List[Dict[str, Any]]
    call_sites: List[Dict[str, Any]]
    complexity_metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    impact_score: float
    risk_level: str


@dataclass
class TrainingData:
    """Training data for LLM function prediction."""
    functions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


def hop_through_imports(imp: Import) -> Union[Symbol, ExternalModule]:
    """
    Finds the root symbol for an import by following re-export chains.
    
    When working with imports, symbols can be re-exported multiple times.
    For example, a helper function might be imported and re-exported through
    several files before being used. We need to follow this chain to find
    the actual implementation.
    
    Args:
        imp: Import object to resolve
        
    Returns:
        The root symbol or external module
    """
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol


def get_function_context(function: Function) -> Dict[str, Any]:
    """
    Get the implementation, dependencies, and usages of a function.
    
    This creates a structured representation of each function's context
    including its source code, dependencies, and usage patterns.
    
    Args:
        function: Function object to analyze
        
    Returns:
        Dictionary containing comprehensive function context
    """
    context = {
        "implementation": {
            "source": function.source,
            "filepath": function.filepath,
            "line_start": getattr(function, 'line_start', None),
            "line_end": getattr(function, 'line_end', None),
            "name": function.name,
            "parameters": [p.name for p in function.parameters] if hasattr(function, 'parameters') else [],
            "return_type": getattr(function, 'return_type', None),
            "is_async": getattr(function, 'is_async', False),
            "has_decorators": bool(getattr(function, 'decorators', [])),
            "docstring": getattr(function, 'docstring', None)
        },
        "dependencies": [],
        "usages": [],
        "call_sites": [],
        "metrics": {}
    }
    
    # Add dependencies
    if hasattr(function, 'dependencies'):
        for dep in function.dependencies:
            try:
                # Hop through imports to find the root symbol source
                if isinstance(dep, Import):
                    dep = hop_through_imports(dep)
                
                dep_info = {
                    "source": getattr(dep, 'source', str(dep)),
                    "filepath": getattr(dep, 'filepath', None),
                    "name": getattr(dep, 'name', str(dep)),
                    "type": type(dep).__name__
                }
                context["dependencies"].append(dep_info)
            except Exception as e:
                logger.warning(f"Error processing dependency {dep}: {e}")
                context["dependencies"].append({
                    "source": str(dep),
                    "filepath": None,
                    "name": str(dep),
                    "type": "unknown",
                    "error": str(e)
                })
    
    # Add usages
    if hasattr(function, 'usages'):
        for usage in function.usages:
            try:
                usage_info = {
                    "source": getattr(usage.usage_symbol, 'source', str(usage)),
                    "filepath": getattr(usage.usage_symbol, 'filepath', None),
                    "line": getattr(usage, 'line', None),
                    "context": getattr(usage, 'context', None)
                }
                context["usages"].append(usage_info)
            except Exception as e:
                logger.warning(f"Error processing usage {usage}: {e}")
                context["usages"].append({
                    "source": str(usage),
                    "filepath": None,
                    "error": str(e)
                })
    
    # Add call sites
    if hasattr(function, 'call_sites'):
        for call_site in function.call_sites:
            try:
                call_info = {
                    "source": getattr(call_site, 'source', str(call_site)),
                    "filepath": getattr(call_site, 'filepath', None),
                    "line": getattr(call_site, 'line', None),
                    "caller": getattr(call_site, 'caller', None)
                }
                context["call_sites"].append(call_info)
            except Exception as e:
                logger.warning(f"Error processing call site {call_site}: {e}")
                context["call_sites"].append({
                    "source": str(call_site),
                    "filepath": None,
                    "error": str(e)
                })
    
    # Add basic metrics
    try:
        source_lines = function.source.split('\n') if function.source else []
        context["metrics"] = {
            "line_count": len(source_lines),
            "parameter_count": len(context["implementation"]["parameters"]),
            "dependency_count": len(context["dependencies"]),
            "usage_count": len(context["usages"]),
            "call_site_count": len(context["call_sites"]),
            "complexity_estimate": _estimate_complexity(function.source) if function.source else 0
        }
    except Exception as e:
        logger.warning(f"Error calculating metrics for {function.name}: {e}")
        context["metrics"] = {}
    
    return context


def _estimate_complexity(source: str) -> int:
    """Estimate cyclomatic complexity from source code."""
    if not source:
        return 0
    
    complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with']
    complexity = 1  # Base complexity
    
    for line in source.split('\n'):
        line = line.strip()
        for keyword in complexity_keywords:
            if line.startswith(keyword + ' ') or line.startswith(keyword + ':'):
                complexity += 1
    
    return complexity


def run(codebase: Codebase) -> TrainingData:
    """
    Generate training data using a node2vec-like approach for code embeddings.
    
    This processes all functions in the codebase to generate comprehensive
    training data that can be used for various ML tasks like function prediction,
    code embeddings, and dependency analysis.
    
    Args:
        codebase: Codebase object to analyze
        
    Returns:
        TrainingData object with functions and metadata
    """
    logger.info("Starting function context analysis for training data generation")
    
    # Track all function contexts
    training_data = {
        "functions": [],
        "metadata": {
            "total_functions": len(codebase.functions),
            "total_processed": 0,
            "avg_dependencies": 0,
            "avg_usages": 0,
            "avg_complexity": 0,
            "files_analyzed": 0,
            "analysis_timestamp": None
        },
    }
    
    processed_files = set()
    
    # Process each function in the codebase
    for function in codebase.functions:
        try:
            # Skip if function is too small or has no meaningful content
            if not function.source or len(function.source.split("\n")) < 2:
                continue
            
            # Get function context
            context = get_function_context(function)
            
            # Only keep functions with enough context for meaningful analysis
            if len(context["dependencies"]) + len(context["usages"]) > 0:
                training_data["functions"].append(context)
                
                # Track processed files
                if context["implementation"]["filepath"]:
                    processed_files.add(context["implementation"]["filepath"])
                    
        except Exception as e:
            logger.warning(f"Error processing function {function.name}: {e}")
            continue
    
    # Update metadata
    training_data["metadata"]["total_processed"] = len(training_data["functions"])
    training_data["metadata"]["files_analyzed"] = len(processed_files)
    
    if training_data["functions"]:
        # Calculate averages
        training_data["metadata"]["avg_dependencies"] = sum(
            len(f["dependencies"]) for f in training_data["functions"]
        ) / len(training_data["functions"])
        
        training_data["metadata"]["avg_usages"] = sum(
            len(f["usages"]) for f in training_data["functions"]
        ) / len(training_data["functions"])
        
        training_data["metadata"]["avg_complexity"] = sum(
            f["metrics"].get("complexity_estimate", 0) for f in training_data["functions"]
        ) / len(training_data["functions"])
    
    # Add timestamp
    from datetime import datetime
    training_data["metadata"]["analysis_timestamp"] = datetime.now().isoformat()
    
    logger.info(f"Processed {training_data['metadata']['total_processed']} functions from {training_data['metadata']['files_analyzed']} files")
    
    return TrainingData(
        functions=training_data["functions"],
        metadata=training_data["metadata"]
    )


def create_training_example(function_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a masked prediction example from function data.
    
    This creates training examples for LLM tasks like masked function prediction,
    where the model needs to predict implementation from context.
    
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
            "metrics": function_data["metrics"]
        },
        "target": function_data["implementation"]
    }


def analyze_function_issues(function: Function, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze function for potential issues based on context.
    
    Args:
        function: Function object
        context: Function context data
        
    Returns:
        List of identified issues
    """
    issues = []
    
    # Check for high complexity
    complexity = context["metrics"].get("complexity_estimate", 0)
    if complexity > 10:
        issues.append({
            "type": "high_complexity",
            "severity": "warning",
            "message": f"Function has high cyclomatic complexity ({complexity})",
            "recommendation": "Consider breaking this function into smaller functions"
        })
    
    # Check for no usages (potential dead code)
    if context["metrics"].get("usage_count", 0) == 0:
        issues.append({
            "type": "unused_function",
            "severity": "info",
            "message": "Function appears to be unused",
            "recommendation": "Consider removing if truly unused, or add tests"
        })
    
    # Check for too many dependencies
    dep_count = context["metrics"].get("dependency_count", 0)
    if dep_count > 15:
        issues.append({
            "type": "high_coupling",
            "severity": "warning",
            "message": f"Function has many dependencies ({dep_count})",
            "recommendation": "Consider reducing dependencies or splitting functionality"
        })
    
    # Check for missing docstring
    if not context["implementation"].get("docstring"):
        issues.append({
            "type": "missing_documentation",
            "severity": "info",
            "message": "Function lacks documentation",
            "recommendation": "Add docstring explaining purpose and parameters"
        })
    
    return issues


def get_enhanced_function_context(function: Function) -> FunctionContext:
    """
    Get enhanced function context with issues analysis and recommendations.
    
    Args:
        function: Function to analyze
        
    Returns:
        Enhanced function context with comprehensive analysis
    """
    # Get basic context
    basic_context = get_function_context(function)
    
    # Analyze issues
    issues = analyze_function_issues(function, basic_context)
    
    # Calculate impact score
    impact_score = _calculate_impact_score(basic_context)
    
    # Determine risk level
    risk_level = _determine_risk_level(basic_context, issues)
    
    # Generate recommendations
    recommendations = _generate_recommendations(basic_context, issues)
    
    return FunctionContext(
        name=function.name,
        filepath=basic_context["implementation"]["filepath"],
        implementation=basic_context["implementation"],
        dependencies=basic_context["dependencies"],
        usages=basic_context["usages"],
        call_sites=basic_context["call_sites"],
        complexity_metrics=basic_context["metrics"],
        issues=issues,
        recommendations=recommendations,
        impact_score=impact_score,
        risk_level=risk_level
    )


def _calculate_impact_score(context: Dict[str, Any]) -> float:
    """Calculate impact score based on usage and complexity."""
    usage_count = context["metrics"].get("usage_count", 0)
    complexity = context["metrics"].get("complexity_estimate", 0)
    dependency_count = context["metrics"].get("dependency_count", 0)
    
    # Normalize and weight factors
    usage_score = min(usage_count / 10.0, 1.0) * 0.4
    complexity_score = min(complexity / 20.0, 1.0) * 0.3
    dependency_score = min(dependency_count / 15.0, 1.0) * 0.3
    
    return usage_score + complexity_score + dependency_score


def _determine_risk_level(context: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
    """Determine risk level based on context and issues."""
    high_severity_issues = [i for i in issues if i.get("severity") == "error"]
    warning_issues = [i for i in issues if i.get("severity") == "warning"]
    
    if high_severity_issues:
        return "high"
    elif len(warning_issues) > 2:
        return "medium"
    elif warning_issues:
        return "low"
    else:
        return "minimal"


def _generate_recommendations(context: Dict[str, Any], issues: List[Dict[str, Any]]) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    # Add issue-specific recommendations
    for issue in issues:
        if "recommendation" in issue:
            recommendations.append(issue["recommendation"])
    
    # Add general recommendations based on metrics
    complexity = context["metrics"].get("complexity_estimate", 0)
    if complexity > 5:
        recommendations.append("Consider adding unit tests to verify complex logic")
    
    usage_count = context["metrics"].get("usage_count", 0)
    if usage_count > 10:
        recommendations.append("High usage function - ensure it's well-tested and documented")
    
    return list(set(recommendations))  # Remove duplicates


# Standalone functions for external use
def analyze_codebase_functions(codebase: Codebase, output_file: str = "training_data.json") -> Dict[str, Any]:
    """
    Analyze all functions in a codebase and save training data.
    
    Args:
        codebase: Codebase to analyze
        output_file: File to save training data
        
    Returns:
        Analysis summary
    """
    print("Initializing codebase analysis...")
    training_data = run(codebase)
    
    print("Generating training data...")
    
    # Create training examples
    examples = [create_training_example(f) for f in training_data.functions]
    
    # Save training data
    output_data = {
        "training_examples": examples,
        "raw_functions": training_data.functions,
        "metadata": training_data.metadata
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Training data saved to {output_file}")
    
    return {
        "total_functions": training_data.metadata["total_functions"],
        "processed_functions": training_data.metadata["total_processed"],
        "files_analyzed": training_data.metadata["files_analyzed"],
        "avg_dependencies": training_data.metadata["avg_dependencies"],
        "avg_usages": training_data.metadata["avg_usages"],
        "avg_complexity": training_data.metadata["avg_complexity"],
        "training_examples": len(examples),
        "output_file": output_file
    }


if __name__ == "__main__":
    # Example usage
    print("Function Context Analyzer")
    print("=" * 50)
    print("This module provides comprehensive function context analysis")
    print("for codebase understanding and LLM training data generation.")
    print("\nKey features:")
    print("- Function dependency tracking")
    print("- Usage pattern analysis")
    print("- Complexity metrics")
    print("- Issue detection")
    print("- Training data generation")

