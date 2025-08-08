# Comprehensive Error Analysis for Graph-Sitter

This document describes the comprehensive error analysis capabilities added to graph-sitter, providing advanced error detection, categorization, and context-aware analysis.

## Overview

The comprehensive error analysis system integrates Serena LSP capabilities with graph-sitter's existing codebase analysis to provide:

- **24+ Error Categories**: Comprehensive error classification including syntax, type, security, performance, and more
- **Real-time Monitoring**: Live error detection and streaming as code changes
- **Context-aware Analysis**: Deep understanding of error impact and blast radius
- **Fix Suggestions**: Intelligent recommendations for resolving errors
- **Graph-sitter Integration**: Seamless integration with existing codebase analysis

## Quick Start

```python
from graph_sitter.core.codebase import Codebase

# Create a codebase instance
codebase = Codebase('path/to/your/repo')

# Access comprehensive error analysis
full_errors = codebase.FullErrors

# Get comprehensive error analysis
if full_errors:
    errors = full_errors.get_comprehensive_errors()
    print(f'Found {errors.total_count} errors')
    
    # Get error summary with statistics
    summary = full_errors.get_error_summary()
    print(f'Total errors: {summary["total_errors"]}')
    print(f'By category: {summary["errors_by_category"]}')
```

## Features

### 1. Enhanced Error Categories (24+ Types)

The system categorizes errors into comprehensive categories:

#### Core Language Errors
- **Syntax**: Parse errors, missing brackets, indentation issues
- **Type**: Type mismatches, invalid type annotations
- **Logic**: Undefined variables, unreachable code
- **Runtime**: Potential runtime exceptions

#### Code Quality
- **Style**: Formatting, naming conventions
- **Complexity**: High cyclomatic complexity, deep nesting
- **Maintainability**: Code smells, anti-patterns
- **Readability**: Unclear variable names, missing documentation

#### Security & Safety
- **Security**: SQL injection, XSS vulnerabilities
- **Vulnerability**: Known security issues
- **Safety**: Null pointer access, buffer overflows

#### Performance
- **Performance**: Inefficient algorithms, unnecessary computations
- **Memory**: Memory leaks, excessive allocations
- **Optimization**: Missed optimization opportunities

#### Dependencies & Imports
- **Dependency**: Missing dependencies, version conflicts
- **Import**: Import errors, circular imports
- **Compatibility**: Version compatibility issues

#### Code Organization
- **Unused**: Unused variables, functions, imports
- **Duplicate**: Code duplication, redundant logic
- **Dead Code**: Unreachable or obsolete code

#### Documentation & Testing
- **Documentation**: Missing docstrings, outdated comments
- **Testing**: Missing tests, test failures

### 2. Comprehensive Error Information

Each error includes:

```python
error = ErrorInfo(
    id="unique_error_id",
    message="Error description",
    severity=ErrorSeverity.ERROR,  # CRITICAL, ERROR, WARNING, INFO, HINT
    category=ErrorCategory.SYNTAX,  # One of 24+ categories
    location=ErrorLocation(
        file_path="path/to/file.py",
        line=42,
        column=10,
        end_line=42,
        end_column=20
    ),
    suggestions=["Fix suggestion 1", "Fix suggestion 2"],
    context={"surrounding_code": "..."},
    related_errors=["related_error_id"],
    timestamp=1234567890.0
)
```

### 3. Context-Aware Analysis

The system provides deep context analysis for each error:

```python
# Analyze error context
context = full_errors.analyze_error_context(error)

print(f"Code context: {context.code_context}")
print(f"Calling functions: {context.calling_functions}")
print(f"Called functions: {context.called_functions}")
print(f"Blast radius: {context.blast_radius}")
print(f"Fix suggestions: {context.fix_suggestions}")
```

### 4. Real-time Monitoring

Enable real-time error monitoring:

```python
# Add error listener
def on_errors(errors):
    print(f"New errors detected: {len(errors)}")

full_errors.lsp_bridge.add_error_listener(on_errors)

# Start real-time monitoring
full_errors.lsp_bridge.start_real_time_monitoring(interval=5.0)

# Get error statistics
stats = full_errors.lsp_bridge.get_error_statistics()
print(f"Total errors in history: {stats['total_errors']}")
print(f"By severity: {stats['by_severity']}")
print(f"By category: {stats['by_category']}")
```

