# Graph-Sitter Visualization Adapters

This package provides comprehensive visualization capabilities for codebase analysis using graph-sitter. The visualization adapters help developers understand code relationships, dependencies, and architectural patterns through interactive graph visualizations.

## Overview

The visualization system includes four main types of analysis:

1. **Function Call Relationships** - Trace downstream function call relationships
2. **Symbol Dependencies** - Map symbol dependencies throughout the codebase  
3. **Function Blast Radius** - Show impact radius of potential changes
4. **Class Method Relationships** - Comprehensive view of class method interactions

## Quick Start

```python
from graph_sitter import Codebase
from graph_sitter.adapters.visualizations import (
    UnifiedVisualizationManager,
    VisualizationType
)

# Initialize codebase
codebase = Codebase.from_repo("your-org/your-repo")

# Create visualization manager
manager = UnifiedVisualizationManager()

# Create a call trace visualization
result = manager.create_visualization(
    codebase=codebase,
    visualization_type=VisualizationType.CALL_TRACE,
    target=codebase.functions[0]  # Target function
)

print(f"Created visualization with {result.graph.number_of_nodes()} nodes")
```

## Visualization Types

### 1. Function Call Relationships (`CALL_TRACE`)

Traces downstream function call relationships from a target method, useful for understanding execution flow and identifying complex call chains.

```python
from graph_sitter.adapters.visualizations import CallTraceVisualizer, CallTraceConfig

# Configure the visualizer
config = CallTraceConfig(
    max_depth=5,
    ignore_external_modules=True,
    include_recursive_calls=False,
    highlight_entry_points=True
)

# Create visualizer and analyze
visualizer = CallTraceVisualizer(config)
result = visualizer.visualize(codebase, target_function)

# Access results
print(f"Call chains found: {result.metadata['total_call_chains']}")
print(f"Max depth reached: {result.metadata['max_depth_reached']}")
```

**Key Features:**
- Configurable depth control
- Entry point detection
- Recursive call handling
- Critical function identification
- Call frequency tracking

### 2. Symbol Dependencies (`DEPENDENCY_TRACE`)

Maps symbol dependencies throughout the codebase, helping identify tightly coupled components and understand the impact of modifying shared dependencies.

```python
from graph_sitter.adapters.visualizations import DependencyTraceVisualizer, DependencyTraceConfig

# Configure dependency analysis
config = DependencyTraceConfig(
    max_depth=3,
    include_import_dependencies=True,
    include_symbol_dependencies=True,
    show_circular_dependencies=True,
    group_by_package=True
)

# Analyze dependencies
visualizer = DependencyTraceVisualizer(config)
result = visualizer.visualize(codebase, target_symbol)

# Check for circular dependencies
circular_deps = result.metadata.get("circular_dependencies", [])
if circular_deps:
    print(f"Found {len(circular_deps)} circular dependencies")
```

**Key Features:**
- Import and symbol dependency tracking
- Circular dependency detection
- Package-level grouping
- Dependency weight calculation
- Coupling analysis

### 3. Function Blast Radius (`BLAST_RADIUS`)

Shows the impact radius of potential changes by revealing all code paths that could be affected by modifying a particular function or symbol.

```python
from graph_sitter.adapters.visualizations import BlastRadiusVisualizer, BlastRadiusConfig

# Configure blast radius analysis
config = BlastRadiusConfig(
    max_depth=4,
    include_test_usages=False,
    highlight_critical_paths=True,
    show_impact_metrics=True,
    weight_by_usage_frequency=True
)

# Analyze impact
visualizer = BlastRadiusVisualizer(config)
result = visualizer.visualize(codebase, target_function)

# Get impact metrics
impact_metrics = result.metadata.get("impact_metrics", {})
print(f"Blast radius size: {impact_metrics.get('blast_radius_size', 0)}")
print(f"Critical impacts: {impact_metrics.get('critical_impacts', 0)}")
```

**Key Features:**
- Impact level visualization
- Critical path identification
- Usage frequency analysis
- Risk assessment metrics
- Test usage filtering

### 4. Class Method Relationships (`METHOD_RELATIONSHIPS`)

Creates comprehensive views of class method interactions, helping understand class cohesion and identify architectural opportunities.

```python
from graph_sitter.adapters.visualizations import MethodRelationshipsVisualizer, MethodRelationshipsConfig

# Configure method analysis
config = MethodRelationshipsConfig(
    max_depth=3,
    include_private_methods=True,
    show_inheritance_chain=True,
    highlight_overridden_methods=True,
    group_by_access_level=True
)

# Analyze class methods
visualizer = MethodRelationshipsVisualizer(config)
result = visualizer.visualize(codebase, target_class)

# Get cohesion metrics
cohesion = result.metadata.get("average_cohesion", 0)
print(f"Class cohesion: {cohesion:.2f}")
```

**Key Features:**
- Method interaction analysis
- Cohesion metrics calculation
- Inheritance chain visualization
- Access level grouping
- Overridden method detection

## Unified Visualization Manager

The `UnifiedVisualizationManager` provides a single interface for all visualization types and advanced features:

### Batch Processing

```python
from graph_sitter.adapters.visualizations import BatchVisualizationRequest, OutputFormat

# Create batch request
request = BatchVisualizationRequest(
    visualization_types=[
        VisualizationType.CALL_TRACE,
        VisualizationType.DEPENDENCY_TRACE
    ],
    targets=[function1, function2, class1],
    output_formats=[OutputFormat.JSON, OutputFormat.GRAPHML],
    output_directory=Path("./output"),
    config_overrides={
        VisualizationType.CALL_TRACE: {"max_depth": 3}
    }
)

# Execute batch processing
result = manager.create_batch_visualizations(codebase, request)
```

### Comprehensive Analysis

