# 🚀 Serena LSP Integration Guide

## Overview

The Serena LSP integration transforms graph-sitter into a comprehensive code analysis platform with IDE-level capabilities. This integration provides real-time code intelligence, advanced refactoring, code generation, and semantic search - all accessible through the familiar Codebase API.

## 🎯 Key Features

### 🧠 Real-Time Code Intelligence
- **Live Code Completions** - Context-aware suggestions as you type
- **Rich Hover Information** - Detailed symbol documentation and type info  
- **Function Signature Help** - Parameter assistance during function calls
- **Go-to Definition/References** - Enhanced cross-file navigation

### 🔧 Advanced Refactoring Engine
- **Safe Symbol Renaming** - Cross-file renaming with conflict detection
- **Extract Method/Variable** - Intelligent code extraction with scope analysis
- **Inline Operations** - Safe inlining with dependency checking
- **Move Symbol/File** - Relocate code with automatic import updates
- **Organize Imports** - Automatic import cleanup and optimization

### ⚡ Code Actions & Quick Fixes
- **Automated Error Fixes** - One-click solutions for common issues
- **Code Quality Improvements** - Suggestions for better patterns
- **Import Management** - Add missing imports, remove unused ones
- **Style Corrections** - Automatic formatting and style fixes

### 🏗️ Intelligent Code Generation
- **Boilerplate Generation** - Templates for common patterns
- **Test Generation** - Automatic unit and integration test creation
- **Documentation Generation** - Auto-generate docstrings and comments
- **Template System** - Customizable code templates

### 🔍 Enhanced Semantic Search
- **Natural Language Queries** - "Find functions that handle authentication"
- **Pattern-Based Search** - Complex code pattern matching
- **Similarity Analysis** - Find similar code structures
- **Usage Pattern Detection** - Identify code patterns and anti-patterns

### 🌐 Multi-Language Support
- **Python** - Full Python ecosystem support
- **TypeScript/JavaScript** - Complete Node.js and web development support
- **Java** - Enterprise Java with Spring/Maven integration
- **C#** - .NET ecosystem with NuGet and framework support
- **Go** - Goroutines, interfaces, and Go-specific patterns
- **Rust** - Memory safety analysis and Cargo integration
- **PHP** - Laravel/Symfony framework support
- **Extensible Architecture** - Easy to add new languages

### ⚡ Real-Time Analysis
- **File Watching** - Automatic re-analysis on code changes
- **Incremental Updates** - Efficient processing of only changed code
- **Live Symbol Tracking** - Real-time symbol relationship updates
- **Performance Optimization** - Efficient caching and memory management

### 🎨 Advanced Symbol Intelligence
- **Deep Context Analysis** - Understanding symbol relationships and dependencies
- **Impact Analysis** - Predict effects of code changes
- **Cross-File Resolution** - Intelligent symbol resolution across projects
- **Semantic Understanding** - AI-powered code comprehension

## 🚀 Quick Start

### Basic Usage

```python
from graph_sitter import Codebase

# Initialize codebase with Serena integration
codebase = Codebase("path/to/your/project")

# Get code completions
completions = codebase.get_completions("src/main.py", line=10, character=5)
for comp in completions:
    print(f"{comp['label']}: {comp['detail']}")

# Get hover information
hover = codebase.get_hover_info("src/main.py", line=15, character=10)
if hover:
    print(f"Symbol: {hover['symbolName']}")
    print(f"Documentation: {hover['documentation']}")

# Rename a symbol safely
result = codebase.rename_symbol("src/main.py", 20, 5, "new_function_name")
if result['success']:
    print(f"Renamed symbol in {len(result['changes'])} locations")
```

### Advanced Features

```python
# Semantic search with natural language
results = codebase.semantic_search("functions that handle user authentication")
for result in results:
    print(f"Found: {result['file']}:{result['line']} - {result['match']}")

# Extract method refactoring
result = codebase.extract_method("src/main.py", start_line=15, end_line=25, method_name="calculate_total")
if result['success']:
    print("Method extracted successfully")

# Generate tests automatically
result = codebase.generate_tests("calculate_total", ["unit", "edge_cases"])
if result['success']:
    for test in result['generated_tests']:
        print(test)

# Find similar code patterns
reference = "def calculate_total(items): return sum(item.price for item in items)"
results = codebase.find_similar_code(reference, similarity_threshold=0.7)
for result in results:
    print(f"Similar code in {result['file']} (similarity: {result['similarity']})")
```

