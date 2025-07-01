# Graph-Sitter Public API Documentation

This document describes the clean public API for external consumption by tools like contexten and other AI-powered development frameworks.

## Overview

The graph-sitter module now provides three main public interfaces:

```python
from graph_sitter import Codebase, Analysis, Codemods
```

## 1. Codebase - Core Codebase Representation

The `Codebase` class provides the fundamental interface for loading and manipulating codebases.

### Basic Usage

```python
from graph_sitter import Codebase

# Load a codebase
codebase = Codebase("/path/to/project")

# Access codebase properties
print(f"Project: {codebase.name}")
print(f"Files: {len(codebase.files)}")
```

### Key Features
- Tree-sitter based parsing
- Multi-language support
- File system operations
- Git integration
- Symbol resolution

## 2. Analysis - Comprehensive Analysis and Visualization

The `Analysis` module aggregates all analysis and visualization capabilities into a unified interface.

### High-Level Analysis Functions

```python
from graph_sitter import Codebase, Analysis

codebase = Codebase("/path/to/project")

# Comprehensive analysis (recommended starting point)
result = Analysis.analyze_comprehensive(codebase)

# Specific analysis types
metrics = Analysis.calculate_metrics(codebase)
dependencies = Analysis.analyze_dependencies(codebase)
dead_code = Analysis.find_dead_code(codebase)

# Visualizations
dashboard = Analysis.create_dashboard(codebase)
blast_radius = Analysis.visualize_blast_radius(codebase, function_name="my_function")
react_components = Analysis.create_react_visualizations(codebase)
```

### Available Analysis Types

#### Enhanced Code Analysis
- **Function**: `Analysis.analyze_comprehensive(codebase)`
- **Purpose**: Complete codebase analysis with all available analyzers
- **Returns**: `ComprehensiveAnalysisResult` with all analysis data

#### Metrics Calculation
- **Function**: `Analysis.calculate_metrics(codebase)`
- **Purpose**: Calculate complexity, maintainability, and quality metrics
- **Returns**: `CodebaseMetrics` object

#### Dependency Analysis
- **Function**: `Analysis.analyze_dependencies(codebase)`
- **Purpose**: Analyze import patterns, circular dependencies, and module relationships
- **Returns**: Dictionary with dependency analysis results

#### Dead Code Detection
- **Function**: `Analysis.find_dead_code(codebase)`
- **Purpose**: Find unused functions, imports, and variables
- **Returns**: Dictionary with dead code analysis results

#### Error Blast Radius
- **Function**: `Analysis.visualize_blast_radius(codebase, function_name)`
- **Purpose**: Visualize how changes to a function propagate through the codebase
- **Returns**: HTML visualization showing impact analysis

### Visualization Capabilities

#### Interactive Dashboard
```python
# Create comprehensive dashboard
dashboard_html = Analysis.create_dashboard(codebase)

# Save to file
with open("codebase_dashboard.html", "w") as f:
    f.write(dashboard_html)
```

#### React Components
```python
# Generate React-compatible visualization data
react_data = Analysis.create_react_visualizations(codebase)

# Access specific visualizations
function_graph = react_data["function_blast_radius"]
dependency_graph = react_data["dependency_visualization"]
metrics_dashboard = react_data["metrics_dashboard"]
```

### Advanced Analysis Classes

For more control, you can use the underlying analyzer classes directly:

```python
# Enhanced analyzer for detailed code analysis
analyzer = Analysis.EnhancedAnalyzer()
enhanced_result = analyzer.analyze(codebase)

# Dependency analyzer for import analysis
dep_analyzer = Analysis.DependencyAnalyzer()
dependencies = dep_analyzer.analyze(codebase)

# Call graph analyzer for function relationships
call_analyzer = Analysis.CallGraphAnalyzer()
call_graph = call_analyzer.generate_call_graph(codebase)

# Dead code analyzer for unused code detection
dead_analyzer = Analysis.DeadCodeAnalyzer()
dead_code = dead_analyzer.find_dead_code(codebase)
```

## 3. Codemods - Code Modification and Transformation

The `Codemods` module provides tools for automated code modification and refactoring.

### High-Level Codemod Functions

```python
from graph_sitter import Codebase, Codemods

codebase = Codebase("/path/to/project")

# Apply built-in codemod collections
Codemods.apply_modernization(codebase)
Codemods.fix_code_smells(codebase)
Codemods.apply_security_fixes(codebase)
Codemods.apply_performance_optimizations(codebase)

# Apply specific codemods
Codemods.apply_codemod(codebase, "convert_array_type_to_square_bracket")

# Apply multiple codemods
codemods_to_apply = ["bang_bang_to_boolean", "mark_is_boolean"]
Codemods.apply_multiple(codebase, codemods_to_apply)
```

### Custom Codemods

```python
# Create custom pattern-based codemod
custom_codemod = Codemods.create_custom_codemod(
    pattern=r"old_function\((.*?)\)",
    replacement=r"new_function(\1)"
)
custom_codemod.apply(codebase)

# Create refactoring codemod
refactor_codemod = Codemods.create_refactor_codemod(
    codebase, 
    refactor_type="extract_method"
)
refactor_codemod.apply()
```

