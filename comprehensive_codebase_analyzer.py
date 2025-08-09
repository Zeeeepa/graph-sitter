#!/usr/bin/env python3
"""
Comprehensive Codebase Analyzer
A unified tool that executes all codebase analysis functions and generates a complete report.
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import networkx as nx

# Import graph_sitter components
import graph_sitter
from graph_sitter import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

# Configuration constants
MAX_DEPTH = 5
IGNORE_EXTERNAL_MODULE_CALLS = True
IGNORE_CLASS_CALLS = False

# Color palette for visualizations
COLOR_PALETTE = {
    "Function": "#4CAF50",
    "Class": "#2196F3", 
    "ExternalModule": "#FF9800",
    "StartFunction": "#F44336",
    "HTTP_METHOD": "#9C27B0",
    "DeadCode": "#795548"
}

# HTTP methods to highlight
HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]


class ComprehensiveCodebaseAnalyzer:
    """Main analyzer class that orchestrates all analysis functions."""
    
    def __init__(self, codebase_path: str):
        """Initialize the analyzer with a codebase path."""
        self.codebase_path = codebase_path
        self.codebase = None
        self.analysis_results = {}
        self.graphs = {}
        self.timestamp = datetime.now().isoformat()
        
    def load_codebase(self):
        """Load the codebase for analysis."""
        print(f"🔄 Loading codebase from: {self.codebase_path}")
        
        if self.codebase_path.startswith(('http://', 'https://', 'git@')):
            # Remote repository
            self.codebase = Codebase.from_repo(self.codebase_path)
        else:
            # Local repository
            self.codebase = Codebase(self.codebase_path)
            
        print(f"✅ Codebase loaded successfully")
        
    def analyze_basic_stats(self) -> Dict[str, Any]:
        """Analyze basic codebase statistics."""
        print("\n🔍 Analyzing Basic Statistics...")
        
        stats = {
            "total_files": len(self.codebase.files),
            "total_classes": len(self.codebase.classes),
            "total_functions": len(self.codebase.functions),
            "total_imports": len(self.codebase.imports),
            "lines_of_code": sum(len(file.source.splitlines()) for file in self.codebase.files)
        }
        
        print("🔍 Codebase Analysis")
        print("=" * 50)
        print(f"📁 Total Files: {stats['total_files']}")
        print(f"📚 Total Classes: {stats['total_classes']}")
        print(f"⚡ Total Functions: {stats['total_functions']}")
        print(f"🔄 Total Imports: {stats['total_imports']}")
        print(f"📝 Lines of Code: {stats['lines_of_code']}")
        
        return stats
        
    def analyze_inheritance(self) -> Dict[str, Any]:
        """Analyze class inheritance patterns."""
        print("\n🌳 Analyzing Inheritance Patterns...")
        
        inheritance_data = {
            "deepest_inheritance": None,
            "inheritance_chains": [],
            "classes_with_inheritance": 0
        }
        
        if self.codebase.classes:
            # Find class with most inheritance
            deepest_class = max(self.codebase.classes, key=lambda x: len(x.superclasses))
            
            inheritance_data["deepest_inheritance"] = {
                "class_name": deepest_class.name,
                "chain_depth": len(deepest_class.superclasses),
                "chain": [s.name for s in deepest_class.superclasses]
            }
            
            print(f"🌳 Class with most inheritance: {deepest_class.name}")
            print(f" 📊 Chain Depth: {len(deepest_class.superclasses)}")
            print(f" ⛓️ Chain: {' -> '.join(s.name for s in deepest_class.superclasses)}")
            
            # Collect all inheritance chains
            for cls in self.codebase.classes:
                if cls.superclasses:
                    inheritance_data["classes_with_inheritance"] += 1
                    inheritance_data["inheritance_chains"].append({
                        "class_name": cls.name,
                        "superclasses": [s.name for s in cls.superclasses]
                    })
        
        return inheritance_data
        
    def analyze_recursive_functions(self) -> Dict[str, Any]:
        """Find recursive functions in the codebase."""
        print("\n🔄 Analyzing Recursive Functions...")
        
        recursive_functions = []
        for func in self.codebase.functions:
            if any(call.name == func.name for call in func.function_calls):
                recursive_functions.append({
                    "name": func.name,
                    "file": func.file.filepath if func.file else "unknown",
                    "line": func.start_point[0] if func.start_point else 0
                })
        
        recursive_data = {
            "total_recursive": len(recursive_functions),
            "recursive_functions": recursive_functions[:10]  # Limit to first 10
        }
        
        if recursive_functions:
            print(f"🔄 Found {len(recursive_functions)} recursive functions:")
            for func in recursive_functions[:5]:  # Show first 5
                print(f" - {func['name']} ({func['file']})")
        else:
            print("🔄 No recursive functions found")
            
        return recursive_data
        
    def analyze_tests(self) -> Dict[str, Any]:
        """Analyze test coverage and organization."""
        print("\n🧪 Analyzing Test Coverage...")
        
        test_functions = [x for x in self.codebase.functions if x.name.startswith('test_')]
        test_classes = [x for x in self.codebase.classes if x.name.startswith('Test')]
        
        # Find files with the most tests
        file_test_counts = Counter([x.file for x in test_classes])
        top_test_files = []
        
        for file, num_tests in file_test_counts.most_common(5):
            top_test_files.append({
                "filepath": file.filepath,
                "test_classes": num_tests,
                "file_length": len(file.source.splitlines()),
                "total_functions": len(file.functions)
            })
        
        test_data = {
            "total_test_functions": len(test_functions),
            "total_test_classes": len(test_classes),
            "tests_per_file": len(test_functions) / len(self.codebase.files) if self.codebase.files else 0,
            "top_test_files": top_test_files
        }
        
        print("🧪 Test Analysis")
        print("=" * 50)
        print(f"📝 Total Test Functions: {test_data['total_test_functions']}")
        print(f"🔬 Total Test Classes: {test_data['total_test_classes']}")
        print(f"📊 Tests per File: {test_data['tests_per_file']:.1f}")
        
        if top_test_files:
            print("\n📚 Top Test Files by Class Count")
            print("-" * 50)
            for file_info in top_test_files:
                print(f"🔍 {file_info['test_classes']} test classes: {file_info['filepath']}")
                print(f" 📏 File Length: {file_info['file_length']} lines")
                print(f" 💡 Functions: {file_info['total_functions']}")
        
        return test_data
        
    def analyze_dead_code(self) -> Dict[str, Any]:
        """Identify dead code in the codebase."""
        print("\n🗑️ Analyzing Dead Code...")
        
        dead_functions = []
        dead_classes = []
        
        # Find unused functions
        for func in self.codebase.functions:
            if len(func.usages) == 0:
                dead_functions.append({
                    "name": func.name,
                    "file": func.file.filepath if func.file else "unknown",
                    "line": func.start_point[0] if func.start_point else 0,
                    "type": "function"
                })
                print(f'🗑️ Dead function: {func.name}')
        
        # Find unused classes
        for cls in self.codebase.classes:
            if len(cls.usages) == 0:
                dead_classes.append({
                    "name": cls.name,
                    "file": cls.file.filepath if cls.file else "unknown",
                    "line": cls.start_point[0] if cls.start_point else 0,
                    "type": "class"
                })
                print(f'🗑️ Dead class: {cls.name}')
        
        dead_code_data = {
            "total_dead_functions": len(dead_functions),
            "total_dead_classes": len(dead_classes),
            "dead_functions": dead_functions,
            "dead_classes": dead_classes,
            "dead_code_locations": dead_functions + dead_classes
        }
        
        print(f"🗑️ Found {len(dead_functions)} dead functions and {len(dead_classes)} dead classes")
        
        return dead_code_data
        
    def analyze_imports(self) -> Dict[str, Any]:
        """Analyze import relationships."""
        print("\n📦 Analyzing Import Relationships...")
        
        import_data = {
            "total_imports": len(self.codebase.imports),
            "external_imports": 0,
            "internal_imports": 0,
            "import_graph": {},
            "most_imported_files": []
        }
        
        # Count import types
        for imp in self.codebase.imports:
            if isinstance(imp.imported_symbol, ExternalModule):
                import_data["external_imports"] += 1
            else:
                import_data["internal_imports"] += 1
        
        # Build import relationships
        file_import_counts = Counter()
        for file in self.codebase.files:
            inbound_count = len(file.inbound_imports)
            if inbound_count > 0:
                file_import_counts[file.filepath] = inbound_count
                
        import_data["most_imported_files"] = [
            {"file": filepath, "import_count": count}
            for filepath, count in file_import_counts.most_common(10)
        ]
        
        print(f"📦 Total Imports: {import_data['total_imports']}")
        print(f"🌐 External Imports: {import_data['external_imports']}")
        print(f"🏠 Internal Imports: {import_data['internal_imports']}")
        
        return import_data
        
    def analyze_type_coverage(self) -> Dict[str, Any]:
        """Analyze type annotation coverage."""
        print("\n🏷️ Analyzing Type Coverage...")
        
        # Initialize counters
        total_parameters = 0
        typed_parameters = 0
        total_functions = 0
        typed_returns = 0
        total_attributes = 0
        typed_attributes = 0
        
        # Count parameter and return type coverage
        for function in self.codebase.functions:
            # Count parameters
            total_parameters += len(function.parameters)
            typed_parameters += sum(1 for param in function.parameters if hasattr(param, 'is_typed') and param.is_typed)
            
            # Count return types
            total_functions += 1
            if hasattr(function, 'return_type') and function.return_type and hasattr(function.return_type, 'is_typed') and function.return_type.is_typed:
                typed_returns += 1
        
        # Count class attribute coverage
        for cls in self.codebase.classes:
            if hasattr(cls, 'attributes'):
                for attr in cls.attributes:
                    total_attributes += 1
                    if hasattr(attr, 'is_typed') and attr.is_typed:
                        typed_attributes += 1
        
        # Calculate percentages
        param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
        return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
        attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0
        
        type_data = {
            "parameter_coverage": {
                "percentage": param_percentage,
                "typed": typed_parameters,
                "total": total_parameters
            },
            "return_type_coverage": {
                "percentage": return_percentage,
                "typed": typed_returns,
                "total": total_functions
            },
            "attribute_coverage": {
                "percentage": attr_percentage,
                "typed": typed_attributes,
                "total": total_attributes
            }
        }
        
        print("🏷️ Type Coverage Analysis")
        print("---------------------")
        print(f"Parameters: {param_percentage:.1f}% ({typed_parameters}/{total_parameters} typed)")
        print(f"Return types: {return_percentage:.1f}% ({typed_returns}/{total_functions} typed)")
        print(f"Class attributes: {attr_percentage:.1f}% ({typed_attributes}/{total_attributes} typed)")
        
        return type_data
        
    def create_call_graph(self, target_function_name: Optional[str] = None) -> nx.DiGraph:
        """Create a call graph for the codebase."""
        print("\n📊 Creating Call Graph...")
        
        G = nx.DiGraph()
        
        def generate_edge_meta(call) -> dict:
            """Generate metadata for call graph edges."""
            return {
                "name": call.name,
                "file_path": call.filepath if hasattr(call, 'filepath') else "unknown",
                "start_point": call.start_point if hasattr(call, 'start_point') else (0, 0),
                "end_point": call.end_point if hasattr(call, 'end_point') else (0, 0),
                "symbol_name": "FunctionCall"
            }
        
        def create_downstream_call_trace(src_func, depth: int = 0):
            """Creates call graph by recursively traversing function calls."""
            if MAX_DEPTH <= depth:
                return
                
            if isinstance(src_func, ExternalModule):
                return
            
            for call in src_func.function_calls:
                if call.name == src_func.name:
                    continue
                    
                func = call.function_definition
                if not func:
                    continue
                    
                if isinstance(func, ExternalModule) and IGNORE_EXTERNAL_MODULE_CALLS:
                    continue
                if isinstance(func, Class) and IGNORE_CLASS_CALLS:
                    continue
                
                # Generate display name
                if isinstance(func, (Class, ExternalModule)):
                    func_name = func.name
                elif isinstance(func, Function):
                    func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name
                else:
                    func_name = str(func)
                
                # Add node and edge
                G.add_node(func, name=func_name, 
                          color=COLOR_PALETTE.get(func.__class__.__name__, "#CCCCCC"))
                G.add_edge(src_func, func, **generate_edge_meta(call))
                
                if isinstance(func, Function):
                    create_downstream_call_trace(func, depth + 1)
        
        # If target function specified, start from there
        if target_function_name:
            target_func = None
            for func in self.codebase.functions:
                if func.name == target_function_name:
                    target_func = func
                    break
            
            if target_func:
                G.add_node(target_func, name=target_func.name, 
                          color=COLOR_PALETTE["StartFunction"])
                create_downstream_call_trace(target_func)
        else:
            # Create graph for all functions (limited to prevent explosion)
            for func in list(self.codebase.functions)[:50]:  # Limit to first 50 functions
                if not G.has_node(func):
                    G.add_node(func, name=func.name, 
                              color=COLOR_PALETTE.get("Function", "#4CAF50"))
                    create_downstream_call_trace(func, 0)
        
        print(f"📊 Call graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
        
    def generate_3d_visualization_data(self) -> Dict[str, Any]:
        """Generate data for 3D visualization of codebase structure."""
        print("\n🌐 Generating 3D Visualization Data...")
        
        # Create nodes for 3D visualization
        nodes_3d = []
        edges_3d = []
        
        # Add files as nodes
        for i, file in enumerate(self.codebase.files):
            dead_code_count = sum(1 for func in file.functions if len(func.usages) == 0)
            
            nodes_3d.append({
                "id": f"file_{i}",
                "label": file.filepath,
                "type": "file",
                "size": len(file.source.splitlines()),
                "dead_code_count": dead_code_count,
                "function_count": len(file.functions),
                "class_count": len(file.classes),
                "x": i % 10,  # Simple grid layout
                "y": i // 10,
                "z": dead_code_count,  # Z-axis represents dead code
                "color": "#FF0000" if dead_code_count > 0 else "#00FF00"
            })
        
        # Add function relationships
        for i, func in enumerate(self.codebase.functions):
            if func.file:
                file_id = f"file_{list(self.codebase.files).index(func.file)}"
                
                nodes_3d.append({
                    "id": f"func_{i}",
                    "label": func.name,
                    "type": "function",
                    "size": len(func.usages),
                    "is_dead": len(func.usages) == 0,
                    "parent_file": file_id,
                    "color": "#795548" if len(func.usages) == 0 else "#4CAF50"
                })
                
                # Connect function to file
                edges_3d.append({
                    "source": file_id,
                    "target": f"func_{i}",
                    "type": "contains"
                })
        
        visualization_data = {
            "nodes": nodes_3d,
            "edges": edges_3d,
            "metadata": {
                "total_nodes": len(nodes_3d),
                "total_edges": len(edges_3d),
                "dead_code_nodes": len([n for n in nodes_3d if n.get("is_dead", False)])
            }
        }
        
        print(f"🌐 Generated 3D visualization with {len(nodes_3d)} nodes and {len(edges_3d)} edges")
        return visualization_data
        
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run all analysis functions and compile results."""
        print("🚀 Starting Comprehensive Codebase Analysis")
        print("=" * 60)
        
        # Load codebase
        self.load_codebase()
        
        # Run all analyses
        self.analysis_results = {
            "metadata": {
                "codebase_path": self.codebase_path,
                "analysis_timestamp": self.timestamp,
                "analyzer_version": "1.0.0"
            },
            "basic_stats": self.analyze_basic_stats(),
            "inheritance": self.analyze_inheritance(),
            "recursive_functions": self.analyze_recursive_functions(),
            "test_analysis": self.analyze_tests(),
            "dead_code": self.analyze_dead_code(),
            "imports": self.analyze_imports(),
            "type_coverage": self.analyze_type_coverage(),
            "visualization_3d": self.generate_3d_visualization_data()
        }
        
        # Create call graph
        self.graphs["call_graph"] = self.create_call_graph()
        
        print("\n✅ Comprehensive analysis completed!")
        return self.analysis_results
        
    def save_results(self, output_dir: str = "analysis_output"):
        """Save all analysis results to files."""
        print(f"\n💾 Saving results to {output_dir}/")
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save JSON report
        json_path = Path(output_dir) / "comprehensive_analysis_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        # Save call graph
        if "call_graph" in self.graphs:
            graph_path = Path(output_dir) / "call_graph.gexf"
            nx.write_gexf(self.graphs["call_graph"], graph_path)
        
        # Generate HTML report
        self.generate_html_report(output_dir)
        
        print(f"✅ Results saved to {output_dir}/")
        print(f"📄 JSON Report: {json_path}")
        print(f"📊 HTML Report: {output_dir}/analysis_report.html")
        
    def generate_html_report(self, output_dir: str):
        """Generate an HTML report with visualizations."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Codebase Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
        .dead-code {{ background-color: #ffebee; }}
        .good-coverage {{ background-color: #e8f5e8; }}
        h1, h2 {{ color: #333; }}
        .chart {{ width: 100%; height: 400px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🔍 Comprehensive Codebase Analysis Report</h1>
    <p><strong>Codebase:</strong> {self.analysis_results['metadata']['codebase_path']}</p>
    <p><strong>Analysis Date:</strong> {self.analysis_results['metadata']['analysis_timestamp']}</p>
    
    <div class="section">
        <h2>📊 Basic Statistics</h2>
        <div class="metric">📁 Files: {self.analysis_results['basic_stats']['total_files']}</div>
        <div class="metric">📚 Classes: {self.analysis_results['basic_stats']['total_classes']}</div>
        <div class="metric">⚡ Functions: {self.analysis_results['basic_stats']['total_functions']}</div>
        <div class="metric">🔄 Imports: {self.analysis_results['basic_stats']['total_imports']}</div>
        <div class="metric">📝 Lines of Code: {self.analysis_results['basic_stats']['lines_of_code']}</div>
    </div>
    
    <div class="section {'dead-code' if self.analysis_results['dead_code']['total_dead_functions'] > 0 else 'good-coverage'}">
        <h2>🗑️ Dead Code Analysis</h2>
        <div class="metric">Dead Functions: {self.analysis_results['dead_code']['total_dead_functions']}</div>
        <div class="metric">Dead Classes: {self.analysis_results['dead_code']['total_dead_classes']}</div>
        <div id="deadCodeChart" class="chart"></div>
    </div>
    
    <div class="section">
        <h2>🏷️ Type Coverage</h2>
        <div class="metric">Parameters: {self.analysis_results['type_coverage']['parameter_coverage']['percentage']:.1f}%</div>
        <div class="metric">Return Types: {self.analysis_results['type_coverage']['return_type_coverage']['percentage']:.1f}%</div>
        <div class="metric">Attributes: {self.analysis_results['type_coverage']['attribute_coverage']['percentage']:.1f}%</div>
        <div id="typeCoverageChart" class="chart"></div>
    </div>
    
    <div class="section">
        <h2>🧪 Test Analysis</h2>
        <div class="metric">Test Functions: {self.analysis_results['test_analysis']['total_test_functions']}</div>
        <div class="metric">Test Classes: {self.analysis_results['test_analysis']['total_test_classes']}</div>
        <div class="metric">Tests per File: {self.analysis_results['test_analysis']['tests_per_file']:.1f}</div>
    </div>
    
    <div class="section">
        <h2>🌐 3D Codebase Structure</h2>
        <p>Dead code is highlighted in red and positioned on the Z-axis based on dead code count.</p>
        <div id="codebase3D" class="chart" style="height: 600px;"></div>
    </div>
    
    <script>
        // Dead Code Chart
        var deadCodeData = [{{
            x: ['Functions', 'Classes'],
            y: [{self.analysis_results['dead_code']['total_dead_functions']}, {self.analysis_results['dead_code']['total_dead_classes']}],
            type: 'bar',
            marker: {{ color: ['#FF6B6B', '#4ECDC4'] }}
        }}];
        Plotly.newPlot('deadCodeChart', deadCodeData, {{title: 'Dead Code Distribution'}});
        
        // Type Coverage Chart
        var typeCoverageData = [{{
            labels: ['Parameters', 'Return Types', 'Attributes'],
            values: [
                {self.analysis_results['type_coverage']['parameter_coverage']['percentage']},
                {self.analysis_results['type_coverage']['return_type_coverage']['percentage']},
                {self.analysis_results['type_coverage']['attribute_coverage']['percentage']}
            ],
            type: 'pie',
            marker: {{ colors: ['#FF9999', '#66B2FF', '#99FF99'] }}
        }}];
        Plotly.newPlot('typeCoverageChart', typeCoverageData, {{title: 'Type Coverage Distribution'}});
        
        // 3D Codebase Visualization
        var nodes3D = {json.dumps(self.analysis_results['visualization_3d']['nodes'])};
        var fileNodes = nodes3D.filter(n => n.type === 'file');
        
        var trace3D = {{
            x: fileNodes.map(n => n.x),
            y: fileNodes.map(n => n.y),
            z: fileNodes.map(n => n.z),
            mode: 'markers+text',
            marker: {{
                size: fileNodes.map(n => Math.max(5, n.size / 10)),
                color: fileNodes.map(n => n.dead_code_count),
                colorscale: 'RdYlGn',
                reversescale: true,
                showscale: true,
                colorbar: {{ title: "Dead Code Count" }}
            }},
            text: fileNodes.map(n => n.label),
            textposition: 'top center',
            type: 'scatter3d'
        }};
        
        var layout3D = {{
            title: '3D Codebase Structure (Z-axis = Dead Code Count)',
            scene: {{
                xaxis: {{ title: 'File Index X' }},
                yaxis: {{ title: 'File Index Y' }},
                zaxis: {{ title: 'Dead Code Count' }}
            }}
        }};
        
        Plotly.newPlot('codebase3D', [trace3D], layout3D);
    </script>
</body>
</html>
        """
        
        html_path = Path(output_dir) / "analysis_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main function to run the comprehensive analysis."""
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_codebase_analyzer.py <codebase_path>")
        print("Example: python comprehensive_codebase_analyzer.py /path/to/repo")
        print("Example: python comprehensive_codebase_analyzer.py https://github.com/user/repo")
        sys.exit(1)
    
    codebase_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "analysis_output"
    
    # Create analyzer and run analysis
    analyzer = ComprehensiveCodebaseAnalyzer(codebase_path)
    
    try:
        # Run comprehensive analysis
        results = analyzer.run_comprehensive_analysis()
        
        # Save results
        analyzer.save_results(output_dir)
        
        print("\n🎉 Analysis Complete!")
        print(f"📊 View the interactive HTML report: {output_dir}/analysis_report.html")
        print(f"📄 JSON data available at: {output_dir}/comprehensive_analysis_report.json")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
