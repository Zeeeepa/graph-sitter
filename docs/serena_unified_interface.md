# Unified Serena Error Interface

The Unified Serena Error Interface provides a comprehensive, consistent API for detecting, analyzing, and automatically fixing code errors through LSP (Language Server Protocol) integration.

## Overview

The unified interface consolidates all error-related functionality into a single, easy-to-use API that's directly available on the `Codebase` class. This eliminates the need to work with multiple scattered components and provides a streamlined experience for error management.

## Key Features

- **🔍 Comprehensive Error Detection**: Detects all types of errors from multiple LSP servers
- **🎯 Detailed Error Context**: Provides rich context information for each error
- **🔧 Automatic Error Resolution**: Safely applies fixes for common error patterns
- **⚡ Performance Optimized**: Uses lazy loading, caching, and batching for efficiency
- **🛡️ Graceful Error Handling**: Degrades gracefully when LSP is not available
- **🔄 Real-time Updates**: Supports background error monitoring and callbacks

## Quick Start

```python
from graph_sitter import Codebase

# Initialize codebase with full LSP integration
codebase = Codebase("./my-project")

# Get all errors with one simple call
all_errors = codebase.errors()
print(f"Found {len(all_errors)} errors")

# Get detailed context for any error
if all_errors:
    context = codebase.full_error_context(all_errors[0].id)
    print(f"Error context: {context.surrounding_code}")

# Auto-fix all fixable errors
results = codebase.resolve_errors()
successful_fixes = [r for r in results if r.success]
print(f"Successfully fixed {len(successful_fixes)} errors")

# Fix a specific error
if all_errors:
    result = codebase.resolve_error(all_errors[0].id)
    if result.success:
        print(f"Fixed error: {result.message}")
```

## API Reference

### Core Methods

#### `codebase.errors()`

Get all errors in the codebase with optional filtering.

```python
def errors(
    include_warnings: bool = True,
    include_hints: bool = False,
    file_path: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None
) -> List[UnifiedError]:
```

**Parameters:**
- `include_warnings`: Include warnings in results (default: True)
- `include_hints`: Include hints/info messages (default: False)
- `file_path`: Filter by specific file path
- `category`: Filter by error category ("syntax", "type", "import", etc.)
- `source`: Filter by error source ("pylsp", "mypy", "ruff", etc.)

**Returns:** List of `UnifiedError` objects

**Examples:**
```python
# Get all errors and warnings
all_issues = codebase.errors()

# Get only critical errors
critical_errors = codebase.errors(include_warnings=False)

# Get errors in a specific file
file_errors = codebase.errors(file_path="src/main.py")

# Get only syntax errors
syntax_errors = codebase.errors(category="syntax")

# Get errors from a specific tool
mypy_errors = codebase.errors(source="mypy")
```

#### `codebase.full_error_context(error_id)`

Get comprehensive context information for a specific error.

```python
def full_error_context(error_id: str) -> Optional[ErrorContext]:
```

**Parameters:**
- `error_id`: ID of the error to analyze

**Returns:** `ErrorContext` object with detailed information, or `None` if error not found

**Example:**
```python
errors = codebase.errors()
if errors:
    context = codebase.full_error_context(errors[0].id)
    if context:
        print(f"Surrounding code:\n{context.surrounding_code}")
        print(f"Function context: {context.function_context}")
        print(f"Recommended fixes: {len(context.recommended_fixes)}")
```

#### `codebase.resolve_errors()`

Automatically resolve multiple errors.

```python
def resolve_errors(
    error_ids: Optional[List[str]] = None,
    auto_fixable_only: bool = True,
    max_fixes: Optional[int] = None
) -> List[ErrorResolutionResult]:
```

**Parameters:**
- `error_ids`: Specific error IDs to resolve, or None for all eligible errors
- `auto_fixable_only`: Only attempt high-confidence fixes (default: True)
- `max_fixes`: Maximum number of fixes to apply for safety

**Returns:** List of `ErrorResolutionResult` objects

**Example:**
```python
# Fix all auto-fixable errors (safest)
results = codebase.resolve_errors()

# Fix specific errors
error_ids = [error.id for error in codebase.errors()[:5]]
results = codebase.resolve_errors(error_ids=error_ids)

# Fix with safety limit
results = codebase.resolve_errors(max_fixes=10)

# Check results
successful = [r for r in results if r.success]
print(f"Successfully fixed {len(successful)} errors")
```

#### `codebase.resolve_error(error_id)`

Resolve a specific error by ID.

```python
def resolve_error(error_id: str) -> ErrorResolutionResult:
```

**Parameters:**
- `error_id`: ID of the error to resolve

**Returns:** `ErrorResolutionResult` object

