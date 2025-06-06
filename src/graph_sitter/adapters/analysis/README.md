# Graph-Sitter Analysis Module

This module provides comprehensive codebase analysis capabilities for the graph-sitter project. All analysis features have been consolidated here for better organization and maintainability.

## Features

### Core Analysis
- **Codebase Summary**: Comprehensive statistics and overview of codebase structure
- **Symbol Analysis**: Detailed analysis of symbol usage, dependencies, and relationships
- **Dead Code Detection**: Identification of unused functions, imports, and unreachable code
- **Import Analysis**: Analysis of import relationships and circular dependency detection
- **Class Hierarchy**: Inheritance chain analysis and design pattern detection

### Advanced Analysis
- **Test Analysis**: Test coverage analysis, organization assessment, and test file management
- **AI-Powered Analysis**: Automated issue detection and intelligent code improvement suggestions
- **Training Data Generation**: LLM training data creation for code embeddings and pattern analysis

## Module Structure

```
analysis/
├── __init__.py                     # Main module exports
├── codebase_summary.py            # Codebase overview and statistics
├── symbol_analysis.py             # Symbol usage and dependency analysis
├── dead_code_detection.py         # Unused code identification
├── import_analysis.py             # Import relationship analysis
├── class_hierarchy.py             # Inheritance and design patterns
├── test_analysis.py               # Test coverage and organization
├── ai_analysis.py                 # AI-powered code analysis
├── training_data.py               # LLM training data generation
├── legacy_analyze_codebase.py     # Legacy analysis tool (moved)
├── legacy_enhanced_analyzer.py    # Legacy enhanced analyzer (moved)
└── legacy_analyze_codebase_enhanced.py  # Legacy enhanced tool (moved)
```

## Quick Start

### Basic Usage

```python
from graph_sitter.adapters.analysis import (
    get_codebase_summary,
    analyze_symbol_usage,
    find_dead_code,
    analyze_test_coverage
)

# Get codebase overview
summary = get_codebase_summary(codebase)
print(summary)

# Analyze symbol usage
symbol_analysis = analyze_symbol_usage(codebase)
print(f"Total symbols: {symbol_analysis['total_symbols']}")

# Find dead code
dead_code = find_dead_code(codebase)
print(f"Unused functions: {len(dead_code['unused_functions'])}")

# Analyze test coverage
test_analysis = analyze_test_coverage(codebase)
print(f"Coverage: {test_analysis['coverage_metrics']['coverage_percentage']:.1f}%")
```

### Advanced Analysis

```python
from graph_sitter.adapters.analysis import (
    analyze_inheritance_chains,
    detect_circular_imports,
    analyze_codebase,
    generate_training_data
)

# Analyze class hierarchies
hierarchy = analyze_inheritance_chains(codebase)
if hierarchy["deepest_inheritance"]:
    print(f"Deepest inheritance: {hierarchy['deepest_inheritance']['class']}")

# Detect circular imports
circular = detect_circular_imports(codebase)
print(f"Circular imports found: {circular['total_cycles']}")

# AI-powered analysis
ai_analysis = analyze_codebase(codebase)
print(f"Issues found: {ai_analysis['total_issues']}")

# Generate training data for LLMs
training_data = generate_training_data(codebase)
print(f"Functions processed: {training_data['metadata']['total_processed']}")
```

### Comprehensive Reports

```python
from graph_sitter.adapters.analysis import (
    print_codebase_overview,
    generate_dead_code_report,
    generate_import_report,
    generate_hierarchy_report,
    generate_test_report,
    generate_ai_analysis_report
)

# Print formatted overview
print_codebase_overview(codebase)

# Generate detailed reports
print(generate_dead_code_report(codebase))
print(generate_import_report(codebase))
print(generate_hierarchy_report(codebase))
print(generate_test_report(codebase))
print(generate_ai_analysis_report(codebase))
```

## Analysis Categories

### 1. Codebase Summary (`codebase_summary.py`)
- `get_codebase_summary()`: Overall codebase statistics
- `get_file_summary()`: Individual file analysis
- `get_class_summary()`: Class structure analysis
- `get_function_summary()`: Function analysis
- `get_symbol_summary()`: Symbol usage patterns
- `print_codebase_overview()`: Formatted overview with emojis

