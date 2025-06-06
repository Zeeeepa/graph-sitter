# 🚀 Enhanced Graph-Sitter Codebase Analysis Tool

This enhanced version of the codebase analysis tool leverages graph-sitter's pre-computed graph elements and advanced features for comprehensive code analysis.

## 🌟 New Features

### 1. **Pre-computed Graph Element Access**
Access all codebase elements through graph-sitter's optimized graph structure:

```python
# Access pre-computed graph elements
codebase.functions    # All functions in codebase
codebase.classes      # All classes
codebase.imports      # All import statements
codebase.files        # All files
codebase.symbols      # All symbols
codebase.external_modules  # External dependencies
```

### 2. **Advanced Function Analysis**
Enhanced function metrics using graph-sitter:

```python
for function in codebase.functions:
    function.usages           # All usage sites
    function.call_sites       # All call locations
    function.dependencies     # Function dependencies
    function.function_calls   # Functions this function calls
    function.parameters       # Function parameters
    function.return_statements # Return statements
    function.decorators       # Function decorators
    function.is_async         # Async function detection
    function.is_generator     # Generator function detection
```

### 3. **Class Hierarchy Analysis**
Comprehensive class analysis:

```python
for cls in codebase.classes:
    cls.superclasses         # Parent classes
    cls.subclasses          # Child classes
    cls.methods             # Class methods
    cls.attributes          # Class attributes
    cls.decorators          # Class decorators
    cls.usages              # Class usage sites
    cls.dependencies        # Class dependencies
    cls.is_abstract         # Abstract class detection
```

### 4. **Import Relationship Analysis**
Advanced import analysis and loop detection:

```python
for file in codebase.files:
    file.imports            # Outbound imports
    file.inbound_imports    # Files that import this file
    file.symbols            # Symbols defined in file
    file.external_modules   # External dependencies
```

### 5. **Training Data Generation for LLMs**
Generate structured training data for machine learning models:

```bash
python analyze_codebase_enhanced.py . --training-data --output training.json
```

Features:
- Function implementation extraction
- Dependency context analysis
- Usage pattern identification
- Metadata generation for ML training

### 6. **Import Loop Detection**
Detect and analyze circular import dependencies:

```bash
python analyze_codebase_enhanced.py . --import-loops --output loops.json
```

Features:
- Static vs dynamic import detection
- Severity classification (critical/warning/info)
- Strongly connected component analysis
- Fix recommendations

### 7. **Dead Code Detection**
Identify unused functions, classes, and variables:

```bash
python analyze_codebase_enhanced.py . --dead-code --output dead_code.json
```

Features:
- Usage-based analysis
- Confidence scoring
- Safe removal recommendations
- Special method exclusions

### 8. **Graph Structure Analysis**
Comprehensive graph analysis:

```bash
python analyze_codebase_enhanced.py . --graph-analysis --output graph.json
```

Features:
- Node and edge counting
- Edge type classification
- Connectivity analysis
- Architectural insights

### 9. **Enhanced Metrics**
Advanced function and class metrics:

```bash
python analyze_codebase_enhanced.py . --enhanced-metrics --output metrics.json
```

Features:
- Graph-sitter enhanced complexity metrics
- Dependency analysis
- Usage pattern identification
- Inheritance depth calculation

### 10. **Advanced Configuration**
Use enhanced CodebaseConfig options:

```bash
python analyze_codebase_enhanced.py . --advanced-config --graph-analysis
```

Configuration options:
- Method usage resolution
- Generic type resolution
- Full range indexing
- Lazy graph construction
- Debug and validation modes

## 📋 Usage Examples

### Basic Enhanced Analysis
```bash
# Comprehensive enhanced analysis
python analyze_codebase_enhanced.py /path/to/code --enhanced-metrics --output results.json

# Remote repository analysis
python analyze_codebase_enhanced.py --repo fastapi/fastapi --training-data --output fastapi_training.json
```

### Specific Analysis Types
```bash
# Generate training data for LLMs
python analyze_codebase_enhanced.py . --training-data --output training.json

# Detect import loops
python analyze_codebase_enhanced.py . --import-loops --visualize-graph

# Find dead code
python analyze_codebase_enhanced.py . --dead-code --output dead_code.json

# Analyze graph structure
python analyze_codebase_enhanced.py . --graph-analysis --advanced-config

# Enhanced function/class metrics
python analyze_codebase_enhanced.py . --enhanced-metrics --output metrics.json
```

### Combined Analysis
```bash
# Run multiple analyses together
python analyze_codebase_enhanced.py . \
    --training-data \
    --import-loops \
    --dead-code \
    --enhanced-metrics \
    --advanced-config \
    --output comprehensive_analysis.json
```

## 🔧 Configuration Options

### Advanced CodebaseConfig
The enhanced analyzer supports advanced configuration:

```python
config = CodebaseConfig(
    # Performance optimizations
    method_usages=True,          # Enable method usage resolution
    generics=True,               # Enable generic type resolution
    sync_enabled=True,           # Enable graph sync during commits
    
    # Advanced analysis
    full_range_index=True,       # Full range-to-node mapping
    py_resolve_syspath=True,     # Resolve sys.path imports
    
    # Experimental features
    exp_lazy_graph=False,        # Lazy graph construction
)
```

