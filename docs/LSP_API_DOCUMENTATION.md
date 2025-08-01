# Comprehensive LSP Error Retrieval API Documentation

## Overview

The Graph-Sitter Codebase class now provides a comprehensive LSP (Language Server Protocol) error retrieval API that makes all Serena LSP features easily retrievable directly from the codebase object. This unified interface provides real-time error detection, analysis, and resolution capabilities.

## Quick Start

```python
from graph_sitter import Codebase

# Initialize codebase with full LSP capabilities
codebase = Codebase("./my-project")

# Get all errors with one simple call
all_errors = codebase.errors()
print(f"Found {len(all_errors)} errors")

# Get detailed context for any error
if all_errors:
    context = codebase.full_error_context(all_errors[0].id)
    suggestions = codebase.error_suggestions(all_errors[0].id)

# Auto-fix errors where possible
fixable_errors = [e for e in all_errors if e.has_quick_fix]
codebase.auto_fix_errors([e.id for e in fixable_errors])

# Real-time error monitoring
codebase.watch_errors(lambda errors: print(f"Errors updated: {len(errors)}"))

# Full code intelligence
completions = codebase.completions("src/main.py", (10, 5))
hover = codebase.hover_info("src/main.py", (15, 10))
```

## API Reference

### 🔍 Core Error Retrieval Commands

#### `errors()`
Get all errors in the codebase.

```python
all_errors = codebase.errors()
# Returns: List[DiagnosticInfo] - All errors across the codebase
```

#### `errors_by_file(file_path: str)`
Get errors in a specific file.

```python
file_errors = codebase.errors_by_file("src/main.py")
# Returns: List[DiagnosticInfo] - Errors in the specified file
```

#### `errors_by_severity(severity: str)`
Filter errors by severity level.

```python
critical_errors = codebase.errors_by_severity("ERROR")
warnings = codebase.errors_by_severity("WARNING")
info_messages = codebase.errors_by_severity("INFO")
# Returns: List[DiagnosticInfo] - Errors matching the severity level
```

#### `errors_by_type(error_type: str)`
Filter errors by type.

```python
syntax_errors = codebase.errors_by_type("syntax")
semantic_errors = codebase.errors_by_type("semantic")
lint_errors = codebase.errors_by_type("lint")
# Returns: List[DiagnosticInfo] - Errors matching the specified type
```

#### `recent_errors(since_timestamp: float)`
Get recent errors since a timestamp.

```python
import time
recent_errors = codebase.recent_errors(time.time() - 3600)  # Last hour
# Returns: List[DiagnosticInfo] - Errors since the timestamp
```

### 📋 Detailed Error Context

#### `full_error_context(error_id: str)`
Get comprehensive context for a specific error.

```python
error_context = codebase.full_error_context("error_123")
# Returns: Dict with keys:
# - error: DiagnosticInfo object
# - file_path: str
# - line: int
# - character: int
# - message: str
# - severity: int
# - source: str
# - code: str
# - context_lines: Dict with before/error_line/after
```

#### `error_suggestions(error_id: str)`
Get fix suggestions for an error.

```python
suggestions = codebase.error_suggestions("error_123")
# Returns: List[str] - Human-readable fix suggestions
```

#### `error_related_symbols(error_id: str)`
Get symbols related to the error.

```python
related_symbols = codebase.error_related_symbols("error_123")
# Returns: List[str] - Symbol names related to the error
```

#### `error_impact_analysis(error_id: str)`
Get impact analysis of the error.

```python
impact = codebase.error_impact_analysis("error_123")
# Returns: Dict with keys:
# - severity_impact: str ("High", "Medium", "Low")
# - affected_file: str
# - potential_cascade: bool
# - fix_complexity: str ("Simple", "Complex")
```

### 📊 Error Statistics & Analysis

#### `error_summary()`
Get summary statistics of all errors.

```python
summary = codebase.error_summary()
# Returns: Dict with keys:
# - total_diagnostics: int
# - error_count: int
# - warning_count: int
# - info_count: int
# - files_with_errors: int
# - most_common_source: str
```

