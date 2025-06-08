# Graph-Sitter Codebase Analysis Functions

This module provides comprehensive summary functions for analyzing codebases using graph-sitter. These functions extract detailed insights about code structure, dependencies, and usage patterns.

## Available Functions

### `get_codebase_summary(codebase: Codebase) -> str`

Returns a comprehensive summary of the entire codebase including:
- Total nodes and edges in the graph
- File, import, and symbol counts
- Breakdown by symbol types (classes, functions, global variables, interfaces)
- Edge type analysis (symbol usage, import resolution, exports)

**Example:**
```python
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary

codebase = Codebase("./my_project")
summary = get_codebase_summary(codebase)
print(summary)
```

**Output:**
```
Contains 1247 nodes
- 45 files
- 123 imports
- 67 external_modules
- 892 symbols
	- 23 classes
	- 156 functions
	- 89 global_vars
	- 12 interfaces

Contains 2341 edges
- 1456 symbol -> used symbol
- 234 import -> used symbol
- 89 export -> exported symbol
```

### `get_file_summary(file: SourceFile) -> str`

Returns a detailed summary of a specific file including:
- Import count and details
- Symbol references breakdown
- Usage summary (how many other files import this file)

**Example:**
```python
file = codebase.get_file("src/main.py")
summary = get_file_summary(file)
print(summary)
```

### `get_class_summary(cls: Class) -> str`

Returns a comprehensive summary of a class including:
- Parent class relationships
- Method and attribute counts
- Decorator information
- Dependency analysis
- Usage patterns across the codebase

**Example:**
```python
cls = codebase.get_class("MyClass")
summary = get_class_summary(cls)
print(summary)
```

### `get_function_summary(func: Function) -> str`

Returns a detailed summary of a function including:
- Return statement analysis
- Parameter information
- Function call patterns
- Call site locations
- Decorator usage
- Dependency relationships

**Example:**
```python
func = codebase.get_function("process_data")
summary = get_function_summary(func)
print(summary)
```

### `get_symbol_summary(symbol: Symbol) -> str`

Returns a comprehensive usage summary for any symbol including:
- Total usage count across the codebase
- Breakdown by symbol types that use it
- Import analysis
- External module dependencies

**Example:**
```python
symbol = codebase.get_symbol("my_variable")
summary = get_symbol_summary(symbol)
print(summary)
```

## Usage Patterns

### 1. Quick Codebase Overview

```python
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary

def quick_overview(path):
    codebase = Codebase(path)
    print("📊 Codebase Overview:")
    print(get_codebase_summary(codebase))
    
    # Show top files by symbol count
    files_by_symbols = sorted(codebase.files, key=lambda f: len(f.symbols), reverse=True)
    print("\n🔥 Top files by symbol count:")
    for i, file in enumerate(files_by_symbols[:5]):
        print(f"  {i+1}. {file.name}: {len(file.symbols)} symbols")

quick_overview("./my_project")
```

### 2. Analyze Specific Components

```python
def analyze_component(codebase_path, component_name, component_type):
    codebase = Codebase(codebase_path)
    
    if component_type == "class":
        component = codebase.get_class(component_name)
        summary = get_class_summary(component)
    elif component_type == "function":
        component = codebase.get_function(component_name)
        summary = get_function_summary(component)
    elif component_type == "file":
        component = codebase.get_file(component_name)
        summary = get_file_summary(component)
    else:
        component = codebase.get_symbol(component_name)
        summary = get_symbol_summary(component)
    
    print(f"📋 Analysis of {component_type}: {component_name}")
    print(summary)

# Analyze specific components
analyze_component("./project", "UserService", "class")
analyze_component("./project", "authenticate", "function")
```

### 3. Dependency Analysis

```python
def analyze_dependencies(codebase_path):
    codebase = Codebase(codebase_path)
    
    print("🔗 Dependency Analysis:")
    print(get_codebase_summary(codebase))
    
    # Find most connected symbols
    symbols_by_usage = sorted(codebase.symbols, 
                             key=lambda s: len(s.symbol_usages), 
                             reverse=True)
    
    print("\n🌟 Most used symbols:")
    for symbol in symbols_by_usage[:10]:
        print(f"\n{symbol.name} ({type(symbol).__name__}):")
        print(get_symbol_summary(symbol))

analyze_dependencies("./my_project")
```

### 4. File-by-File Analysis

```python
def analyze_all_files(codebase_path):
    codebase = Codebase(codebase_path)
    
    print("📁 File-by-File Analysis:")
    for file in codebase.files:
        print(f"\n{'='*60}")
        print(get_file_summary(file))
        
        # Show classes in this file
        if file.classes:
            print(f"\n🏗️ Classes in {file.name}:")
            for cls in file.classes:
                print(get_class_summary(cls))
        
        # Show functions in this file
        if file.functions:
            print(f"\n⚙️ Functions in {file.name}:")
            for func in file.functions:
                print(get_function_summary(func))

analyze_all_files("./my_project")
```

## Integration with Other Tools

These summary functions work well with other graph-sitter analysis tools:

```python
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import *

# Combine with contexten analysis
from contexten.extensions.graph_sitter import comprehensive_analysis

def enhanced_analysis(codebase_path):
    codebase = Codebase(codebase_path)
    
    # Get basic summaries
    print("📊 Basic Codebase Summary:")
    print(get_codebase_summary(codebase))
    
    # Get detailed analysis
    print("\n🔍 Comprehensive Analysis:")
    results = comprehensive_analysis(codebase)
    
    # Combine insights
    print("\n💡 Key Insights:")
    print(f"- Dead functions: {results['dead_code']['summary']['total_dead_functions']}")
    print(f"- Complex functions: {results['complexity']['summary']['high_complexity_functions']}")
    print(f"- Security issues: {results['security']['summary']['critical_issues']}")
    
    return results

enhanced_analysis("./my_project")
```

## Error Handling

```python
def safe_analysis(codebase_path, entity_name, entity_type):
    try:
        codebase = Codebase(codebase_path)
        
        if entity_type == "class":
            entity = codebase.get_class(entity_name)
            summary = get_class_summary(entity)
        elif entity_type == "function":
            entity = codebase.get_function(entity_name)
            summary = get_function_summary(entity)
        # ... other types
        
        print(summary)
        
    except Exception as e:
        print(f"❌ Error analyzing {entity_type} '{entity_name}': {e}")
        
        # Fallback: show available entities
        print(f"\n📋 Available {entity_type}s:")
        if entity_type == "class":
            for cls in codebase.classes:
                print(f"  - {cls.name}")
        elif entity_type == "function":
            for func in codebase.functions:
                print(f"  - {func.name}")

safe_analysis("./project", "NonExistentClass", "class")
```

## Command Line Usage

You can also use the example script for command-line analysis:

```bash
# Full analysis
python src/graph_sitter/codebase/example_usage.py ./my_project full

# Quick overview
python src/graph_sitter/codebase/example_usage.py ./my_project quick

# Specific entity analysis
python src/graph_sitter/codebase/example_usage.py ./my_project specific
```

## Return Value Format

All summary functions return formatted strings with:
- Clear section headers with emoji indicators
- Hierarchical information with proper indentation
- Quantitative metrics (counts, percentages)
- Relationship information (dependencies, usages)
- File paths and locations where relevant

The output is designed to be both human-readable and suitable for further processing or logging.

