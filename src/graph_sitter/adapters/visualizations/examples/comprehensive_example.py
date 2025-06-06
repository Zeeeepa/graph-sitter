"""
Comprehensive example demonstrating all visualization types.

This example shows how to use the graph_sitter visualization adapters
to create different types of codebase visualizations.
"""

from pathlib import Path
from graph_sitter import Codebase
from graph_sitter.adapters.visualizations import (
    UnifiedVisualizationManager,
    VisualizationType,
    create_config,
    CallTraceConfig,
    DependencyTraceConfig,
    BlastRadiusConfig,
    MethodRelationshipsConfig,
    BatchVisualizationRequest,
    OutputFormat
)


def main():
    """Main example function demonstrating all visualization types."""
    
    # Initialize codebase (replace with your target repository)
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", language="python")
    print(f"Loaded codebase with {len(codebase.functions)} functions and {len(codebase.classes)} classes")
    
    # Create visualization manager
    manager = UnifiedVisualizationManager()
    
    # Example 1: Single visualization - Call Trace
    print("\n=== Example 1: Call Trace Visualization ===")
    if codebase.functions:
        target_function = codebase.functions[0]  # Use first function as example
        
        # Create custom configuration
        config = CallTraceConfig(
            max_depth=5,
            ignore_external_modules=True,
            include_recursive_calls=False
        )
        
        result = manager.create_visualization(
            codebase=codebase,
            visualization_type=VisualizationType.CALL_TRACE,
            target=target_function,
            config=config
        )
        
        print(f"Call trace visualization created:")
        print(f"  - Nodes: {result.graph.number_of_nodes()}")
        print(f"  - Edges: {result.graph.number_of_edges()}")
        print(f"  - Target: {target_function.name}")
    
    # Example 2: Dependency Trace
    print("\n=== Example 2: Dependency Trace Visualization ===")
    if codebase.classes:
        target_class = codebase.classes[0]  # Use first class as example
        
        config = DependencyTraceConfig(
            max_depth=3,
            include_import_dependencies=True,
            show_circular_dependencies=True,
            group_by_package=True
        )
        
        result = manager.create_visualization(
            codebase=codebase,
            visualization_type=VisualizationType.DEPENDENCY_TRACE,
            target=target_class,
            config=config
        )
        
        print(f"Dependency trace visualization created:")
        print(f"  - Nodes: {result.graph.number_of_nodes()}")
        print(f"  - Edges: {result.graph.number_of_edges()}")
        print(f"  - Target: {target_class.name}")
        
        # Check for circular dependencies
        circular_deps = result.metadata.get("circular_dependencies", [])
        if circular_deps:
            print(f"  - Found {len(circular_deps)} circular dependencies")
    
    # Example 3: Blast Radius Analysis
    print("\n=== Example 3: Blast Radius Visualization ===")
    if codebase.functions:
        # Find a function with usages for better blast radius analysis
        target_function = None
        for func in codebase.functions:
            if hasattr(func, 'usages') and len(func.usages) > 0:
                target_function = func
                break
        
        if not target_function:
            target_function = codebase.functions[0]
        
        config = BlastRadiusConfig(
            max_depth=4,
            include_test_usages=False,
            highlight_critical_paths=True,
            show_impact_metrics=True
        )
        
        result = manager.create_visualization(
            codebase=codebase,
            visualization_type=VisualizationType.BLAST_RADIUS,
            target=target_function,
            config=config
        )
        
        print(f"Blast radius visualization created:")
        print(f"  - Nodes: {result.graph.number_of_nodes()}")
        print(f"  - Edges: {result.graph.number_of_edges()}")
        print(f"  - Target: {target_function.name}")
        print(f"  - Max impact level: {result.metadata.get('max_impact_level', 0)}")
        print(f"  - Total affected symbols: {result.metadata.get('total_affected_symbols', 0)}")
    
    # Example 4: Method Relationships
    print("\n=== Example 4: Method Relationships Visualization ===")
    if codebase.classes:
        # Find a class with multiple methods
        target_class = None
        for cls in codebase.classes:
            if hasattr(cls, 'methods') and len(cls.methods) > 2:
                target_class = cls
                break
        
        if not target_class:
            target_class = codebase.classes[0]
        
        config = MethodRelationshipsConfig(
            max_depth=3,
            include_private_methods=True,
            show_inheritance_chain=True,
            highlight_overridden_methods=True
        )
        
        result = manager.create_visualization(
            codebase=codebase,
            visualization_type=VisualizationType.METHOD_RELATIONSHIPS,
            target=target_class,
            config=config
        )
        
        print(f"Method relationships visualization created:")
        print(f"  - Nodes: {result.graph.number_of_nodes()}")
        print(f"  - Edges: {result.graph.number_of_edges()}")
        print(f"  - Target: {target_class.name}")
        
        cohesion_metrics = result.metadata.get("cohesion_metrics", {})
        if cohesion_metrics:
            print(f"  - Average cohesion: {result.metadata.get('average_cohesion', 0):.2f}")
    
    # Example 5: Batch Visualization
    print("\n=== Example 5: Batch Visualization ===")
    
    # Prepare targets for batch processing
    targets = []
    if codebase.functions:
        targets.append(codebase.functions[0])
    if codebase.classes:
        targets.append(codebase.classes[0])
    
    if targets:
        # Create batch request
        batch_request = BatchVisualizationRequest(
            visualization_types=[
                VisualizationType.CALL_TRACE,
                VisualizationType.DEPENDENCY_TRACE
            ],
            targets=targets,
            output_formats=[OutputFormat.JSON, OutputFormat.GRAPHML],
            output_directory=Path("./visualization_output"),
            config_overrides={
                VisualizationType.CALL_TRACE: {"max_depth": 3},
                VisualizationType.DEPENDENCY_TRACE: {"max_depth": 2}
            }
        )
        
        # Execute batch visualization
        batch_result = manager.create_batch_visualizations(codebase, batch_request)
        
        print(f"Batch visualization completed:")
        print(f"  - Total results: {batch_result.summary['total_results']}")
        print(f"  - Total nodes: {batch_result.summary['total_nodes']}")
        print(f"  - Total edges: {batch_result.summary['total_edges']}")
        print(f"  - Errors: {len(batch_result.errors)}")
        
        if batch_result.export_paths:
            print(f"  - Exported files:")
            for result_key, paths in batch_result.export_paths.items():
                print(f"    {result_key}: {len(paths)} files")
    
    # Example 6: Comprehensive Analysis
    print("\n=== Example 6: Comprehensive Analysis ===")
    
    comprehensive_results = manager.create_comprehensive_visualization(
        codebase=codebase,
        output_directory=Path("./comprehensive_output")
    )
    
    print(f"Comprehensive analysis completed:")
    for viz_type, result in comprehensive_results.items():
        print(f"  - {viz_type}: {result.graph.number_of_nodes()} nodes, {result.graph.number_of_edges()} edges")
    
    # Example 7: Interactive HTML Report
    print("\n=== Example 7: Interactive HTML Report ===")
    
    html_path = manager.create_interactive_html_report(
        codebase=codebase,
        output_path=Path("./codebase_report.html"),
        include_types=[
            VisualizationType.CALL_TRACE,
            VisualizationType.DEPENDENCY_TRACE
        ]
    )
    
    print(f"Interactive HTML report created: {html_path}")
    
    # Example 8: Web-friendly Data Generation
    print("\n=== Example 8: Web-friendly Data Generation ===")
    
    web_data = manager.generate_visualization_data(
        codebase=codebase,
        visualization_type=VisualizationType.CALL_TRACE
    )
    
    print(f"Web-friendly data generated:")
    print(f"  - Nodes: {len(web_data['nodes'])}")
    print(f"  - Edges: {len(web_data['edges'])}")
    print(f"  - Visualization type: {web_data['visualization_type']}")
    print(f"  - Graph density: {web_data['statistics']['density']:.3f}")
    
    print("\n=== All Examples Completed Successfully! ===")


if __name__ == "__main__":
    main()