#### `error_trends()`
Get error trends over time.

```python
trends = codebase.error_trends()
# Returns: Dict with keys:
# - current_snapshot: Dict (error summary)
# - trend: str ("increasing", "decreasing", "stable")
# - timestamp: float
```

#### `most_common_errors()`
Get most frequently occurring errors.

```python
common_errors = codebase.most_common_errors()
# Returns: List[Dict] with keys:
# - message: str
# - count: int
```

#### `error_hotspots()`
Get files/areas with most errors.

```python
hotspots = codebase.error_hotspots()
# Returns: List[Dict] with keys:
# - file_path: str
# - error_count: int
```

### ⚡ Real-time Error Monitoring

#### `watch_errors(callback: Callable)`
Set up real-time error monitoring.

```python
def on_error_change(errors):
    print(f"Errors updated: {len(errors)} total errors")

success = codebase.watch_errors(on_error_change)
# Returns: bool - True if monitoring was set up successfully
```

#### `error_stream()`
Get a stream of error updates.

```python
for errors in codebase.error_stream():
    print(f"Current errors: {len(errors)}")
    if len(errors) == 0:
        break
# Returns: Generator[List[DiagnosticInfo]] - Stream of error updates
```

#### `refresh_errors()`
Force refresh of error detection.

```python
refreshed = codebase.refresh_errors()
# Returns: bool - True if refresh was successful
```

### 🔧 Error Resolution & Actions

#### `auto_fix_errors(error_ids: List[str])`
Auto-fix specific errors.

```python
fixed_errors = codebase.auto_fix_errors(["error_123", "error_456"])
# Returns: List[str] - IDs of successfully fixed errors
```

#### `get_quick_fixes(error_id: str)`
Get available quick fixes for an error.

```python
fixes = codebase.get_quick_fixes("error_123")
# Returns: List[Dict] with keys:
# - id: str
# - title: str
# - description: str
```

#### `apply_error_fix(error_id: str, fix_id: str)`
Apply a specific fix to resolve an error.

```python
success = codebase.apply_error_fix("error_123", "fix_456")
# Returns: bool - True if fix was applied successfully
```

### 🚀 Full Serena LSP Feature Retrieval

#### `completions(file_path: str, position: Tuple[int, int])`
Get code completions at the specified position.

```python
completions = codebase.completions("src/main.py", (10, 5))
# Returns: List[CompletionItem] - Available code completions
```

#### `hover_info(file_path: str, position: Tuple[int, int])`
Get hover information at the specified position.

```python
hover = codebase.hover_info("src/main.py", (10, 5))
# Returns: Dict or None with hover information
```

#### `signature_help(file_path: str, position: Tuple[int, int])`
Get function signature help at the specified position.

```python
signature = codebase.signature_help("src/main.py", (10, 5))
# Returns: Dict with keys:
# - signatures: List[SignatureInfo]
# - active_signature: int
# - active_parameter: int
```

#### `definitions(symbol_name: str)`
Go to definition for a symbol.

```python
definitions = codebase.definitions("MyClass")
# Returns: List[Dict] with keys:
# - file_path: str
# - line: int
# - character: int
```

#### `references(symbol_name: str)`
Find all references to a symbol.

```python
references = codebase.references("MyClass")
# Returns: List[Dict] with keys:
# - file_path: str
# - line: int
# - character: int
```

### 🔄 Code Actions & Refactoring

#### `code_actions(file_path: str, range_obj: Dict)`
Get available code actions for a file range.

```python
actions = codebase.code_actions("src/main.py", {
    "start": {"line": 10, "character": 0},
    "end": {"line": 15, "character": 0}
})
# Returns: List[Dict] with keys:
# - title: str
# - kind: str
# - command: str
```

#### `rename_symbol(old_name: str, new_name: str)`
Rename a symbol throughout the codebase.

```python
result = codebase.rename_symbol("old_function", "new_function")
# Returns: Dict with keys:
# - changes: List[Dict] - File changes to be made
# - success: bool
```