### Available Codemods

```python
# Get list of all available codemods
available = Codemods.get_available_codemods()
print("Available codemods:", available)
```

## Integration Examples

### For Contexten Module

```python
# contexten/extensions/graph_sitter_integration.py
from graph_sitter import Codebase, Analysis, Codemods

class GraphSitterIntegration:
    def __init__(self, project_path):
        self.codebase = Codebase(project_path)
    
    def analyze_for_ai_context(self):
        """Analyze codebase to provide context for AI agents."""
        # Get comprehensive analysis
        analysis_result = Analysis.analyze_comprehensive(self.codebase)
        
        # Extract key information for AI context
        context = {
            "metrics": analysis_result.metrics_summary,
            "dependencies": analysis_result.dependency_analysis,
            "issues": analysis_result.enhanced_analysis.issues,
            "functions": analysis_result.function_contexts
        }
        
        return context
    
    def suggest_improvements(self):
        """Suggest code improvements based on analysis."""
        # Find dead code
        dead_code = Analysis.find_dead_code(self.codebase)
        
        # Calculate metrics to identify problem areas
        metrics = Analysis.calculate_metrics(self.codebase)
        
        suggestions = []
        if dead_code["unused_functions"]:
            suggestions.append("Remove unused functions")
        
        if metrics.average_complexity > 10:
            suggestions.append("Reduce function complexity")
            
        return suggestions
    
    def apply_automated_fixes(self):
        """Apply safe automated code improvements."""
        # Apply modernization codemods
        Codemods.apply_modernization(self.codebase)
        
        # Fix code smells
        Codemods.fix_code_smells(self.codebase)
        
        return "Automated fixes applied"
```

### For AI Code Analysis

```python
# ai_code_analyzer.py
from graph_sitter import Codebase, Analysis

def analyze_codebase_for_ai(project_path):
    """Analyze codebase and return AI-friendly summary."""
    codebase = Codebase(project_path)
    
    # Get comprehensive analysis
    result = Analysis.analyze_comprehensive(codebase)
    
    # Create AI-friendly summary
    summary = {
        "project_health": result.health_score,
        "risk_areas": result.risk_assessment,
        "recommendations": result.actionable_recommendations,
        "key_metrics": {
            "complexity": result.metrics_summary.get("average_complexity"),
            "maintainability": result.metrics_summary.get("maintainability_index"),
            "test_coverage": result.metrics_summary.get("test_coverage")
        },
        "error_hotspots": [
            issue for issue in result.enhanced_analysis.issues 
            if issue.severity == "high"
        ],
        "blast_radius_data": result.dependency_analysis
    }
    
    return summary

def generate_codebase_visualization(project_path, output_path):
    """Generate interactive visualization for codebase exploration."""
    codebase = Codebase(project_path)
    
    # Create comprehensive dashboard
    dashboard_html = Analysis.create_dashboard(codebase)
    
    # Save visualization
    with open(output_path, "w") as f:
        f.write(dashboard_html)
    
    print(f"Codebase visualization saved to {output_path}")
```

## Error Handling

The public API includes graceful error handling for missing dependencies:

```python
try:
    from graph_sitter import Codebase, Analysis, Codemods
    
    codebase = Codebase("/path/to/project")
    result = Analysis.analyze_comprehensive(codebase)
    
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages")
```

## Migration Guide

### From Internal Imports

**Before:**
```python
from graph_sitter.adapters.analysis.enhanced_analysis import analyze_codebase_enhanced
from graph_sitter.adapters.visualizations.react_visualizations import create_react_visualizations
from graph_sitter.adapters.codemods import Codemod
```

**After:**
```python
from graph_sitter import Codebase, Analysis, Codemods

# Analysis
result = Analysis.analyze_codebase_enhanced(codebase)
visualizations = Analysis.create_react_visualizations(codebase)

# Codemods
codemod = Codemods.create_custom_codemod(pattern="...", replacement="...")
```

## Best Practices

1. **Start with High-Level Functions**: Use `Analysis.analyze_comprehensive()` for initial analysis
2. **Use Specific Analyzers for Focused Tasks**: Use individual analyzers when you need specific functionality
3. **Combine Analysis with Visualization**: Always create visualizations to understand analysis results
4. **Test Codemods Safely**: Always backup your code before applying codemods
5. **Handle Import Errors**: Wrap imports in try-catch blocks for production use

## Future Enhancements

The public API is designed to be extensible. Future enhancements will include:

- Language-specific analyzers (JavaScript, TypeScript, Java, C++, Go, Rust)
- Real-time analysis with file watching
- Advanced security vulnerability detection
- Performance optimization suggestions
- Integration with popular IDEs and CI/CD systems
- Machine learning-powered code quality insights

## Support

For issues or questions about the public API, please refer to the main graph-sitter documentation or create an issue in the repository.