### 5. Codebase Analysis

Analyze entire codebases:

```python
# Analyze entire codebase
comprehensive_errors = full_errors.lsp_bridge.analyze_codebase(
    file_patterns=['*.py', '*.ts'],
    exclude_patterns=['*/node_modules/*', '*/__pycache__/*']
)

print(f"Analysis duration: {comprehensive_errors.analysis_duration:.2f}s")
print(f"Files analyzed: {len(comprehensive_errors.files_analyzed)}")
print(f"Errors by severity:")
print(f"  Critical: {comprehensive_errors.critical_count}")
print(f"  Errors: {comprehensive_errors.error_count}")
print(f"  Warnings: {comprehensive_errors.warning_count}")
```

### 6. Advanced Filtering

Filter errors by various criteria:

```python
from graph_sitter.extensions.lsp import ErrorSeverity, ErrorCategory

# Get only critical errors
critical_errors = full_errors.get_comprehensive_errors(
    severity_filter=[ErrorSeverity.CRITICAL, ErrorSeverity.ERROR],
    max_errors=50
)

# Get errors by category
syntax_errors = comprehensive_errors.get_errors_by_category(ErrorCategory.SYNTAX)
security_errors = comprehensive_errors.get_errors_by_category(ErrorCategory.SECURITY)

# Get errors by file
file_errors = comprehensive_errors.get_errors_by_file('path/to/file.py')
```

## API Reference

### Core Classes

#### `ComprehensiveErrorAnalyzer`
Main class for error analysis with graph-sitter integration.

```python
analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp=True)

# Get all errors
errors = analyzer.get_all_errors()
warnings = analyzer.get_all_warnings()
diagnostics = analyzer.get_all_diagnostics()

# Get comprehensive analysis
comprehensive = analyzer.get_comprehensive_errors(
    include_context=True,
    include_suggestions=True,
    max_errors=100,
    severity_filter=[ErrorSeverity.ERROR]
)

# Analyze error context
context = analyzer.analyze_error_context(error)

# Get error summary
summary = analyzer.get_error_summary()
```

#### `SerenaLSPBridge`
Bridge to Serena LSP servers for real-time error detection.

```python
bridge = SerenaLSPBridge(repo_path)

# Get diagnostics
diagnostics = bridge.get_diagnostics()
file_diagnostics = bridge.get_file_diagnostics('path/to/file.py')

# Real-time monitoring
bridge.add_error_listener(callback)
bridge.start_real_time_monitoring(interval=5.0)

# Statistics
stats = bridge.get_error_statistics()
```

#### `ErrorInfo`
Comprehensive error information with enhanced categorization.

```python
error = ErrorInfo(
    id="error_id",
    message="Error message",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.SYNTAX,
    location=ErrorLocation(...),
    suggestions=["suggestion1", "suggestion2"],
    context={"key": "value"},
    related_errors=["related_id"]
)

# Properties
print(error.is_critical)
print(error.is_error)
print(error.is_warning)
print(error.display_text)
```

### Convenience Functions

```python
from graph_sitter.extensions.lsp import (
    analyze_codebase_errors,
    get_instant_error_context,
    get_all_codebase_errors_with_context
)

# Quick codebase analysis
analyzer = analyze_codebase_errors(codebase)

# Get error context for specific location
context = get_instant_error_context(codebase, 'file.py', line=42)

# Get all errors with context
all_contexts = get_all_codebase_errors_with_context(codebase)
```

## Integration with Existing Graph-Sitter Features

The comprehensive error analysis integrates seamlessly with existing graph-sitter capabilities:

### Codebase Properties

```python
# Basic diagnostics (automatically available)
errors = codebase.errors
warnings = codebase.warnings
diagnostics = codebase.diagnostics

# Comprehensive analysis (new)
full_errors = codebase.FullErrors
```

### Context Analysis Integration

The system leverages existing graph-sitter analysis functions:

