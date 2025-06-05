#!/usr/bin/env python3
"""
Example: Comprehensive React Visualization Generation

This example demonstrates how to use the React visualization system
to create interactive visualizations for all types of codebase analysis.
"""

import sys
import os
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter import Codebase
from graph_sitter.adapters.visualizations.react_visualizations import (
    ReactVisualizationGenerator,
    create_react_visualizations,
    generate_function_blast_radius,
    generate_issue_dashboard
)

def main():
    """
    Generate comprehensive React visualizations for a codebase.
    """
    print("🚀 Generating Comprehensive React Visualizations...")
    
    # Initialize codebase (replace with your target repository)
    print("📁 Loading codebase...")
    try:
        # Example: Load the current graph-sitter codebase
        codebase = Codebase.from_directory(".")
        print(f"✅ Loaded codebase with {len(list(codebase.files))} files")
    except Exception as e:
        print(f"❌ Error loading codebase: {e}")
        return
    
    # Generate all visualization types
    print("🎨 Generating visualizations...")
    
    visualization_types = [
        'class_method_relationships',
        'function_blast_radius', 
        'symbol_dependencies',
        'call_graph',
        'dependency_graph',
        'complexity_heatmap',
        'issue_dashboard',
        'metrics_overview'
    ]
    
    try:
        # Create comprehensive visualizations
        result = create_react_visualizations(
            codebase=codebase,
            visualization_types=visualization_types
        )
        
        print(f"✅ Generated {result['metadata']['total_visualizations']} visualizations")
        
        # Create output directory
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save visualization data as JSON
        print("💾 Saving visualization data...")
        for viz_type, component_data in result['components'].items():
            # Save JSON data
            json_file = output_dir / f"{viz_type}_data.json"
            with open(json_file, 'w') as f:
                json.dump(component_data['data'], f, indent=2, default=str)
            
            # Save React component
            component_file = output_dir / f"{viz_type.title().replace('_', '')}Visualization.jsx"
            with open(component_file, 'w') as f:
                f.write(component_data['component_code'])
            
            print(f"  📄 {viz_type}: {json_file} & {component_file}")
        
        # Save dashboard component
        dashboard_file = output_dir / "CodebaseDashboard.jsx"
        with open(dashboard_file, 'w') as f:
            f.write(result['dashboard_component'])
        print(f"  🎛️  Dashboard: {dashboard_file}")
        
        # Save metadata
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(result['metadata'], f, indent=2, default=str)
        print(f"  📊 Metadata: {metadata_file}")
        
        # Generate usage instructions
        readme_content = generate_usage_readme(result)
        readme_file = output_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        print(f"  📖 Instructions: {readme_file}")
        
        print("\n🎉 React visualizations generated successfully!")
        print(f"📂 Output directory: {output_dir.absolute()}")
        print("\n📋 Generated files:")
        for file in sorted(output_dir.iterdir()):
            print(f"  - {file.name}")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"  - Total visualizations: {result['metadata']['total_visualizations']}")
        print(f"  - Codebase files: {result['metadata']['codebase_summary']['files']}")
        print(f"  - Functions analyzed: {result['metadata']['codebase_summary']['functions']}")
        print(f"  - Classes analyzed: {result['metadata']['codebase_summary']['classes']}")
        
    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