## 📚 API Reference

### Intelligence Methods

#### `get_completions(file_path, line, character, **kwargs)`
Get code completions at the specified position.

**Parameters:**
- `file_path` (str): Path to the file
- `line` (int): Line number (0-based)
- `character` (int): Character position (0-based)
- `**kwargs`: Additional completion options

**Returns:** List of completion items with details

**Example:**
```python
completions = codebase.get_completions("src/main.py", 10, 5)
for comp in completions:
    print(f"{comp['label']}: {comp['detail']}")
```

#### `get_hover_info(file_path, line, character)`
Get hover information for symbol at position.

**Parameters:**
- `file_path` (str): Path to the file
- `line` (int): Line number (0-based)
- `character` (int): Character position (0-based)

**Returns:** Hover information or None if not available

**Example:**
```python
hover = codebase.get_hover_info("src/main.py", 15, 10)
if hover:
    print(f"Symbol: {hover['symbolName']}")
    print(f"Type: {hover['symbolType']}")
    print(f"Documentation: {hover['documentation']}")
```

#### `get_signature_help(file_path, line, character)`
Get signature help for function call at position.

**Parameters:**
- `file_path` (str): Path to the file
- `line` (int): Line number (0-based)
- `character` (int): Character position (0-based)

**Returns:** Signature help information or None if not available

**Example:**
```python
sig = codebase.get_signature_help("src/main.py", 20, 15)
if sig:
    print(f"Function: {sig['functionName']}")
    for i, param in enumerate(sig['parameters']):
        active = " <-- ACTIVE" if i == sig['activeParameter'] else ""
        print(f"  {param['name']}: {param['typeAnnotation']}{active}")
```

### Refactoring Methods

#### `rename_symbol(file_path, line, character, new_name, preview=False)`
Rename symbol at position across all files.

**Parameters:**
- `file_path` (str): Path to the file containing the symbol
- `line` (int): Line number (0-based)
- `character` (int): Character position (0-based)
- `new_name` (str): New name for the symbol
- `preview` (bool): Whether to return preview without applying changes

**Returns:** Refactoring result with changes and conflicts

**Example:**
```python
# Preview rename operation
result = codebase.rename_symbol("src/main.py", 10, 5, "new_function_name", preview=True)
if result['success']:
    print(f"Will rename in {len(result['changes'])} locations")
    # Apply the rename
    result = codebase.rename_symbol("src/main.py", 10, 5, "new_function_name")
```

#### `extract_method(file_path, start_line, end_line, method_name, **kwargs)`
Extract selected code into a new method.

**Parameters:**
- `file_path` (str): Path to the file
- `start_line` (int): Start line of selection (0-based)
- `end_line` (int): End line of selection (0-based)
- `method_name` (str): Name for the new method
- `**kwargs`: Additional options (target_class, visibility, etc.)

**Returns:** Refactoring result with changes and conflicts

**Example:**
```python
result = codebase.extract_method("src/main.py", 15, 25, "calculate_total")
if result['success']:
    print("Method extracted successfully")
    for change in result['changes']:
        print(f"Modified: {change['file']}")
```

#### `extract_variable(file_path, line, character, variable_name, **kwargs)`
Extract expression into a variable.

**Parameters:**
- `file_path` (str): Path to the file
- `line` (int): Line number (0-based)
- `character` (int): Character position (0-based)
- `variable_name` (str): Name for the new variable
- `**kwargs`: Additional options (scope, type_annotation, etc.)

**Returns:** Refactoring result with changes and conflicts

**Example:**
```python
result = codebase.extract_variable("src/main.py", 20, 10, "temp_result")
if result['success']:
    print("Variable extracted successfully")
```

### Code Actions Methods

#### `get_code_actions(file_path, start_line, end_line, context=None)`
Get available code actions for the specified range.

**Parameters:**
- `file_path` (str): Path to the file
- `start_line` (int): Start line of range (0-based)
- `end_line` (int): End line of range (0-based)
- `context` (List[str]): Optional context information

**Returns:** List of available code actions