**Example:**
```python
errors = codebase.errors()
if errors:
    result = codebase.resolve_error(errors[0].id)
    if result.success:
        print(f"✅ Fixed: {result.message}")
        print(f"Modified files: {result.files_modified}")
    else:
        print(f"❌ Failed: {result.message}")
```

### Utility Methods

#### `codebase.error_summary()`

Get a comprehensive summary of all errors in the codebase.

```python
def error_summary() -> ErrorSummary:
```

**Returns:** `ErrorSummary` object with statistics

**Example:**
```python
summary = codebase.error_summary()
print(f"Total errors: {summary.total_errors}")
print(f"Total warnings: {summary.total_warnings}")
print(f"Auto-fixable: {summary.auto_fixable}")
print(f"Error hotspots: {summary.error_hotspots}")
```

#### `codebase.get_fixable_errors()`

Get all errors that can be automatically fixed.

```python
def get_fixable_errors(auto_fixable_only: bool = True) -> List[UnifiedError]:
```

**Parameters:**
- `auto_fixable_only`: Only return high-confidence fixable errors

**Returns:** List of fixable `UnifiedError` objects

#### `codebase.preview_fix(error_id)`

Preview what would happen if an error were fixed.

```python
def preview_fix(error_id: str) -> Dict[str, Any]:
```

**Parameters:**
- `error_id`: ID of the error to preview

**Returns:** Dictionary with fix preview information

**Example:**
```python
errors = codebase.get_fixable_errors()
if errors:
    preview = codebase.preview_fix(errors[0].id)
    if preview['can_resolve']:
        print(f"Fix: {preview['fix_title']}")
        print(f"Confidence: {preview['confidence']}")
        print(f"Impact: {preview['estimated_impact']}")
```

#### `codebase.refresh_errors()`

Refresh error information from LSP servers.

```python
def refresh_errors(file_path: Optional[str] = None) -> None:
```

**Parameters:**
- `file_path`: Specific file to refresh, or None for all files

## Data Models

### UnifiedError

Represents a single error with comprehensive information.

```python
@dataclass
class UnifiedError:
    id: str                          # Unique error identifier
    message: str                     # Error message
    severity: ErrorSeverity          # ERROR, WARNING, INFO, HINT
    category: ErrorCategory          # SYNTAX, TYPE, IMPORT, etc.
    location: ErrorLocation          # File path, line, character
    source: str                      # "pylsp", "mypy", "ruff", etc.
    code: Optional[str]              # Error code if available
    
    # Context information
    context_lines: List[str]         # Surrounding code lines
    related_symbols: List[RelatedSymbol]  # Related symbols
    dependency_chain: List[str]      # Dependency information
    
    # Fix information
    fixes: List[ErrorFix]            # Available fixes
    has_auto_fix: bool               # Has high-confidence fixes
    
    # Properties
    @property
    def is_error(self) -> bool       # True if severity is ERROR
    
    @property
    def is_warning(self) -> bool     # True if severity is WARNING
    
    @property
    def is_fixable(self) -> bool     # True if fixes are available
    
    @property
    def auto_fixable(self) -> bool   # True if high-confidence fixes available
```

### ErrorContext

Comprehensive context information for an error.

```python
@dataclass
class ErrorContext:
    error: UnifiedError              # The original error
    
    # Code context
    surrounding_code: str            # Code around the error
    function_context: Optional[Dict] # Function information
    class_context: Optional[Dict]    # Class information
    
    # Symbol analysis
    symbol_definitions: List[Dict]   # Symbol definitions
    symbol_usages: List[Dict]        # Symbol usages
    
    # Related errors
    related_errors: List[UnifiedError]    # Related errors
    similar_errors: List[UnifiedError]    # Similar errors
    
    # Impact analysis
    affected_functions: List[str]    # Functions that might be affected
    affected_classes: List[str]      # Classes that might be affected
    affected_files: List[str]        # Files that might be affected
    
    # Fix recommendations
    recommended_fixes: List[ErrorFix]     # Recommended fixes
    fix_priority: str                # "low", "medium", "high", "critical"
```

### ErrorResolutionResult

Result of an error resolution attempt.

```python
@dataclass
class ErrorResolutionResult:
    error_id: str                    # ID of the error that was processed
    success: bool                    # Whether the fix was successful
    message: str                     # Human-readable result message
    applied_fixes: List[str]         # IDs of fixes that were applied
    remaining_issues: List[str]      # Issues that still need attention
    files_modified: List[str]        # Files that were modified
```

### ErrorSummary

Summary statistics for all errors in the codebase.

