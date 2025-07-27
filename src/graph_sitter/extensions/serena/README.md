# Advanced Serena Integration for Graph-Sitter

This module provides comprehensive integration with Serena's codebase knowledge features, enabling advanced error analysis, context inclusion, semantic understanding, and intelligent code insights.

## 🚀 Features

### 🧠 Knowledge Extraction
- **Semantic Analysis**: Deep understanding of code semantics, types, and intent
- **Architectural Insights**: Design patterns, coupling analysis, and architectural smells
- **Dependency Analysis**: Comprehensive dependency tracking and impact assessment
- **Knowledge Graphs**: Visual representation of codebase relationships and structure

### 🐛 Advanced Error Analysis
- **Contextual Error Analysis**: Multi-layered context analysis for comprehensive error understanding
- **Intelligent Fix Suggestions**: AI-powered recommendations with implementation guidance
- **Error Clustering**: Automatic grouping of related errors for efficient resolution
- **Impact Assessment**: Understanding the scope and risk of errors

### 🎯 Context Inclusion
- **Multi-Level Context**: Immediate, function, class, file, module, and project-level context
- **Relationship Mapping**: Symbol relationships, dependency chains, and usage patterns
- **Architectural Context**: Understanding code within its architectural framework
- **Ecosystem Knowledge**: Leveraging broader ecosystem patterns and best practices

### 📊 Visualization & Insights
- **Code Visualizations**: Syntax highlighting, dependency graphs, control flow charts
- **Error Visualizations**: Impact charts, relationship diagrams, and pattern analysis
- **Knowledge Insights**: Semantic layers, architectural patterns, and design recommendations

## 🛠️ Installation

```bash
pip install graph-sitter[serena]
```

## 📖 Quick Start

### Basic Usage

```python
import asyncio
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena import create_serena_api

async def main():
    # Load your codebase
    codebase = Codebase.from_directory("path/to/your/project")
    
    # Create advanced API instance
    api = await create_serena_api(codebase, enable_serena=True)
    
    try:
        # Extract comprehensive knowledge
        knowledge = await api.extract_knowledge(
            file_path="src/main.py",
            symbol_name="main_function",
            include_context=True
        )
        
        # Analyze error with full context
        error_info = {
            "id": "error_001",
            "type": "complexity_issue",
            "severity": "high",
            "file_path": "src/main.py",
            "line_number": 42,
            "message": "High cyclomatic complexity"
        }
        
        analysis = await api.analyze_error_comprehensive(error_info)
        
        # Build knowledge graph
        graph = await api.build_knowledge_graph(include_semantic_layers=True)
        
        print(f"Knowledge extracted: {len(knowledge)} insights")
        print(f"Error analysis: {analysis['error_overview']['basic_info']['type']}")
        print(f"Knowledge graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
        
    finally:
        await api.shutdown()

asyncio.run(main())
```

### Quick Functions

```python
from graph_sitter.extensions.serena import quick_error_analysis, quick_knowledge_extraction

# Quick error analysis
error_analysis = await quick_error_analysis(codebase, error_info)

# Quick knowledge extraction
knowledge = await quick_knowledge_extraction(codebase, "src/main.py", "function_name")
```

## 🔧 API Reference

### SerenaAdvancedAPI

The main API class providing comprehensive Serena integration.

#### Knowledge Extraction

```python
# Extract comprehensive knowledge about a code element
knowledge = await api.extract_knowledge(
    file_path="src/module.py",
    symbol_name="MyClass",
    line_number=100,
    include_context=True,
    extractors=["semantic", "architectural", "dependency"]
)

# Build knowledge graph
graph = await api.build_knowledge_graph(
    include_semantic_layers=True,
    include_metrics=True
)

# Search semantic patterns
results = await api.search_semantic_patterns(
    query="factory pattern",
    pattern_type="design_pattern",
    max_results=10
)
```

#### Error Analysis

```python
# Comprehensive error analysis
analysis = await api.analyze_error_comprehensive(
    error_info=error_data,
    include_visualizations=True,
    include_suggestions=True
)

# Error context analysis
context = await api.analyze_error_context(
    error_info=error_data,
    context_depth=3
)

# Cluster related errors
clusters = await api.cluster_errors(
    errors=error_list,
    cluster_types=["file_based", "pattern_based"]
)
```

#### Context Analysis

```python
# Symbol context analysis
context = await api.analyze_symbol_context(
    file_path="src/module.py",
    symbol_name="function_name",
    symbol_type="function",
    include_relationships=True
)

# File context analysis
file_context = await api.analyze_file_context(
    file_path="src/module.py",
    include_dependencies=True,
    include_metrics=True
)
```

#### Relationship Analysis

```python
# Dependency analysis
dependencies = await api.analyze_dependencies(
    file_path="src/module.py",
    symbol_name="MyClass",
    include_transitive=True,
    max_depth=5
)

# Find related symbols
related = await api.find_related_symbols(
    file_path="src/module.py",
    symbol_name="function_name",
    relation_types=["calls", "uses", "inherits"],
    max_results=20
)
```

#### Architectural Analysis

```python
# Project architecture analysis
architecture = await api.analyze_architecture(
    scope="project",
    include_patterns=True,
    include_metrics=True
)
```

## 🏗️ Architecture

### Core Components

1. **AdvancedKnowledgeIntegration**: Main knowledge extraction and integration system
2. **AdvancedContextEngine**: Multi-layered context analysis engine
3. **AdvancedErrorViewer**: Comprehensive error viewing and visualization
4. **SerenaAdvancedAPI**: Unified API layer for all functionality