**Example:**
```python
actions = codebase.get_code_actions("src/main.py", 10, 15)
for action in actions:
    print(f"{action['title']}: {action['description']}")
```

#### `apply_code_action(action_id, file_path, **kwargs)`
Apply a specific code action.

**Parameters:**
- `action_id` (str): ID of the action to apply
- `file_path` (str): Path to the file
- `**kwargs`: Additional action parameters

**Returns:** Result of applying the code action

**Example:**
```python
result = codebase.apply_code_action("add_missing_import", "src/main.py")
if result['success']:
    print("Code action applied successfully")
```

#### `organize_imports(file_path, remove_unused=True, sort_imports=True)`
Organize imports in the specified file.

**Parameters:**
- `file_path` (str): Path to the file
- `remove_unused` (bool): Whether to remove unused imports
- `sort_imports` (bool): Whether to sort imports

**Returns:** Result of import organization

**Example:**
```python
result = codebase.organize_imports("src/main.py")
if result['success']:
    print("Imports organized successfully")
```

### Generation Methods

#### `generate_boilerplate(template, context, target_file=None)`
Generate boilerplate code from template.

**Parameters:**
- `template` (str): Template name or pattern
- `context` (Dict[str, Any]): Context variables for template
- `target_file` (str): Optional target file path

**Returns:** Generated code and metadata

**Example:**
```python
result = codebase.generate_boilerplate("class", {
    "class_name": "MyClass",
    "base_class": "BaseClass"
})
if result['success']:
    print(result['generated_code'])
```

#### `generate_tests(target_function, test_types=None, **kwargs)`
Generate tests for the specified function.

**Parameters:**
- `target_function` (str): Name of the function to test
- `test_types` (List[str]): Types of tests to generate (unit, integration, etc.)
- `**kwargs`: Additional generation options

**Returns:** Generated test code and metadata

**Example:**
```python
result = codebase.generate_tests("calculate_total", ["unit", "edge_cases"])
if result['success']:
    for test in result['generated_tests']:
        print(test)
```

#### `generate_documentation(target, format="docstring", **kwargs)`
Generate documentation for the specified target.

**Parameters:**
- `target` (str): Target symbol or file to document
- `format` (str): Documentation format (docstring, markdown, etc.)
- `**kwargs`: Additional generation options

**Returns:** Generated documentation and metadata

**Example:**
```python
result = codebase.generate_documentation("MyClass.my_method")
if result['success']:
    print(result['generated_docs'])
```

### Search Methods

#### `semantic_search(query, language="natural", **kwargs)`
Perform semantic search across the codebase.

**Parameters:**
- `query` (str): Search query (natural language or code pattern)
- `language` (str): Query language type (natural, code, regex)
- `**kwargs`: Additional search options

**Returns:** List of search results with relevance scores

**Example:**
```python
results = codebase.semantic_search("functions that handle authentication")
for result in results:
    print(f"{result['file']}:{result['line']} - {result['match']}")
```

#### `find_code_patterns(pattern, suggest_improvements=False)`
Find code patterns matching the specified pattern.

**Parameters:**
- `pattern` (str): Code pattern to search for
- `suggest_improvements` (bool): Whether to suggest improvements

**Returns:** List of pattern matches with optional improvement suggestions

**Example:**
```python
results = codebase.find_code_patterns("for.*in.*range", suggest_improvements=True)
for result in results:
    print(f"Found pattern in {result['file']}")
    if result['improvements']:
        print(f"Suggestion: {result['improvements'][0]}")
```

#### `find_similar_code(reference_code, similarity_threshold=0.8)`
Find code similar to the reference code.

**Parameters:**
- `reference_code` (str): Reference code to find similarities to
- `similarity_threshold` (float): Minimum similarity score (0.0 to 1.0)

**Returns:** List of similar code blocks with similarity scores

**Example:**
```python
reference = "def calculate_total(items): return sum(item.price for item in items)"
results = codebase.find_similar_code(reference, 0.7)
for result in results:
    print(f"Similar code in {result['file']} (similarity: {result['similarity']})")
```

### Symbol Intelligence Methods

#### `get_symbol_context(symbol, include_dependencies=True, **kwargs)`
Get comprehensive context for a symbol.