def generate_usage_readme(result):
    """Generate README with usage instructions"""
    return f"""# Codebase React Visualizations

Generated on: {result['metadata']['generated_at']}

## Overview

This directory contains comprehensive React visualizations for codebase analysis, including:

{chr(10).join(f"- **{viz_type.replace('_', ' ').title()}**: Interactive visualization for {viz_type}" for viz_type in result['components'].keys())}

## Files Generated

### Visualization Components
{chr(10).join(f"- `{viz_type.title().replace('_', '')}Visualization.jsx`: React component for {viz_type}" for viz_type in result['components'].keys())}

### Data Files
{chr(10).join(f"- `{viz_type}_data.json`: Visualization data for {viz_type}" for viz_type in result['components'].keys())}

### Dashboard
- `CodebaseDashboard.jsx`: Main dashboard component with tabs for all visualizations

## Usage

### 1. Install Dependencies

```bash
npm install react vis-network
```

### 2. Import and Use Components

```jsx
import React from 'react';
import CodebaseDashboard from './CodebaseDashboard';
import visualizationData from './visualization_data.json';

function App() {{
  return (
    <div className="App">
      <CodebaseDashboard visualizationData={{visualizationData}} />
    </div>
  );
}}

export default App;
```

### 3. Individual Component Usage

```jsx
import ClassMethodRelationshipsVisualization from './ClassMethodRelationshipsVisualization';
import classMethodData from './class_method_relationships_data.json';

function MyComponent() {{
  return (
    <ClassMethodRelationshipsVisualization 
      data={{classMethodData}}
      options={{{{
        // Custom vis-network options
        physics: {{ enabled: true }}
      }}}}
    />
  );
}}
```

## Visualization Types

### 1. Class Method Relationships
- **Purpose**: Visualize class hierarchies and method call relationships
- **Based on**: NetworkX graph with hierarchical layout
- **Interactions**: Click nodes to see method details

### 2. Function Blast Radius  
- **Purpose**: Show impact analysis - what would be affected by changes
- **Based on**: Force-directed graph centered on target function
- **Interactions**: Hover to see usage details

### 3. Symbol Dependencies
- **Purpose**: Visualize dependency chains and import relationships
- **Based on**: Hierarchical layout showing dependency flow
- **Interactions**: Click to explore dependency paths

### 4. Call Graph
- **Purpose**: Overall function call relationships across codebase
- **Based on**: Force-directed layout with function nodes
- **Interactions**: Filter by complexity or file

### 5. Dependency Graph
- **Purpose**: File-level import and dependency relationships
- **Based on**: Circular layout showing file connections
- **Interactions**: Click files to see import details

### 6. Complexity Heatmap
- **Purpose**: Visual representation of code complexity
- **Based on**: Grid layout with color-coded complexity
- **Interactions**: Hover for complexity metrics

### 7. Issue Dashboard
- **Purpose**: Visual representation of code issues and problems
- **Based on**: Grouped layout by severity
- **Interactions**: Click issues for details and recommendations

### 8. Metrics Overview
- **Purpose**: High-level codebase metrics and statistics
- **Based on**: Circular layout with metric nodes
- **Interactions**: Click metrics for detailed breakdowns

## Customization

### Layout Options
Each visualization supports different layout algorithms:
- `hierarchical`: Top-down or left-right tree layout
- `force`: Physics-based force-directed layout  
- `circular`: Circular arrangement of nodes
- `grid`: Grid-based arrangement

### Color Scheme
The visualizations use a consistent color palette:
- **Blue (#9CDCFE)**: Entry points and starting nodes
- **Purple (#A277FF)**: Functions and methods
- **Orange (#FFCA85)**: Classes and HTTP methods
- **Pink (#F694FF)**: External modules and imports
- **Red (#FF6B6B)**: Critical issues
- **Yellow (#FFD93D)**: Warnings
- **Green (#6BCF7F)**: Success/info states

### Event Handlers
All components support click and hover events:
```jsx
<VisualizationComponent 
  data={{data}}
  onNodeClick={{(node) => console.log('Clicked:', node)}}
  onEdgeClick={{(edge) => console.log('Edge:', edge)}}
/>
```

## Codebase Statistics

- **Total Files**: {result['metadata']['codebase_summary']['files']}
- **Total Functions**: {result['metadata']['codebase_summary']['functions']}  
- **Total Classes**: {result['metadata']['codebase_summary']['classes']}
- **Visualizations Generated**: {result['metadata']['total_visualizations']}

## Technical Details

### Dependencies
- **React**: ^18.0.0
- **vis-network**: ^9.0.0

### Browser Support
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Performance
- Optimized for codebases up to 10,000 functions
- Lazy loading for large datasets
- Configurable depth limits for complex graphs

## Troubleshooting

### Large Codebases
If visualizations are slow with large codebases:
1. Reduce `max_depth` parameter
2. Filter by file patterns
3. Use pagination for large datasets

### Memory Issues
For memory-intensive visualizations:
1. Enable `ignore_external_modules`
2. Limit visualization types
3. Use incremental loading

## Support

For issues or questions about these visualizations:
1. Check the console for error messages
2. Verify data format matches expected schema
3. Ensure all dependencies are installed
4. Check browser compatibility

---

Generated by Graph-Sitter React Visualization System
"""

if __name__ == "__main__":
    main()