#### `extract_method(file_path: str, range_obj: Dict)`
Extract method refactoring.

```python
result = codebase.extract_method("src/main.py", {
    "start": {"line": 10, "character": 0},
    "end": {"line": 20, "character": 0}
})
# Returns: Dict with keys:
# - success: bool
# - new_method_name: str
# - changes: List[Dict]
```

#### `organize_imports(file_path: str)`
Organize imports in a file.

```python
result = codebase.organize_imports("src/main.py")
# Returns: Dict with keys:
# - success: bool
# - changes: List[Dict]
```

### 🔍 Semantic Analysis

#### `semantic_tokens(file_path: str)`
Get semantic token information for a file.

```python
tokens = codebase.semantic_tokens("src/main.py")
# Returns: List[Dict] with keys:
# - line: int
# - character: int
# - length: int
# - token_type: str
# - token_modifiers: List[str]
```

#### `document_symbols(file_path: str)`
Get document symbol outline for a file.

```python
symbols = codebase.document_symbols("src/main.py")
# Returns: List[Dict] with keys:
# - name: str
# - kind: str
# - line: int
# - character: int
```

#### `workspace_symbols(query: str)`
Search workspace symbols.

```python
symbols = codebase.workspace_symbols("MyClass")
# Returns: List[Dict] with keys:
# - name: str
# - kind: str
# - file_path: str
# - line: int
```

#### `call_hierarchy(symbol_name: str)`
Get call hierarchy for a symbol.

```python
hierarchy = codebase.call_hierarchy("my_function")
# Returns: Dict with keys:
# - incoming_calls: List[Dict] - Who calls this symbol
# - outgoing_calls: List[Dict] - What this symbol calls
```

### 📊 Diagnostics & Health

#### `diagnostics()`
Get all diagnostics (errors + warnings + info).

```python
all_diagnostics = codebase.diagnostics()
# Returns: List[DiagnosticInfo] - All diagnostics
```

#### `health_check()`
Get overall codebase health assessment.

```python
health = codebase.health_check()
# Returns: Dict with keys:
# - health_score: int (0-100)
# - health_status: str ("Excellent", "Good", "Fair", "Poor")
# - error_summary: Dict
# - recommendations: List[str]
# - comprehensive_metrics: Dict (if available)
```

#### `lsp_status()`
Get LSP server status.

```python
status = codebase.lsp_status()
# Returns: Dict with keys:
# - lsp_available: bool
# - servers: List[str]
# - capabilities: List[str]
# - initialized: bool (if available)
```

#### `capabilities()`
Get available LSP capabilities.

```python
caps = codebase.capabilities()
# Returns: Dict with keys:
# - error_retrieval: bool
# - code_intelligence: bool
# - refactoring: bool
# - semantic_analysis: bool
# - real_time_monitoring: bool
# - auto_fix: bool
# - lsp_diagnostics: bool
# - serena_integration: bool
# - deep_analysis: bool
```

## Complete Usage Examples

### Basic Error Analysis

```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./my-project")

# Get comprehensive error overview
summary = codebase.error_summary()
print(f"Total diagnostics: {summary['total_diagnostics']}")
print(f"Errors: {summary['error_count']}")
print(f"Warnings: {summary['warning_count']}")
print(f"Files affected: {summary['files_with_errors']}")

# Find error hotspots
hotspots = codebase.error_hotspots()
print("Files with most errors:")
for hotspot in hotspots[:5]:
    print(f"  {hotspot['file_path']}: {hotspot['error_count']} errors")

# Get most common error types
common_errors = codebase.most_common_errors()
print("Most common errors:")
for error in common_errors[:3]:
    print(f"  {error['message']} (occurs {error['count']} times)")
```

### Advanced Error Context Analysis