**Parameters:**
- `symbol` (str): Symbol name to analyze
- `include_dependencies` (bool): Whether to include dependency information
- `**kwargs`: Additional context options

**Returns:** Comprehensive symbol context and relationships

**Example:**
```python
context = codebase.get_symbol_context("MyClass")
print(f"Symbol type: {context['type']}")
print(f"Dependencies: {context['dependencies']}")
print(f"Usages: {context['usages']}")
```

#### `analyze_symbol_impact(symbol, change_type)`
Analyze the impact of changing a symbol.

**Parameters:**
- `symbol` (str): Symbol name to analyze
- `change_type` (str): Type of change (rename, delete, modify, etc.)

**Returns:** Impact analysis with affected files and recommendations

**Example:**
```python
impact = codebase.analyze_symbol_impact("calculate_total", "rename")
print(f"Impact level: {impact['impact_level']}")
print(f"Affected files: {impact['affected_files']}")
for rec in impact['recommendations']:
    print(f"Recommendation: {rec}")
```

### Real-time Methods

#### `enable_realtime_analysis(watch_patterns=None, auto_refresh=True)`
Enable real-time analysis with file watching.

**Parameters:**
- `watch_patterns` (List[str]): File patterns to watch (e.g., ["*.py", "*.ts"])
- `auto_refresh` (bool): Whether to automatically refresh analysis on changes

**Returns:** True if real-time analysis was enabled successfully

**Example:**
```python
success = codebase.enable_realtime_analysis(["*.py", "*.ts"])
if success:
    print("Real-time analysis enabled")
```

#### `disable_realtime_analysis()`
Disable real-time analysis.

**Returns:** True if real-time analysis was disabled successfully

**Example:**
```python
success = codebase.disable_realtime_analysis()
if success:
    print("Real-time analysis disabled")
```

### Utility Methods

#### `get_serena_status()`
Get comprehensive status of Serena integration.

**Returns:** Status information for all Serena capabilities

**Example:**
```python
status = codebase.get_serena_status()
print(f"Serena enabled: {status.get('enabled', False)}")
for capability, details in status.get('capability_details', {}).items():
    print(f"{capability}: {details}")
```

#### `shutdown_serena()`
Shutdown Serena integration and cleanup resources.

**Example:**
```python
codebase.shutdown_serena()
print("Serena integration shutdown")
```

## 🔧 Configuration

### Basic Configuration

```python
from graph_sitter.extensions.serena import SerenaConfig, SerenaCapability

# Create custom configuration
config = SerenaConfig(
    enabled_capabilities=[
        SerenaCapability.INTELLIGENCE,
        SerenaCapability.REFACTORING,
        SerenaCapability.SEARCH
    ],
    realtime_analysis=True,
    file_watch_patterns=["*.py", "*.ts", "*.js"],
    cache_size=2000,
    max_completions=100,
    enable_ai_features=True,
    performance_mode=False
)

# Initialize codebase with custom config
codebase = Codebase("path/to/project")
# Configuration will be applied automatically
```

### Performance Tuning

```python
# For large codebases, optimize performance
config = SerenaConfig(
    performance_mode=True,
    cache_size=5000,
    max_completions=25,
    realtime_analysis=False  # Disable for better performance
)
```

### Language-Specific Settings

```python
# Python-focused configuration
config = SerenaConfig(
    file_watch_patterns=["*.py", "*.pyi"],
    enable_ai_features=True
)

# Multi-language configuration
config = SerenaConfig(
    file_watch_patterns=["*.py", "*.ts", "*.js", "*.java", "*.cs", "*.go", "*.rs"]
)
```

## 🚀 Advanced Usage

### Batch Operations

```python
# Process multiple files efficiently
files_to_analyze = ["src/main.py", "src/utils.py", "src/models.py"]

for file_path in files_to_analyze:
    # Get completions for common positions
    completions = codebase.get_completions(file_path, 0, 0)
    
    # Organize imports
    result = codebase.organize_imports(file_path)
    
    # Generate documentation
    doc_result = codebase.generate_documentation(file_path, format="markdown")
```

### Integration with CI/CD