```python
@dataclass
class ErrorSummary:
    total_errors: int                # Number of errors
    total_warnings: int              # Number of warnings
    total_info: int                  # Number of info messages
    total_hints: int                 # Number of hints
    
    # By category
    by_category: Dict[str, int]      # Error counts by category
    by_file: Dict[str, int]          # Error counts by file
    by_source: Dict[str, int]        # Error counts by source
    
    # Fixable errors
    auto_fixable: int                # Number of auto-fixable errors
    manually_fixable: int            # Number of manually fixable errors
    unfixable: int                   # Number of unfixable errors
    
    # Top issues
    most_common_errors: List[Dict]   # Most common error messages
    error_hotspots: List[Dict]       # Files with most errors
    
    @property
    def total_issues(self) -> int    # Total number of all issues
    
    @property
    def critical_issues(self) -> int # Number of critical issues (errors only)
```

## Error Categories

The interface automatically categorizes errors into these types:

- **SYNTAX**: Syntax errors, invalid syntax, parsing errors
- **TYPE**: Type mismatches, incompatible types, type annotations
- **IMPORT**: Import errors, missing modules, circular imports
- **UNDEFINED**: Undefined variables, functions, or classes
- **UNUSED**: Unused imports, variables, or functions
- **STYLE**: Code style issues, formatting, conventions
- **SECURITY**: Security vulnerabilities, unsafe operations
- **PERFORMANCE**: Performance issues, inefficient code
- **LOGIC**: Logic errors that static analysis can detect
- **COMPATIBILITY**: Compatibility issues between versions
- **OTHER**: Other types of errors

## Error Sources

Errors can come from various LSP servers and tools:

- **pylsp**: Python LSP Server (general Python errors)
- **mypy**: Static type checker
- **ruff**: Fast Python linter
- **flake8**: Style guide enforcement
- **black**: Code formatter
- **isort**: Import sorter
- **bandit**: Security linter
- **Custom**: Custom error sources

## Performance Characteristics

The unified interface is designed for performance:

- **Lazy Loading**: Components are initialized only when first accessed
- **Intelligent Caching**: Results are cached with smart invalidation
- **Background Refresh**: Errors are updated in the background
- **Batching**: Multiple operations are batched for efficiency
- **Streaming**: Large result sets can be processed incrementally

### Performance Targets

| Project Size | Files | Get All Errors | Get Summary | Cache Speedup |
|--------------|-------|----------------|-------------|---------------|
| Small        | 5-10  | < 2s          | < 1s        | 2x+           |
| Medium       | 20-50 | < 5s          | < 2s        | 2x+           |
| Large        | 100+  | < 10s         | < 5s        | 2x+           |

## Error Handling and Graceful Degradation

The interface handles various failure scenarios gracefully:

### LSP Not Available
```python
# Still works, returns empty results
errors = codebase.errors()  # Returns []
summary = codebase.error_summary()  # Returns default summary
```

### Partial LSP Functionality
```python
# Some features work, others degrade gracefully
errors = codebase.errors()  # May return limited results
context = codebase.full_error_context(error_id)  # May return None
```

### Network/Performance Issues
```python
# Timeouts and retries are handled automatically
# Cached results are used when available
# Background refresh continues in the background
```

## Best Practices

### 1. Start with Error Detection
```python
# Always start by understanding what errors exist
errors = codebase.errors()
summary = codebase.error_summary()

print(f"Found {summary.total_errors} errors, {summary.auto_fixable} auto-fixable")
```

### 2. Use Filtering for Large Codebases
```python
# Focus on specific types of errors
critical_errors = codebase.errors(include_warnings=False)
syntax_errors = codebase.errors(category="syntax")
file_errors = codebase.errors(file_path="src/problematic_file.py")
```

### 3. Preview Before Fixing
```python
# Always preview fixes before applying them
fixable_errors = codebase.get_fixable_errors()
for error in fixable_errors:
    preview = codebase.preview_fix(error.id)
    if preview['can_resolve'] and preview['confidence'] == 'high':
        print(f"Safe to fix: {preview['fix_title']}")
```

### 4. Use Safety Limits
```python
# Apply safety limits when auto-fixing
results = codebase.resolve_errors(
    auto_fixable_only=True,  # Only high-confidence fixes
    max_fixes=10             # Limit number of fixes
)
```

### 5. Handle Results Properly
```python
results = codebase.resolve_errors()

successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]

print(f"✅ Fixed {len(successful)} errors")
for result in failed:
    print(f"❌ Failed to fix {result.error_id}: {result.message}")
```

### 6. Use Context for Complex Errors
```python
# Get detailed context for errors that need manual attention
complex_errors = [e for e in codebase.errors() if not e.auto_fixable]
for error in complex_errors:
    context = codebase.full_error_context(error.id)
    if context:
        print(f"Error: {error.message}")
        print(f"Function: {context.function_context}")
        print(f"Recommendations: {len(context.recommended_fixes)}")
```

## Integration Examples