```python
# Get all critical errors
critical_errors = codebase.errors_by_severity("ERROR")

for error in critical_errors[:5]:  # Analyze first 5 critical errors
    # Get full context
    context = codebase.full_error_context(error.id)
    if context:
        print(f"Error in {context['file_path']} at line {context['line']}")
        print(f"Message: {context['message']}")
        
        # Get fix suggestions
        suggestions = codebase.error_suggestions(error.id)
        if suggestions:
            print("Suggested fixes:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        
        # Analyze impact
        impact = codebase.error_impact_analysis(error.id)
        print(f"Impact: {impact['severity_impact']}, Complexity: {impact['fix_complexity']}")
        print()
```

### Real-time Error Monitoring

```python
import time

# Set up real-time monitoring
def error_monitor(errors):
    error_count = len([e for e in errors if e.severity == 1])
    warning_count = len([e for e in errors if e.severity == 2])
    print(f"[{time.strftime('%H:%M:%S')}] Errors: {error_count}, Warnings: {warning_count}")

# Start monitoring
codebase.watch_errors(error_monitor)

# Or use error stream
print("Monitoring error stream...")
for errors in codebase.error_stream():
    if len(errors) == 0:
        print("✅ No errors detected!")
        break
    else:
        print(f"⚠️  {len(errors)} issues detected")
```

### Automated Error Resolution

```python
# Get all errors that can be auto-fixed
all_errors = codebase.errors()
fixable_errors = []

for error in all_errors:
    quick_fixes = codebase.get_quick_fixes(error.id)
    if quick_fixes:
        fixable_errors.append(error.id)
        print(f"Can fix: {error.message}")
        for fix in quick_fixes:
            print(f"  - {fix['title']}: {fix['description']}")

# Auto-fix all fixable errors
if fixable_errors:
    print(f"Attempting to auto-fix {len(fixable_errors)} errors...")
    fixed = codebase.auto_fix_errors(fixable_errors)
    print(f"Successfully fixed {len(fixed)} errors")
```

### Code Intelligence Integration

```python
# Get completions for a specific position
completions = codebase.completions("src/main.py", (25, 10))
print(f"Available completions: {len(completions)}")

# Get hover information
hover = codebase.hover_info("src/main.py", (25, 10))
if hover:
    print(f"Hover info: {hover}")

# Find all references to a symbol
references = codebase.references("MyClass")
print(f"Found {len(references)} references to MyClass:")
for ref in references:
    print(f"  {ref['file_path']}:{ref['line']}")

# Get call hierarchy
hierarchy = codebase.call_hierarchy("process_data")
print(f"Incoming calls: {len(hierarchy['incoming_calls'])}")
print(f"Outgoing calls: {len(hierarchy['outgoing_calls'])}")
```

### Health Monitoring Dashboard

```python
# Create a comprehensive health dashboard
def print_health_dashboard():
    print("=" * 60)
    print("CODEBASE HEALTH DASHBOARD")
    print("=" * 60)
    
    # Overall health
    health = codebase.health_check()
    print(f"Overall Health: {health['health_status']} ({health['health_score']}/100)")
    
    # Error summary
    summary = health['error_summary']
    print(f"Total Issues: {summary['total_diagnostics']}")
    print(f"  - Errors: {summary['error_count']}")
    print(f"  - Warnings: {summary['warning_count']}")
    print(f"  - Info: {summary['info_count']}")
    
    # Recommendations
    if health['recommendations']:
        print("\nRecommendations:")
        for rec in health['recommendations']:
            print(f"  • {rec}")
    
    # LSP Status
    lsp_status = codebase.lsp_status()
    print(f"\nLSP Status: {'✅ Available' if lsp_status['lsp_available'] else '❌ Not Available'}")
    
    # Capabilities
    caps = codebase.capabilities()
    print("\nAvailable Capabilities:")
    for cap, available in caps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {cap.replace('_', ' ').title()}")
    
    print("=" * 60)

# Run the dashboard
print_health_dashboard()
```

## Integration with Existing Workflows

### CI/CD Integration