```python
# Analyze entire codebase with all visualization types
results = manager.create_comprehensive_visualization(
    codebase=codebase,
    output_directory=Path("./comprehensive_analysis")
)

# Results contain all visualization types
for viz_type, result in results.items():
    print(f"{viz_type}: {result.graph.number_of_nodes()} nodes")
```

### Interactive HTML Reports

```python
# Generate interactive HTML report
html_path = manager.create_interactive_html_report(
    codebase=codebase,
    output_path=Path("./report.html"),
    include_types=[VisualizationType.CALL_TRACE, VisualizationType.BLAST_RADIUS]
)
```

### Web-Friendly Data Export

```python
# Generate data for web frontends
web_data = manager.generate_visualization_data(
    codebase=codebase,
    visualization_type=VisualizationType.CALL_TRACE
)

# Data includes nodes, edges, and metadata in JSON-serializable format
print(f"Nodes: {len(web_data['nodes'])}")
print(f"Edges: {len(web_data['edges'])}")
```

## Configuration System

All visualizers support extensive configuration through dedicated config classes:

### Common Configuration Options

```python
from graph_sitter.adapters.visualizations import VisualizationConfig

config = VisualizationConfig(
    max_depth=100,                    # Maximum traversal depth
    ignore_external_modules=False,    # Skip external dependencies
    ignore_class_calls=True,          # Skip class constructor calls
    color_palette={...},              # Custom color scheme
    include_metadata=True,            # Include source locations
    enable_caching=True,              # Performance optimization
    output_format=OutputFormat.NETWORKX
)
```

### Custom Color Palettes

```python
custom_colors = {
    "StartFunction": "#ff6b6b",      # Red for entry points
    "PyFunction": "#4ecdc4",         # Teal for functions
    "PyClass": "#45b7d1",            # Blue for classes
    "ExternalModule": "#96ceb4",     # Green for external
    "HTTP_METHOD": "#feca57",        # Yellow for HTTP methods
}

config = CallTraceConfig(color_palette=custom_colors)
```

## Output Formats

The visualization system supports multiple output formats:

- **NetworkX** (`OutputFormat.NETWORKX`) - Python NetworkX graph objects
- **JSON** (`OutputFormat.JSON`) - JSON serialization for web frontends
- **GraphML** (`OutputFormat.GRAPHML`) - Standard graph format for tools like Gephi
- **HTML** (`OutputFormat.HTML`) - Interactive HTML reports
- **PNG/SVG** (`OutputFormat.PNG`/`OutputFormat.SVG`) - Static image exports

## Integration with Existing Tools

### With Graph-Sitter Decorators

```python
import graph_sitter
from graph_sitter.adapters.visualizations import UnifiedVisualizationManager

@graph_sitter.function("analyze-call-relationships")
def analyze_calls(codebase):
    manager = UnifiedVisualizationManager()
    
    # Find main function
    main_func = codebase.get_function("main")
    
    # Create call trace
    result = manager.create_visualization(
        codebase=codebase,
        visualization_type=VisualizationType.CALL_TRACE,
        target=main_func
    )
    
    return result.to_dict()
```

### With React Frontends

```python
# Generate React-compatible data
react_data = manager.create_react_visualizations(codebase)

# Export for frontend consumption
with open("visualization_data.json", "w") as f:
    json.dump(react_data, f, indent=2)
```

## Performance Considerations

### Large Codebases

For large codebases, consider these optimizations:

```python
# Limit depth for performance
config = CallTraceConfig(
    max_depth=5,                     # Reduce depth
    ignore_external_modules=True,    # Skip external calls
    enable_caching=True,             # Enable caching
    batch_size=500                   # Process in batches
)

# Use targeted analysis instead of full codebase
target_functions = codebase.get_functions_by_pattern("main|run|start")
for func in target_functions[:10]:  # Limit to first 10
    result = visualizer.visualize(codebase, func)
```

### Memory Management

```python
# Clear visualizer state between runs
visualizer.reset()

# Use batch processing for multiple targets
batch_request = BatchVisualizationRequest(
    visualization_types=[VisualizationType.CALL_TRACE],
    targets=target_functions,
    output_formats=[OutputFormat.JSON]  # Avoid keeping graphs in memory
)
```

## Examples

See the `examples/` directory for comprehensive usage examples:

- `comprehensive_example.py` - Demonstrates all visualization types
- `batch_processing_example.py` - Shows batch processing capabilities
- `custom_configuration_example.py` - Custom configuration examples
- `web_integration_example.py` - Web frontend integration

## API Reference

### Core Classes

- `UnifiedVisualizationManager` - Main interface for all visualizations
- `CallTraceVisualizer` - Function call relationship analysis
- `DependencyTraceVisualizer` - Symbol dependency analysis
- `BlastRadiusVisualizer` - Impact radius analysis
- `MethodRelationshipsVisualizer` - Class method relationship analysis

### Configuration Classes

- `VisualizationConfig` - Base configuration
- `CallTraceConfig` - Call trace specific configuration
- `DependencyTraceConfig` - Dependency analysis configuration
- `BlastRadiusConfig` - Blast radius analysis configuration
- `MethodRelationshipsConfig` - Method relationship configuration

### Result Classes

- `VisualizationResult` - Contains graph, metadata, and configuration
- `BatchVisualizationResult` - Results from batch processing

### Enums

- `VisualizationType` - Available visualization types
- `OutputFormat` - Supported output formats

## Contributing

To add new visualization types:

1. Create a new visualizer class inheriting from `BaseVisualizationAdapter`
2. Implement the required abstract methods
3. Add configuration class if needed
4. Register in `UnifiedVisualizationManager`
5. Add tests and documentation

## License

This visualization system is part of the graph-sitter project and follows the same license terms.