### CI/CD Integration
```python
#!/usr/bin/env python3
"""CI/CD error checking script."""

from graph_sitter import Codebase
import sys

def main():
    codebase = Codebase(".")
    
    # Get all errors
    errors = codebase.errors(include_warnings=False)  # Only errors
    
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  {error.location}: {error.message}")
        sys.exit(1)
    else:
        print("✅ No errors found")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Pre-commit Hook
```python
#!/usr/bin/env python3
"""Pre-commit hook for auto-fixing errors."""

from graph_sitter import Codebase

def main():
    codebase = Codebase(".")
    
    # Auto-fix safe errors
    results = codebase.resolve_errors(
        auto_fixable_only=True,
        max_fixes=20
    )
    
    successful = [r for r in results if r.success]
    if successful:
        print(f"🔧 Auto-fixed {len(successful)} errors")
        
        # Refresh to get updated error count
        codebase.refresh_errors()
        remaining_errors = codebase.errors(include_warnings=False)
        
        if remaining_errors:
            print(f"⚠️  {len(remaining_errors)} errors still need manual attention")
        else:
            print("✅ All errors resolved!")

if __name__ == "__main__":
    main()
```

### IDE Integration
```python
"""IDE plugin integration example."""

class SerenaIDEPlugin:
    def __init__(self, project_path):
        self.codebase = Codebase(project_path)
        
        # Set up real-time error callbacks
        self.codebase.add_error_callback(self.on_errors_updated)
    
    def on_errors_updated(self, errors):
        """Called when errors are updated in real-time."""
        # Update IDE error markers
        self.update_error_markers(errors)
    
    def get_file_errors(self, file_path):
        """Get errors for a specific file."""
        return self.codebase.errors(file_path=file_path)
    
    def get_error_context(self, error_id):
        """Get context for error tooltip."""
        return self.codebase.full_error_context(error_id)
    
    def apply_quick_fix(self, error_id):
        """Apply quick fix for an error."""
        preview = self.codebase.preview_fix(error_id)
        if preview['can_resolve'] and preview['confidence'] == 'high':
            return self.codebase.resolve_error(error_id)
        return None
```

## Troubleshooting

### Common Issues

#### "No errors found but I know there are errors"
- Check if LSP servers are properly installed and configured
- Verify that the project has the correct file extensions (.py, .js, etc.)
- Try refreshing errors: `codebase.refresh_errors()`

#### "Error resolution fails"
- Check if files are writable
- Verify that the error is actually auto-fixable: `error.auto_fixable`
- Preview the fix first: `codebase.preview_fix(error_id)`

#### "Performance is slow"
- Use filtering to reduce the scope: `codebase.errors(file_path="specific_file.py")`
- Check if background refresh is enabled
- Consider the project size and complexity

#### "Context information is missing"
- Ensure LSP servers are running and responsive
- Check if the file exists and is readable
- Try refreshing: `codebase.refresh_errors()`

### Debug Information

```python
# Get debug information about the error interface
if hasattr(codebase, '_get_error_interface'):
    interface = codebase._get_error_interface()
    
    # Check initialization status
    print(f"Initialized: {interface._initialized}")
    
    # Get resolution statistics
    if hasattr(interface, 'get_resolution_stats'):
        stats = interface.get_resolution_stats()
        print(f"Resolution stats: {stats}")
```

## Migration Guide

### From Scattered Serena Components

**Before:**
```python
from graph_sitter.extensions.serena.error_analysis import ComprehensiveErrorAnalyzer
from graph_sitter.extensions.serena.advanced_error_viewer import AdvancedErrorViewer

analyzer = ComprehensiveErrorAnalyzer(codebase)
viewer = AdvancedErrorViewer(codebase)

errors = analyzer.get_all_errors()
context = viewer.view_error_comprehensive(errors[0])
```

**After:**
```python
from graph_sitter import Codebase

codebase = Codebase(".")

errors = codebase.errors()
context = codebase.full_error_context(errors[0].id)
```

### From Direct LSP Integration

**Before:**
```python
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

bridge = SerenaLSPBridge(".")
diagnostics = bridge.get_diagnostics()
```

**After:**
```python
from graph_sitter import Codebase

codebase = Codebase(".")
errors = codebase.errors()  # Automatically uses LSP bridge
```

## Contributing

The unified error interface is designed to be extensible. You can contribute by:

1. **Adding new error sources**: Implement new LSP server integrations
2. **Improving fix patterns**: Add new automatic fix patterns
3. **Enhancing context analysis**: Improve symbol and dependency analysis
4. **Performance optimization**: Optimize caching and batching strategies

See the [Contributing Guide](../CONTRIBUTING.md) for more details.

## License

This unified interface is part of the graph-sitter project and is licensed under the same terms.

