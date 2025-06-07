"""
Training Data Generation Module

Generates structured training data for LLM training, including function context extraction,
dependency mapping, and code embeddings. Based on features from README4.md.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.external_module import ExternalModule
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    Function = Any
    Symbol = Any
    Import = Any


def generate_training_data(codebase: Codebase) -> Dict[str, Any]:
    """
    Generate training data using a node2vec-like approach for code embeddings.
    Based on the training data generation from README4.md.
    
    Args:
        codebase: The codebase to process
        
    Returns:
        Dictionary with training data and metadata
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        # Track all function contexts
        training_data = {
            "functions": [],
            "metadata": {
                "total_functions": 0,
                "total_processed": 0,
                "avg_dependencies": 0,
                "avg_usages": 0,
                "generation_timestamp": None
            },
            "patterns": {
                "common_function_patterns": [],
                "dependency_patterns": [],
                "usage_patterns": []
            }
        }
        
        functions = list(codebase.functions)
        training_data["metadata"]["total_functions"] = len(functions)
        
        # Process each function in the codebase
        for function in functions:
            # Skip if function is too small
            if hasattr(function, 'source') and len(function.source.split('\n')) < 2:
                continue
            
            # Get function context
            context = extract_function_context(function)
            
            # Only keep functions with enough context
            if context and (len(context.get("dependencies", [])) + len(context.get("usages", [])) > 0):
                training_data["functions"].append(context)
        
        # Update metadata
        training_data["metadata"]["total_processed"] = len(training_data["functions"])
        
        if training_data["functions"]:
            training_data["metadata"]["avg_dependencies"] = sum(
                len(f.get("dependencies", [])) for f in training_data["functions"]
            ) / len(training_data["functions"])
            
            training_data["metadata"]["avg_usages"] = sum(
                len(f.get("usages", [])) for f in training_data["functions"]
            ) / len(training_data["functions"])
        
        # Extract patterns
        training_data["patterns"] = extract_code_patterns(training_data["functions"])
        
        return training_data
        
    except Exception as e:
        return {"error": f"Error generating training data: {str(e)}"}


def extract_function_context(function: Function) -> Optional[Dict[str, Any]]:
    """
    Extract comprehensive context for a function including implementation, dependencies, and usages.
    
    Args:
        function: The function to extract context from
        
    Returns:
        Dictionary with function context or None if extraction fails
    """
    try:
        context = {
            "implementation": {
                "source": getattr(function, 'source', ''),
                "filepath": function.file.filepath if hasattr(function, 'file') else "unknown",
                "name": function.name,
                "line_count": 0,
                "complexity_score": 0
            },
            "dependencies": [],
            "usages": [],
            "metadata": {
                "parameter_count": 0,
                "return_type": getattr(function, 'return_type', 'unknown'),
                "is_async": getattr(function, 'is_async', False),
                "has_docstring": bool(getattr(function, 'docstring', None)),
                "function_calls": []
            }
        }
        
        # Calculate basic metrics
        if hasattr(function, 'source'):
            context["implementation"]["line_count"] = len(function.source.split('\n'))
            context["implementation"]["complexity_score"] = calculate_complexity_score(function)
        
        # Extract parameter information
        if hasattr(function, 'parameters'):
            context["metadata"]["parameter_count"] = len(function.parameters)
        
        # Extract function calls
        if hasattr(function, 'function_calls'):
            context["metadata"]["function_calls"] = [
                call.name for call in function.function_calls if hasattr(call, 'name')
            ]
        
        # Add dependencies
        if hasattr(function, 'dependencies'):
            for dep in function.dependencies:
                # Hop through imports to find the root symbol source
                if isinstance(dep, Import):
                    dep = hop_through_imports(dep)
                
                if dep:
                    dep_context = {
                        "source": getattr(dep, 'source', ''),
                        "filepath": dep.file.filepath if hasattr(dep, 'file') else "unknown",
                        "name": getattr(dep, 'name', 'unknown'),
                        "type": type(dep).__name__,
                        "is_external": isinstance(dep, ExternalModule)
                    }
                    context["dependencies"].append(dep_context)
        
        # Add usages
        if hasattr(function, 'usages'):
            for usage in function.usages:
                if hasattr(usage, 'usage_symbol'):
                    usage_context = {
                        "source": getattr(usage.usage_symbol, 'source', ''),
                        "filepath": usage.usage_symbol.file.filepath if hasattr(usage.usage_symbol, 'file') else "unknown",
                        "name": getattr(usage.usage_symbol, 'name', 'unknown'),
                        "context_type": type(usage.usage_symbol).__name__
                    }
                    context["usages"].append(usage_context)
        
        return context
        
    except Exception as e:
        print(f"Error extracting context for function {getattr(function, 'name', 'unknown')}: {e}")
        return None


