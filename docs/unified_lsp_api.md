# Unified LSP API Documentation

The Graph-Sitter Enhanced Codebase provides a comprehensive, unified API for LSP (Language Server Protocol) error retrieval and code intelligence. All Serena LSP features are directly accessible from the codebase object with a clean, intuitive interface.

## Quick Start

```python
from graph_sitter.enhanced import Codebase

# Initialize codebase with LSP
codebase = Codebase("./my-project")

# Get all errors - it's that simple!
errors = codebase.errors()
print(f"Found {len(errors.errors)} errors")
```

## Core Principles

- **Always Available**: LSP functionality is guaranteed to work, no optional fallbacks
- **Direct Access**: All methods are directly accessible from the codebase object
- **Lazy Loading**: LSP components are initialized only when first accessed
- **Consistent Returns**: All methods return standardized error/result objects
- **Performance**: Efficient caching and batching of LSP requests

## API Reference

### 🔍 Core Error Retrieval Commands

#### `codebase.errors() -> ErrorCollection`
Get all errors in the codebase.

```python
all_errors = codebase.errors()
print(f"Total errors: {all_errors.total_count}")
print(f"Critical errors: {all_errors.error_count}")
print(f"Warnings: {all_errors.warning_count}")
```

#### `codebase.full_error_context(error_id: str) -> ErrorContext`
Get full context for a specific error.

```python
if all_errors.errors:
    context = codebase.full_error_context(all_errors.errors[0].id)
    print(f"Error: {context.error.message}")
    print(f"Surrounding code:\n{context.surrounding_code}")
    print(f"Fix suggestions: {context.fix_suggestions}")
```

### 📋 Extended Error Retrieval API

#### Basic Error Operations

```python
# Errors in specific file
file_errors = codebase.errors_by_file("src/main.py")

# Filter by severity
critical_errors = codebase.errors_by_severity(ErrorSeverity.ERROR)
warnings = codebase.errors_by_severity(ErrorSeverity.WARNING)

# Filter by error type
syntax_errors = codebase.errors_by_type(ErrorType.SYNTAX)
import_errors = codebase.errors_by_type(ErrorType.IMPORT)

# Recent errors
from datetime import datetime, timedelta
one_hour_ago = datetime.now() - timedelta(hours=1)
recent = codebase.recent_errors(one_hour_ago)
```

#### Detailed Error Context

```python
# Get fix suggestions for specific error
suggestions = codebase.error_suggestions("error_123")
for suggestion in suggestions:
    print(f"Suggestion: {suggestion}")

# Get symbols related to error
symbols = codebase.error_related_symbols("error_123")
print(f"Related symbols: {symbols}")

# Get impact analysis
impact = codebase.error_impact_analysis("error_123")
print(f"Blocking: {impact.get('blocking', False)}")
print(f"Priority: {impact.get('priority', 'unknown')}")
```

#### Error Statistics & Analysis

```python
# Summary statistics
summary = codebase.error_summary()
print(f"Total errors: {summary.total_errors}")
print(f"Files with errors: {summary.files_with_errors}")

# Error trends over time
trends = codebase.error_trends()
print(f"Trend direction: {trends.get('direction', 'stable')}")

# Most common error types
common = codebase.most_common_errors()
for error_info in common:
    print(f"{error_info['type']}: {error_info['count']} occurrences")

# Error hotspots (files with most errors)
hotspots = codebase.error_hotspots()
for hotspot in hotspots:
    print(f"{hotspot['file_path']}: {hotspot['error_count']} errors")
```

### ⚡ Real-time Error Monitoring

```python
# Real-time error monitoring
def on_error_change(error_collection):
    print(f"Errors updated: {len(error_collection.errors)} total")
    if error_collection.error_count > 0:
        print(f"⚠️  {error_collection.error_count} critical errors!")

codebase.watch_errors(on_error_change)

# Stop monitoring
codebase.unwatch_errors(on_error_change)

# Force refresh
refreshed = codebase.refresh_errors()
print(f"Refreshed: {len(refreshed.errors)} errors")
```

### 🔧 Error Resolution & Actions

```python
# Auto-fix errors where possible
errors = codebase.errors()
fixable_errors = [e.id for e in errors.errors if e.has_quick_fix]
results = codebase.auto_fix_errors(fixable_errors)
print(f"Fixed {sum(results.values())} out of {len(results)} errors")

# Get available quick fixes
fixes = codebase.get_quick_fixes("error_123")
for fix in fixes:
    print(f"Fix: {fix.title} - {fix.description}")

# Apply specific fix
if fixes:
    success = codebase.apply_error_fix("error_123", fixes[0].id)
    print(f"Fix applied: {success}")
```