### Command Line Options
```bash
# Enhanced analysis options
--training-data          # Generate training data for LLMs
--import-loops          # Detect circular import dependencies
--dead-code             # Detect unused code
--graph-analysis        # Perform graph structure analysis
--enhanced-metrics      # Use enhanced function/class metrics
--visualize-graph       # Generate graph visualizations
--advanced-config       # Use advanced CodebaseConfig

# Traditional options (still supported)
--comprehensive         # Traditional comprehensive analysis
--tree-sitter          # Tree-sitter specific features
--visualize            # Traditional visualizations
--export-html          # HTML export
```

## 📊 Output Formats

### Training Data Output
```json
{
  "training_data": [
    {
      "implementation": {
        "source": "def process_data(input: str) -> dict: ...",
        "filepath": "src/processor.py"
      },
      "dependencies": [
        {
          "source": "def validate_input(data: str) -> bool: ...",
          "filepath": "src/validators.py",
          "name": "validate_input",
          "type": "Function"
        }
      ],
      "usages": [
        {
          "source": "result = process_data(user_input)",
          "filepath": "src/api.py",
          "name": "api_handler",
          "type": "Function"
        }
      ],
      "metadata": {
        "name": "process_data",
        "line_start": 15,
        "line_end": 25,
        "is_async": false,
        "parameter_count": 1
      }
    }
  ],
  "metadata": {
    "total_functions": 150,
    "processed_functions": 120,
    "coverage_percentage": 80.0,
    "avg_dependencies_per_function": 2.5,
    "avg_usages_per_function": 3.2
  }
}
```

### Import Loop Output
```json
{
  "import_loops": [
    {
      "files": ["src/module_a.py", "src/module_b.py"],
      "loop_type": "static",
      "severity": "warning",
      "imports": [
        {
          "import_statement": "from module_b import helper",
          "is_dynamic": false,
          "line_number": 5
        }
      ]
    }
  ],
  "summary": {
    "total_loops": 3,
    "critical_loops": 1,
    "warning_loops": 2,
    "info_loops": 0
  },
  "recommendations": [
    "🔄 Consider moving shared code to separate modules",
    "💡 Use lazy imports where appropriate"
  ]
}
```

### Dead Code Output
```json
{
  "dead_code_items": [
    {
      "type": "function",
      "name": "unused_helper",
      "file_path": "src/utils.py",
      "line_start": 45,
      "line_end": 52,
      "reason": "No usages found",
      "confidence": 0.8
    }
  ],
  "summary": {
    "total_dead_code_items": 15,
    "dead_functions": 10,
    "dead_classes": 3,
    "dead_variables": 2
  },
  "recommendations": [
    "🗑️ 12 high-confidence dead code items can be safely removed",
    "🔍 Review dead code items before removal - some may be used dynamically"
  ]
}
```

## 🎯 Integration with Existing Tools

The enhanced analyzer is fully compatible with the existing analyze_codebase.py functionality:

- All existing command line options work
- Traditional analysis modes are preserved
- Enhanced features are additive
- Backward compatibility maintained

## 🚀 Performance Optimizations

### Lazy Graph Construction
```bash
python analyze_codebase_enhanced.py . --advanced-config --graph-analysis
```

### Incremental Analysis
The enhanced analyzer supports incremental analysis for large codebases:
- Pre-computed graph elements for fast access
- Optimized dependency resolution
- Efficient memory usage

### Caching
- Graph structure caching
- Symbol resolution caching
- Import relationship caching

## 🔍 Advanced Use Cases

### 1. Code Quality Assessment
```bash
# Comprehensive quality analysis
python analyze_codebase_enhanced.py . \
    --enhanced-metrics \
    --dead-code \
    --import-loops \
    --advanced-config
```

### 2. ML Training Data Generation
```bash
# Generate training data for code completion models
python analyze_codebase_enhanced.py . \
    --training-data \
    --enhanced-metrics \
    --output ml_training_data.json
```

### 3. Architecture Analysis
```bash
# Analyze codebase architecture
python analyze_codebase_enhanced.py . \
    --graph-analysis \
    --import-loops \
    --visualize-graph \
    --advanced-config
```

### 4. Refactoring Support
```bash
# Identify refactoring opportunities
python analyze_codebase_enhanced.py . \
    --dead-code \
    --import-loops \
    --enhanced-metrics \
    --output refactoring_analysis.json
```

## 📚 Dependencies

### Required
- `graph-sitter` - Core graph-sitter library
- `networkx` - For import loop detection and graph analysis

### Optional
- `graphviz` - For graph visualizations
- `plotly` - For interactive charts
- `matplotlib` - For static visualizations

## 🤝 Contributing

The enhanced analyzer is designed to be extensible:

1. Add new analysis functions to `graph_sitter_enhancements.py`
2. Extend the `EnhancedCodebaseAnalyzer` class
3. Add new command line options
4. Update documentation

## 📄 License

Same license as the main graph-sitter project.