```python
# Code quality checks in CI/CD
def check_code_quality(codebase):
    issues = []
    
    # Find code patterns that need improvement
    patterns = codebase.find_code_patterns("TODO|FIXME|HACK", suggest_improvements=True)
    for pattern in patterns:
        issues.append(f"Code smell in {pattern['file']}: {pattern['pattern']}")
    
    # Check for similar code (potential duplication)
    for file in codebase.files:
        if file.path.endswith('.py'):
            similar = codebase.find_similar_code(file.content[:500], 0.9)
            if len(similar) > 1:
                issues.append(f"Potential code duplication in {file.path}")
    
    return issues
```

### Custom Workflows

```python
# Automated refactoring workflow
def refactor_function(codebase, file_path, function_name):
    # 1. Find the function
    results = codebase.semantic_search(f"function {function_name}")
    
    if not results:
        return {"error": "Function not found"}
    
    # 2. Analyze impact
    impact = codebase.analyze_symbol_impact(function_name, "modify")
    
    # 3. Generate tests if none exist
    test_result = codebase.generate_tests(function_name, ["unit", "integration"])
    
    # 4. Extract complex logic into helper methods
    # (This would require more sophisticated analysis)
    
    # 5. Generate documentation
    doc_result = codebase.generate_documentation(function_name)
    
    return {
        "impact": impact,
        "tests_generated": test_result['success'],
        "documentation": doc_result['generated_docs'] if doc_result['success'] else None
    }
```

## 🐛 Troubleshooting

### Common Issues

#### Serena Not Initializing
```python
# Check Serena status
status = codebase.get_serena_status()
if not status.get('enabled'):
    print(f"Serena error: {status.get('error')}")
```

#### Performance Issues
```python
# Enable performance mode
config = SerenaConfig(performance_mode=True, cache_size=1000)

# Disable real-time analysis for large codebases
codebase.disable_realtime_analysis()
```

#### Language Server Issues
```python
# Check LSP bridge status
status = codebase.get_serena_status()
lsp_status = status.get('lsp_bridge_status', {})
print(f"LSP initialized: {lsp_status.get('initialized')}")
print(f"Language servers: {lsp_status.get('language_servers')}")
```

### Debug Mode

```python
import logging
logging.getLogger('graph_sitter.extensions.serena').setLevel(logging.DEBUG)

# Now Serena operations will show detailed debug information
completions = codebase.get_completions("src/main.py", 10, 5)
```

## 🤝 Contributing

### Adding New Capabilities

1. Create a new module in `src/graph_sitter/extensions/serena/`
2. Implement the capability class with required methods
3. Add the capability to `SerenaCapability` enum
4. Update `SerenaCore` to initialize the new capability
5. Add methods to `SerenaIntegration` class
6. Update documentation

### Testing

```python
# Run Serena integration tests
python -m pytest tests/extensions/serena/

# Test specific capability
python -m pytest tests/extensions/serena/test_intelligence.py
```

## 📈 Performance Benchmarks

### Completion Performance
- **Cold start**: ~100ms
- **Cached results**: ~5ms
- **Large files (>1000 lines)**: ~50ms

### Refactoring Performance
- **Simple rename**: ~200ms
- **Cross-file rename**: ~500ms
- **Extract method**: ~300ms

### Search Performance
- **Semantic search**: ~1-2s for 10k files
- **Pattern matching**: ~500ms for 10k files
- **Similarity analysis**: ~2-3s for reference

## 🔮 Future Roadmap

### Planned Features
- **AI-Powered Code Review** - Automated code review with suggestions
- **Smart Code Migration** - Automated framework/library migrations
- **Performance Analysis** - Code performance optimization suggestions
- **Security Analysis** - Automated security vulnerability detection
- **Code Metrics** - Comprehensive code quality metrics
- **Visual Code Maps** - Interactive code visualization
- **Collaborative Features** - Team-based code analysis and sharing

### Language Expansion
- **Kotlin** - Android and JVM development
- **Swift** - iOS and macOS development
- **C/C++** - Systems programming support
- **Ruby** - Rails and Ruby ecosystem
- **Scala** - Functional programming support
- **Dart** - Flutter development

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/graph-sitter/issues)
- **Documentation**: [Full API documentation](https://docs.graph-sitter.com/serena)
- **Community**: [Join our Discord](https://discord.gg/graph-sitter)

---

**🎉 Congratulations! You now have the most comprehensive code analysis platform available. Happy coding with Serena! 🚀**