```python
#!/usr/bin/env python3
"""
CI/CD Error Check Script
Run this in your CI pipeline to check for errors
"""

from graph_sitter import Codebase
import sys

def ci_error_check():
    codebase = Codebase(".")
    
    # Get error summary
    summary = codebase.error_summary()
    
    # Check for critical errors
    critical_errors = codebase.errors_by_severity("ERROR")
    
    if critical_errors:
        print(f"❌ CI FAILED: {len(critical_errors)} critical errors found")
        
        # Show first 5 errors with context
        for error in critical_errors[:5]:
            context = codebase.full_error_context(error.id)
            if context:
                print(f"  {context['file_path']}:{context['line']} - {context['message']}")
        
        return 1  # Exit with error
    
    # Check warning threshold
    warnings = codebase.errors_by_severity("WARNING")
    if len(warnings) > 10:  # Configurable threshold
        print(f"⚠️  CI WARNING: {len(warnings)} warnings found (threshold: 10)")
    
    print(f"✅ CI PASSED: {summary['total_diagnostics']} total diagnostics")
    return 0

if __name__ == "__main__":
    sys.exit(ci_error_check())
```

### IDE Integration

```python
"""
IDE Plugin Integration Example
This shows how to integrate the LSP API with an IDE plugin
"""

class IDELSPIntegration:
    def __init__(self, project_path):
        self.codebase = Codebase(project_path)
        self.setup_real_time_monitoring()
    
    def setup_real_time_monitoring(self):
        """Set up real-time error monitoring for IDE"""
        def on_errors_changed(errors):
            # Update IDE error markers
            self.update_error_markers(errors)
            
            # Update problem panel
            self.update_problem_panel(errors)
        
        self.codebase.watch_errors(on_errors_changed)
    
    def update_error_markers(self, errors):
        """Update error markers in editor"""
        for error in errors:
            # Add red squiggly lines for errors
            if error.severity == 1:  # Error
                self.add_error_marker(error.file_path, error.line, error.message)
            elif error.severity == 2:  # Warning
                self.add_warning_marker(error.file_path, error.line, error.message)
    
    def get_hover_info(self, file_path, line, character):
        """Get hover information for IDE"""
        return self.codebase.hover_info(file_path, (line, character))
    
    def get_completions(self, file_path, line, character):
        """Get code completions for IDE"""
        return self.codebase.completions(file_path, (line, character))
    
    def get_quick_fixes(self, file_path, line):
        """Get quick fixes for IDE"""
        # Find error at this location
        file_errors = self.codebase.errors_by_file(file_path)
        for error in file_errors:
            if error.line == line:
                return self.codebase.get_quick_fixes(error.id)
        return []

# Usage in IDE plugin
ide_integration = IDELSPIntegration("/path/to/project")
```

## Performance Considerations

The LSP API is designed with performance in mind:

- **Lazy Loading**: LSP features are initialized only when first accessed
- **Caching**: Diagnostics and other frequently accessed data are cached
- **Background Processing**: Real-time monitoring runs in the background
- **Efficient Updates**: Only changed diagnostics trigger callbacks

## Troubleshooting

### Common Issues

1. **LSP Not Available**: Check that Serena dependencies are installed
2. **No Errors Detected**: Ensure LSP server is properly initialized
3. **Performance Issues**: Check if real-time monitoring is needed

### Debug Information

```python
# Check LSP status
status = codebase.lsp_status()
print(f"LSP Available: {status['lsp_available']}")
print(f"Servers: {status['servers']}")

# Check capabilities
caps = codebase.capabilities()
for cap, available in caps.items():
    print(f"{cap}: {available}")

# Force refresh if needed
codebase.refresh_errors()
```

## Migration from Legacy API

If you're migrating from legacy Serena methods:

```python
# Old way
from graph_sitter.extensions.serena import SerenaCore
serena = SerenaCore(codebase_path)
errors = await serena.get_diagnostics()

# New way - much simpler!
from graph_sitter import Codebase
codebase = Codebase(codebase_path)
errors = codebase.errors()  # Direct access, no async needed
```

The new API provides all the same functionality with a much cleaner, more intuitive interface.