- `get_codebase_summary()` - Overall codebase context
- `get_file_summary()` - File-level context
- `get_function_summary()` - Function-level context
- `get_class_summary()` - Class-level context
- `get_symbol_summary()` - Symbol-level context

### Transaction Awareness

The system integrates with graph-sitter's transaction system to provide real-time updates when files change.

## Configuration

### LSP Server Configuration

The system automatically detects and configures LSP servers for supported languages:

- **Python**: Automatically configured for `.py` files
- **TypeScript/JavaScript**: Support planned for `.ts`, `.tsx`, `.js`, `.jsx` files
- **Additional languages**: Can be added by extending the language server framework

### Error Categories

Error categories can be customized by extending the `ErrorCategory` enum:

```python
from graph_sitter.extensions.lsp import ErrorCategory

# Categories are automatically determined based on:
# - LSP diagnostic source
# - Error message content
# - Code patterns
```

## Performance Considerations

- **Lazy Loading**: LSP servers are initialized only when needed
- **Caching**: Error analysis results are cached for performance
- **Incremental Updates**: Only changed files are re-analyzed
- **Background Processing**: Real-time monitoring runs in background threads
- **Memory Management**: Error history is limited to prevent memory leaks

## Troubleshooting

### Common Issues

1. **"FullErrors is None"**
   - This is expected when LSP servers are not available
   - The system gracefully degrades to basic functionality

2. **"LSP integration not available"**
   - Install Serena dependencies for full LSP support
   - Basic diagnostics still work without LSP

3. **"Failed to initialize LSP diagnostics"**
   - This is expected in environments without LSP servers
   - The system continues to work with reduced functionality

### Debug Information

```python
# Check LSP status
if codebase.FullErrors:
    status = codebase.FullErrors.lsp_bridge.get_status()
    print(f"LSP Status: {status}")

# Get diagnostic capabilities
if hasattr(codebase, 'get_lsp_status'):
    lsp_status = codebase.get_lsp_status()
    print(f"Diagnostic Status: {lsp_status}")
```

## Examples

### Example 1: Basic Error Analysis

```python
from graph_sitter.core.codebase import Codebase

codebase = Codebase('my-project')
full_errors = codebase.FullErrors

if full_errors:
    # Get comprehensive errors
    errors = full_errors.get_comprehensive_errors(max_errors=20)
    
    print(f"Found {errors.total_count} errors:")
    print(f"  Critical: {errors.critical_count}")
    print(f"  Errors: {errors.error_count}")
    print(f"  Warnings: {errors.warning_count}")
    
    # Show top errors by category
    for category, count in errors.get_summary()['category_breakdown'].items():
        if count > 0:
            print(f"  {category}: {count}")
```

### Example 2: Real-time Monitoring

```python
def error_callback(errors):
    print(f"🚨 {len(errors)} new errors detected!")
    for error in errors[:3]:  # Show first 3
        print(f"  {error.display_text}")

if full_errors and full_errors.lsp_bridge:
    # Add listener
    full_errors.lsp_bridge.add_error_listener(error_callback)
    
    # Start monitoring
    full_errors.lsp_bridge.start_real_time_monitoring(interval=10.0)
    
    print("Real-time monitoring started...")
```

### Example 3: Error Context Analysis

```python
# Get file errors
file_errors = full_errors.get_file_errors('src/main.py')

for error in file_errors:
    # Analyze context
    context = full_errors.analyze_error_context(error)
    
    print(f"Error: {error.message}")
    print(f"Category: {error.category.value}")
    print(f"Severity: {error.severity.value}")
    
    if context.code_context:
        print("Code context:")
        print(context.code_context)
    
    if context.fix_suggestions:
        print("Suggestions:")
        for suggestion in context.fix_suggestions:
            print(f"  • {suggestion}")
    
    print("-" * 50)
```

## Contributing

To extend the error analysis system:

1. **Add new error categories** in `ErrorCategory` enum
2. **Implement language servers** by extending `BaseLanguageServer`
3. **Enhance context analysis** by adding new analysis functions
4. **Improve categorization** by updating `_determine_category()` logic

## License

This comprehensive error analysis system is part of the graph-sitter project and follows the same license terms.