### Knowledge Extractors

- **SemanticKnowledgeExtractor**: Semantic analysis using Serena's capabilities
- **ArchitecturalKnowledgeExtractor**: Architectural patterns and design analysis
- **DependencyKnowledgeExtractor**: Dependency tracking and impact analysis

### Data Models

- **KnowledgeContext**: Comprehensive context for knowledge extraction
- **KnowledgeGraph**: Graph representation of codebase understanding
- **ContextualError**: Enhanced error with comprehensive context
- **ErrorVisualization**: Error visualization data and metadata

## 🎨 Visualization Types

### Code Visualizations
- **Code Highlighting**: Syntax-highlighted code with annotations
- **Dependency Graphs**: Visual representation of dependencies
- **Control Flow Charts**: Function control flow visualization
- **Impact Charts**: Error impact and scope visualization

### Knowledge Visualizations
- **Knowledge Graphs**: Interactive codebase relationship graphs
- **Semantic Layers**: Semantic similarity and clustering visualizations
- **Architectural Diagrams**: Design pattern and architectural structure views

## 🔍 Error Analysis Features

### Context Layers
1. **Immediate Context**: Surrounding code lines and immediate environment
2. **Function Context**: Function-level analysis including complexity and parameters
3. **Class Context**: Class-level analysis including methods and inheritance
4. **File Context**: File-level metrics and symbol analysis
5. **Module Context**: Module-level dependencies and relationships
6. **Project Context**: Project-wide architectural patterns and health

### Fix Suggestions
- **Immediate Fixes**: Critical issues requiring immediate attention
- **Short-term Fixes**: High-priority improvements
- **Long-term Improvements**: Architectural and design enhancements
- **Code Examples**: Concrete implementation examples
- **Best Practices**: Industry best practices and recommendations

### Error Clustering
- **File-based Clustering**: Errors grouped by file location
- **Function-based Clustering**: Errors within the same function
- **Pattern-based Clustering**: Errors with similar patterns or types
- **Priority Scoring**: Automatic priority calculation for clusters

## 🧪 Testing

Run the comprehensive demo to see all features in action:

```bash
python examples/advanced_serena_integration_demo.py
```

## 🔧 Configuration

### API Configuration

```python
api = SerenaAdvancedAPI(
    codebase=codebase,
    enable_serena=True,        # Enable Serena MCP integration
    enable_caching=True,       # Enable result caching
    max_workers=4              # Parallel processing workers
)
```

### Error Viewer Configuration

```python
from graph_sitter.extensions.serena import ErrorViewConfig

config = ErrorViewConfig(
    include_context=True,
    include_suggestions=True,
    include_related_errors=True,
    include_code_examples=True,
    max_context_depth=3,
    max_suggestions=10,
    max_related_errors=5
)

error_viewer = AdvancedErrorViewer(codebase, config=config)
```

## 🚀 Performance

### Caching
- **Knowledge Cache**: Caches extracted knowledge for faster repeated access
- **Context Cache**: Caches context analysis results
- **Graph Cache**: Caches knowledge graph construction

### Parallel Processing
- **Multi-threaded Extraction**: Parallel knowledge extraction using multiple workers
- **Async Operations**: Asynchronous processing for better performance
- **Batch Processing**: Efficient batch processing for large codebases

### Memory Management
- **Lazy Loading**: Load knowledge on-demand
- **Cache Limits**: Configurable cache size limits
- **Resource Cleanup**: Automatic resource cleanup and garbage collection

## 🔌 Integration

### Serena MCP Integration
The advanced integration leverages Serena's Model Context Protocol (MCP) server for enhanced capabilities:

- **Semantic Tools**: Advanced semantic analysis and understanding
- **Code Intelligence**: Intelligent code analysis and insights
- **Symbol Intelligence**: Deep symbol relationship analysis
- **Semantic Search**: Pattern matching and similarity search

### Fallback Implementation
When Serena MCP is not available, the system provides fallback implementations:

- **Basic Semantic Analysis**: Simple semantic analysis without Serena
- **Pattern Detection**: Basic architectural pattern detection
- **Dependency Analysis**: Standard dependency tracking
- **Context Analysis**: Multi-layered context without advanced insights

## 📊 Metrics and Analytics

### Knowledge Metrics
- **Extraction Coverage**: Percentage of codebase analyzed
- **Knowledge Depth**: Depth of analysis performed
- **Relationship Density**: Density of discovered relationships
- **Pattern Coverage**: Architectural patterns detected

### Error Metrics
- **Error Distribution**: Distribution of errors by type and severity
- **Context Completeness**: Completeness of context analysis
- **Fix Success Rate**: Success rate of applied fixes
- **Resolution Time**: Time to resolve clustered errors

### Performance Metrics
- **Extraction Time**: Time taken for knowledge extraction
- **Analysis Throughput**: Number of elements analyzed per second
- **Cache Hit Rate**: Effectiveness of caching system
- **Memory Usage**: Memory consumption during analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Run the demo for examples
- Review the API reference

## 🔄 Version History

### v2.0.0 (Current)
- Advanced Serena integration with comprehensive knowledge extraction
- Multi-layered context analysis and error viewing
- Knowledge graph construction and visualization
- Architectural pattern detection and analysis
- Enhanced API with async support and caching

### v1.0.0
- Basic Serena integration
- Simple error analysis
- Basic context inclusion