### 🚀 Full Serena LSP Feature Retrieval

#### Code Intelligence

```python
from graph_sitter.core.lsp_types import Position

# Code completions
pos = Position(line=10, character=5)
completions = codebase.completions("src/main.py", pos)
for comp in completions:
    print(f"Completion: {comp.label}")

# Hover information
hover = codebase.hover_info("src/main.py", pos)
if hover:
    print(f"Hover: {hover.contents}")

# Function signature help
sig_help = codebase.signature_help("src/main.py", pos)
if sig_help:
    print(f"Signatures: {len(sig_help.signatures)}")

# Go to definition
definitions = codebase.definitions("MyClass")
for definition in definitions:
    print(f"Definition: {definition.name} at {definition.location}")

# Find references
references = codebase.references("MyClass")
print(f"Found {len(references)} references to MyClass")
```

#### Code Actions & Refactoring

```python
from graph_sitter.core.lsp_types import Range, Position

# Available code actions
range_obj = Range(Position(10, 0), Position(10, 20))
actions = codebase.code_actions("src/main.py", range_obj)
for action in actions:
    print(f"Action: {action.get('title', 'Unknown')}")

# Rename symbol
success = codebase.rename_symbol("old_function", "new_function")
print(f"Rename successful: {success}")

# Extract method
range_obj = Range(Position(10, 0), Position(20, 0))
success = codebase.extract_method("src/main.py", range_obj)
print(f"Method extracted: {success}")

# Organize imports
success = codebase.organize_imports("src/main.py")
print(f"Imports organized: {success}")
```

#### Semantic Analysis

```python
# Semantic tokens
tokens = codebase.semantic_tokens("src/main.py")
print(f"Found {len(tokens)} semantic tokens")

# Document symbols
symbols = codebase.document_symbols("src/main.py")
for symbol in symbols:
    print(f"Symbol: {symbol.name} ({symbol.kind})")

# Workspace symbol search
symbols = codebase.workspace_symbols("MyClass")
print(f"Found {len(symbols)} symbols matching 'MyClass'")

# Call hierarchy
hierarchy = codebase.call_hierarchy("my_function")
print(f"Callers: {len(hierarchy.get('callers', []))}")
print(f"Callees: {len(hierarchy.get('callees', []))}")
```

### 🏥 Diagnostics & Health

```python
# All diagnostics (errors + warnings + info)
diagnostics = codebase.diagnostics()
print(f"Total diagnostics: {diagnostics.total_count}")

# Overall health check
health = codebase.health_check()
print(f"Overall score: {health.overall_score:.2f}")
print(f"LSP health: {health.lsp_health}")
for recommendation in health.recommendations:
    print(f"Recommendation: {recommendation}")

# LSP server status
status = codebase.lsp_status()
print(f"LSP running: {status.is_running}")
print(f"Server info: {status.server_info}")

# Available capabilities
capabilities = codebase.capabilities()
print(f"Completion: {capabilities.completion}")
print(f"Hover: {capabilities.hover}")
print(f"Diagnostics: {capabilities.diagnostics}")
```

## Complete Usage Example

```python
from graph_sitter.enhanced import Codebase, ErrorSeverity
from datetime import datetime, timedelta

def analyze_codebase(project_path):
    """Complete example of codebase analysis using the unified LSP API."""
    
    # Initialize codebase
    codebase = Codebase(project_path)
    print(f"Analyzing codebase: {codebase.name}")
    
    # Check LSP status
    status = codebase.lsp_status()
    if not status.is_running:
        print("❌ LSP server not running")
        return
    
    print("✅ LSP server running")
    
    # Get overall health
    health = codebase.health_check()
    print(f"📊 Overall health score: {health.overall_score:.2f}")
    
    # Get all errors
    errors = codebase.errors()
    print(f"🔍 Found {errors.total_count} total issues:")
    print(f"  - {errors.error_count} errors")
    print(f"  - {errors.warning_count} warnings")
    print(f"  - {errors.info_count} info messages")
    
    # Show error hotspots
    hotspots = codebase.error_hotspots()
    if hotspots:
        print("\n🔥 Error hotspots:")
        for hotspot in hotspots[:5]:  # Top 5
            print(f"  - {hotspot['file_path']}: {hotspot['error_count']} errors")
    
    # Show most common error types
    common_errors = codebase.most_common_errors()
    if common_errors:
        print("\n📈 Most common error types:")
        for error_type in common_errors[:3]:  # Top 3
            print(f"  - {error_type['type']}: {error_type['count']} occurrences")
    
    # Auto-fix what we can
    critical_errors = codebase.errors_by_severity(ErrorSeverity.ERROR)
    fixable = [e.id for e in critical_errors.errors if e.has_quick_fix]
    
    if fixable:
        print(f"\n🔧 Attempting to auto-fix {len(fixable)} errors...")
        results = codebase.auto_fix_errors(fixable)
        fixed_count = sum(results.values())
        print(f"✅ Successfully fixed {fixed_count} errors")
    
    # Set up real-time monitoring
    def on_error_change(error_collection):
        print(f"📡 Real-time update: {len(error_collection.errors)} total errors")
    
    print("\n📡 Starting real-time error monitoring...")
    codebase.watch_errors(on_error_change)
    
    # Show recommendations
    if health.recommendations:
        print("\n💡 Recommendations:")
        for rec in health.recommendations:
            print(f"  - {rec}")
    
    return codebase

# Run the analysis
if __name__ == "__main__":
    codebase = analyze_codebase("./my-project")
    
    # Keep monitoring for a while
    import time
    time.sleep(10)
    
    # Stop monitoring
    codebase.unwatch_errors(lambda x: None)
    print("Analysis complete!")
```