def hop_through_imports(imp: Import) -> Optional[Symbol]:
    """
    Find the root symbol for an import by following the import chain.
    
    Args:
        imp: The import to resolve
        
    Returns:
        The root symbol or None if resolution fails
    """
    try:
        if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, Import):
            return hop_through_imports(imp.imported_symbol)
        return imp.imported_symbol if hasattr(imp, 'imported_symbol') else None
        
    except Exception:
        return None


def calculate_complexity_score(function: Function) -> int:
    """
    Calculate a simple complexity score for a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        Complexity score (higher = more complex)
    """
    try:
        score = 1  # Base complexity
        
        if not hasattr(function, 'source'):
            return score
        
        source = function.source.lower()
        
        # Count decision points
        decision_keywords = ['if ', 'elif ', 'while ', 'for ', 'try:', 'except ', 'and ', 'or ']
        for keyword in decision_keywords:
            score += source.count(keyword)
        
        # Add complexity for nested structures
        score += source.count('    if ')  # Nested if statements
        score += source.count('        ')  # Deep nesting
        
        # Add complexity for function calls
        if hasattr(function, 'function_calls'):
            score += len(function.function_calls)
        
        return score
        
    except Exception:
        return 1


def extract_code_patterns(functions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract common patterns from the function data.
    
    Args:
        functions_data: List of function context dictionaries
        
    Returns:
        Dictionary with extracted patterns
    """
    try:
        patterns = {
            "common_function_patterns": [],
            "dependency_patterns": [],
            "usage_patterns": [],
            "naming_patterns": [],
            "complexity_patterns": {}
        }
        
        # Analyze function naming patterns
        function_names = [f["implementation"]["name"] for f in functions_data]
        naming_analysis = analyze_naming_patterns(function_names)
        patterns["naming_patterns"] = naming_analysis
        
        # Analyze dependency patterns
        dependency_analysis = analyze_dependency_patterns(functions_data)
        patterns["dependency_patterns"] = dependency_analysis
        
        # Analyze usage patterns
        usage_analysis = analyze_usage_patterns(functions_data)
        patterns["usage_patterns"] = usage_analysis
        
        # Analyze complexity patterns
        complexity_scores = [f["implementation"]["complexity_score"] for f in functions_data]
        if complexity_scores:
            patterns["complexity_patterns"] = {
                "avg_complexity": sum(complexity_scores) / len(complexity_scores),
                "max_complexity": max(complexity_scores),
                "min_complexity": min(complexity_scores),
                "high_complexity_functions": len([s for s in complexity_scores if s > 10])
            }
        
        return patterns
        
    except Exception as e:
        return {"error": f"Error extracting patterns: {str(e)}"}


def analyze_naming_patterns(function_names: List[str]) -> Dict[str, Any]:
    """Analyze naming patterns in function names."""
    patterns = {
        "common_prefixes": defaultdict(int),
        "common_suffixes": defaultdict(int),
        "naming_conventions": defaultdict(int),
        "avg_name_length": 0
    }
    
    try:
        if not function_names:
            return dict(patterns)
        
        # Calculate average name length
        patterns["avg_name_length"] = sum(len(name) for name in function_names) / len(function_names)
        
        # Analyze naming conventions
        for name in function_names:
            if '_' in name:
                patterns["naming_conventions"]["snake_case"] += 1
            elif any(c.isupper() for c in name[1:]):
                patterns["naming_conventions"]["camelCase"] += 1
            else:
                patterns["naming_conventions"]["lowercase"] += 1
            
            # Extract prefixes and suffixes
            if '_' in name:
                parts = name.split('_')
                if len(parts) > 1:
                    patterns["common_prefixes"][parts[0]] += 1
                    patterns["common_suffixes"][parts[-1]] += 1
        
        # Convert to regular dicts and get top patterns
        patterns["common_prefixes"] = dict(sorted(patterns["common_prefixes"].items(), 
                                                 key=lambda x: x[1], reverse=True)[:10])
        patterns["common_suffixes"] = dict(sorted(patterns["common_suffixes"].items(), 
                                                 key=lambda x: x[1], reverse=True)[:10])
        patterns["naming_conventions"] = dict(patterns["naming_conventions"])
        
        return patterns
        
    except Exception:
        return {"error": "Error analyzing naming patterns"}


def analyze_dependency_patterns(functions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze dependency patterns across functions."""
    patterns = {
        "most_common_dependencies": defaultdict(int),
        "external_vs_internal": {"external": 0, "internal": 0},
        "dependency_clusters": defaultdict(list),
        "avg_dependencies_per_function": 0
    }
    
    try:
        total_dependencies = 0
        
        for func_data in functions_data:
            dependencies = func_data.get("dependencies", [])
            total_dependencies += len(dependencies)
            
            for dep in dependencies:
                dep_name = dep.get("name", "unknown")
                patterns["most_common_dependencies"][dep_name] += 1
                
                if dep.get("is_external", False):
                    patterns["external_vs_internal"]["external"] += 1
                else:
                    patterns["external_vs_internal"]["internal"] += 1
                
                # Group by dependency type
                dep_type = dep.get("type", "unknown")
                patterns["dependency_clusters"][dep_type].append(dep_name)
        
        # Calculate averages
        if functions_data:
            patterns["avg_dependencies_per_function"] = total_dependencies / len(functions_data)
        
        # Convert to regular dicts and get top patterns
        patterns["most_common_dependencies"] = dict(sorted(patterns["most_common_dependencies"].items(), 
                                                          key=lambda x: x[1], reverse=True)[:20])
        patterns["dependency_clusters"] = {k: list(set(v)) for k, v in patterns["dependency_clusters"].items()}
        
        return patterns
        
    except Exception:
        return {"error": "Error analyzing dependency patterns"}


def analyze_usage_patterns(functions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze usage patterns across functions."""
    patterns = {
        "most_used_functions": defaultdict(int),
        "usage_distribution": {},
        "avg_usages_per_function": 0
    }
    
    try:
        total_usages = 0
        usage_counts = []
        
        for func_data in functions_data:
            usages = func_data.get("usages", [])
            usage_count = len(usages)
            total_usages += usage_count
            usage_counts.append(usage_count)
            
            func_name = func_data["implementation"]["name"]
            patterns["most_used_functions"][func_name] = usage_count
        
        # Calculate statistics
        if functions_data:
            patterns["avg_usages_per_function"] = total_usages / len(functions_data)
        
        if usage_counts:
            patterns["usage_distribution"] = {
                "max_usages": max(usage_counts),
                "min_usages": min(usage_counts),
                "functions_with_no_usages": len([c for c in usage_counts if c == 0]),
                "functions_with_many_usages": len([c for c in usage_counts if c > 10])
            }
        
        # Get top used functions
        patterns["most_used_functions"] = dict(sorted(patterns["most_used_functions"].items(), 
                                                     key=lambda x: x[1], reverse=True)[:20])
        
        return patterns
        
    except Exception:
        return {"error": "Error analyzing usage patterns"}


def create_function_embeddings(training_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create embeddings data suitable for training code embeddings models.
    
    Args:
        training_data: Training data generated by generate_training_data
        
    Returns:
        Dictionary with embedding training data
    """
    try:
        embeddings_data = {
            "function_pairs": [],
            "context_windows": [],
            "similarity_pairs": [],
            "metadata": {
                "total_pairs": 0,
                "avg_context_size": 0
            }
        }
        
        if "error" in training_data:
            return training_data
        
        functions = training_data.get("functions", [])
        
        # Create function pairs based on dependencies and usages
        for i, func in enumerate(functions):
            func_name = func["implementation"]["name"]
            
            # Create pairs with dependencies
            for dep in func.get("dependencies", []):
                dep_name = dep.get("name", "")
                if dep_name and dep_name != func_name:
                    embeddings_data["function_pairs"].append({
                        "source": func_name,
                        "target": dep_name,
                        "relationship": "depends_on",
                        "context": func["implementation"]["source"][:200]  # First 200 chars
                    })
            
            # Create pairs with usages
            for usage in func.get("usages", []):
                usage_name = usage.get("name", "")
                if usage_name and usage_name != func_name:
                    embeddings_data["function_pairs"].append({
                        "source": usage_name,
                        "target": func_name,
                        "relationship": "uses",
                        "context": usage.get("source", "")[:200]
                    })
        
        # Create context windows for each function
        for func in functions:
            context_window = {
                "function": func["implementation"]["name"],
                "context": {
                    "implementation": func["implementation"]["source"],
                    "dependencies": [dep.get("source", "")[:100] for dep in func.get("dependencies", [])],
                    "usages": [usage.get("source", "")[:100] for usage in func.get("usages", [])]
                }
            }
            embeddings_data["context_windows"].append(context_window)
        
        # Update metadata
        embeddings_data["metadata"]["total_pairs"] = len(embeddings_data["function_pairs"])
        if embeddings_data["context_windows"]:
            avg_context = sum(
                len(cw["context"]["implementation"]) + 
                sum(len(dep) for dep in cw["context"]["dependencies"]) +
                sum(len(usage) for usage in cw["context"]["usages"])
                for cw in embeddings_data["context_windows"]
            ) / len(embeddings_data["context_windows"])
            embeddings_data["metadata"]["avg_context_size"] = avg_context
        
        return embeddings_data
        
    except Exception as e:
        return {"error": f"Error creating function embeddings: {str(e)}"}


def create_training_example(function_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a masked prediction example from function data.
    Based on the example from README4.md.
    
    Args:
        function_data: Function context data
        
    Returns:
        Training example with context and target
    """
    try:
        return {
            "context": {
                "dependencies": function_data.get("dependencies", []),
                "usages": function_data.get("usages", []),
                "metadata": function_data.get("metadata", {})
            },
            "target": function_data.get("implementation", {})
        }
        
    except Exception as e:
        return {"error": f"Error creating training example: {str(e)}"}


def save_training_data(training_data: Dict[str, Any], output_file: str) -> Dict[str, Any]:
    """
    Save training data to a JSON file.
    
    Args:
        training_data: The training data to save
        output_file: Path to the output file
        
    Returns:
        Dictionary with save results
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        return {
            "success": True,
            "file": output_file,
            "functions_saved": len(training_data.get("functions", [])),
            "file_size": f.tell() if hasattr(f, 'tell') else 0
        }
        
    except Exception as e:
        return {"error": f"Error saving training data: {str(e)}"}


def run_training_data_generation(codebase: Codebase, output_file: str = "training_data.json") -> Dict[str, Any]:
    """
    Complete training data generation pipeline.
    Based on the run function from README4.md.
    
    Args:
        codebase: The codebase to process
        output_file: Path to save the training data
        
    Returns:
        Dictionary with generation results
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        print("Generating training data...")
        training_data = generate_training_data(codebase)
        
        if "error" in training_data:
            return training_data
        
        print("Creating embeddings data...")
        embeddings_data = create_function_embeddings(training_data)
        
        # Combine training data and embeddings
        complete_data = {
            "training_data": training_data,
            "embeddings_data": embeddings_data,
            "generation_info": {
                "codebase_path": getattr(codebase, 'path', 'unknown'),
                "total_functions_processed": training_data["metadata"]["total_processed"],
                "patterns_extracted": len(training_data["patterns"])
            }
        }
        
        print("Saving training data...")
        save_result = save_training_data(complete_data, output_file)
        
        if "error" in save_result:
            return save_result
        
        print(f"Training data saved to {output_file}")
        
        return {
            "success": True,
            "output_file": output_file,
            "functions_processed": training_data["metadata"]["total_processed"],
            "patterns_found": len(training_data["patterns"]),
            "embedding_pairs": embeddings_data["metadata"]["total_pairs"]
        }
        
    except Exception as e:
        return {"error": f"Error in training data generation pipeline: {str(e)}"}