### 2. Symbol Analysis (`symbol_analysis.py`)
- `analyze_symbol_usage()`: Symbol usage patterns and statistics
- `find_recursive_functions()`: Recursive function detection
- `get_symbol_dependencies()`: Detailed dependency information
- `analyze_function_complexity()`: Function complexity metrics
- `find_symbol_clusters()`: Related symbol grouping
- `analyze_symbol_relationships()`: Symbol relationship mapping

### 3. Dead Code Detection (`dead_code_detection.py`)
- `find_dead_code()`: Comprehensive dead code analysis
- `analyze_unused_imports()`: Unused import detection
- `detect_unreachable_code()`: Unreachable code patterns
- `remove_dead_code()`: Automated dead code removal (with dry-run)
- `generate_dead_code_report()`: Formatted dead code report

### 4. Import Analysis (`import_analysis.py`)
- `analyze_import_relationships()`: Import dependency analysis
- `detect_circular_imports()`: Circular dependency detection
- `get_import_graph()`: Import dependency graph generation
- `analyze_import_patterns()`: Import style and pattern analysis
- `get_file_import_details()`: Per-file import analysis
- `generate_import_report()`: Comprehensive import report

### 5. Class Hierarchy (`class_hierarchy.py`)
- `analyze_inheritance_chains()`: Inheritance relationship analysis
- `find_deepest_inheritance()`: Deep inheritance detection
- `get_class_relationships()`: Detailed class relationship mapping
- `detect_design_patterns()`: Common design pattern detection
- `generate_hierarchy_report()`: Class hierarchy report

### 6. Test Analysis (`test_analysis.py`)
- `analyze_test_coverage()`: Test coverage assessment
- `split_test_files()`: Large test file splitting utility
- `get_test_statistics()`: Comprehensive test statistics
- `generate_test_report()`: Test analysis report

### 7. AI Analysis (`ai_analysis.py`)
- `analyze_codebase()`: Automated issue detection
- `get_function_context()`: Comprehensive function context extraction
- `flag_code_issues()`: Issue flagging with auto-fix suggestions
- `generate_ai_analysis_report()`: AI-powered analysis report

### 8. Training Data (`training_data.py`)
- `generate_training_data()`: LLM training data generation
- `create_function_embeddings()`: Code embedding data creation
- `extract_code_patterns()`: Pattern extraction for ML
- `run_training_data_generation()`: Complete training pipeline

## Integration with Graph-Sitter

This analysis module integrates seamlessly with the graph-sitter ecosystem:

- **Configuration Support**: Works with all graph-sitter.com advanced settings
- **Performance Optimized**: Leverages pre-computed graph elements
- **Error Handling**: Graceful degradation when graph-sitter is unavailable
- **Extensible**: Easy to add new analysis capabilities

## Configuration

The analysis module respects graph-sitter configuration options:

```python
from graph_sitter import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig

# Configure for enhanced analysis
config = CodebaseConfig(
    method_usages=True,      # Enable method usage tracking
    generics=True,           # Enable generic type resolution
    debug=False,             # Disable verbose logging
    sync_enabled=True        # Enable graph sync
)

codebase = Codebase("path/to/code", config=config)
```

## Performance Considerations

- **Lazy Loading**: Analysis functions only process what's needed
- **Caching**: Results can be cached for repeated analysis
- **Memory Efficient**: Large codebases are processed in chunks
- **Configurable Limits**: Analysis depth and scope can be controlled

## Error Handling

All analysis functions include comprehensive error handling:

- **Graceful Degradation**: Functions work even with partial data
- **Clear Error Messages**: Detailed error information when issues occur
- **Fallback Modes**: Alternative analysis when graph-sitter is unavailable
- **Validation**: Input validation and sanity checks

## Legacy Support

Legacy analysis tools have been moved to maintain compatibility:

- `legacy_analyze_codebase.py`: Original comprehensive analysis tool
- `legacy_enhanced_analyzer.py`: Enhanced analyzer with graph-sitter integration
- `legacy_analyze_codebase_enhanced.py`: Enhanced comprehensive tool

These can still be imported and used if needed for backward compatibility.

## Contributing

When adding new analysis features:

1. Follow the existing module structure
2. Include comprehensive error handling
3. Add type hints and docstrings
4. Provide both programmatic and report interfaces
5. Include examples in the documentation
6. Add appropriate tests

## Examples

See the individual module files for detailed examples and usage patterns. Each module includes comprehensive docstrings and example code.