## Error Types and Severity Levels

### Error Severity

```python
from graph_sitter.core.lsp_types import ErrorSeverity

ErrorSeverity.ERROR    # Critical errors that prevent compilation/execution
ErrorSeverity.WARNING  # Warnings that should be addressed
ErrorSeverity.INFO     # Informational messages
ErrorSeverity.HINT     # Hints for code improvement
```

### Error Types

```python
from graph_sitter.core.lsp_types import ErrorType

ErrorType.SYNTAX      # Syntax errors
ErrorType.SEMANTIC    # Semantic errors
ErrorType.LINT        # Linting issues
ErrorType.TYPE_CHECK  # Type checking errors
ErrorType.IMPORT      # Import/module errors
ErrorType.UNDEFINED   # Undefined variables/functions
```

## Performance Considerations

- **Caching**: Error results are cached for 30 seconds by default
- **Lazy Loading**: LSP components are only initialized when first accessed
- **Batching**: Multiple LSP requests are batched for efficiency
- **Real-time Updates**: Monitoring uses efficient change detection

## Troubleshooting

### LSP Not Available

```python
status = codebase.lsp_status()
if not status.is_running:
    print(f"LSP Error: {status.error_message}")
    
    # Check capabilities
    caps = codebase.capabilities()
    print(f"Diagnostics available: {caps.diagnostics}")
```

### No Errors Returned

```python
# Force refresh
errors = codebase.refresh_errors()
if not errors.errors:
    print("No errors found - codebase is clean!")
else:
    print(f"Found {len(errors.errors)} errors after refresh")
```

### Performance Issues

```python
# Check cache hit rate (for debugging)
manager = codebase._lsp
print(f"Cache hits: {manager._cache_hits}")
print(f"Cache misses: {manager._cache_misses}")
print(f"Hit rate: {manager._cache_hits / (manager._cache_hits + manager._cache_misses):.2%}")
```

## Migration from Old APIs

If you're migrating from the old fragmented LSP APIs:

### Before (Old Fragmented API)
```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
from graph_sitter.core.diagnostics import CodebaseDiagnostics

# Multiple objects to manage
bridge = SerenaLSPBridge(repo_path)
manager = TransactionAwareLSPManager(repo_path)
diagnostics = CodebaseDiagnostics(codebase)

# Complex error retrieval
raw_errors = bridge.get_all_diagnostics()
# ... manual processing required
```

### After (New Unified API)
```python
from graph_sitter.enhanced import Codebase

# Single object with everything
codebase = Codebase(repo_path)

# Simple error retrieval
errors = codebase.errors()  # Just works!
```

## Best Practices

1. **Use the Enhanced Codebase**: Always import from `graph_sitter.enhanced` for full functionality
2. **Handle Errors Gracefully**: Check if errors exist before processing
3. **Use Real-time Monitoring**: Set up callbacks for long-running applications
4. **Leverage Auto-fix**: Use `auto_fix_errors()` for quick wins
5. **Monitor Health**: Regular health checks help maintain code quality
6. **Cache Awareness**: Understand that results are cached for performance

## Next Steps

- See [Error Retrieval Guide](error_retrieval_guide.md) for advanced error handling
- Check [Migration Guide](migration_guide.md) for upgrading from old APIs
- View [Examples](../examples/lsp_usage_examples.py) for more code samples

