# Enhanced Analytics API with Serena LSP Integration

This implementation upgrades the original FastAPI analytics application to include comprehensive codebase error detection using Serena's LSP server implementation and graph-sitter capabilities.

## 🚀 Features

### Core Error Detection
- **Multi-language Support**: Analyzes Python and JavaScript/TypeScript files
- **Comprehensive Error Categories**: Syntax, type, logic, style, security, performance, import, and undefined variable errors
- **Severity Levels**: ERROR, WARNING, INFORMATION, and HINT classifications
- **Context-Aware Analysis**: Provides line numbers, surrounding code context, and fix suggestions

### Error Types Detected

#### Python Files
- Undefined variables and references
- Import statement issues
- Syntax errors and inconsistencies
- Code style violations
- Security vulnerabilities (hardcoded secrets, SQL injection patterns)
- Performance issues (inefficient loops, redundant operations)

#### JavaScript/TypeScript Files
- Variable declaration issues (`var` vs `let`/`const`)
- Console.log statements (production warnings)
- Undefined variables and functions
- Syntax errors
- Type-related issues
- Performance anti-patterns

### Integration Components

The implementation integrates several key components from the Serena ecosystem:

```python
# Core graph-sitter integration
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, 
    get_class_summary, get_function_summary, get_symbol_summary
)

# LSP types and utilities
from solitlsp.ls_types import (
    DiagnosticSeverity, Diagnostic, Position, Range, 
    MarkupContent, Location, MarkupKind
)
from solitlsp.ls_utils import TextUtils, PathUtils, FileUtils
from solitlsp.ls_handler import SolidLanguageServerHandler

# Serena symbol and project management
from serena.symbol import LanguageServerSymbolRetriever, LanguageServerSymbol
from serena.project import Project
from serena.code_editor import CodeEditor
```

## 📊 Error Analysis Output

The system provides detailed error analysis in the following format:

```
Errors in Codebase [8]
----------------------------------------
1. main.py 'Potentially undefined variable: undefined_variable' 'ERROR' 'undefined' 'Line 7' 'def main(): |     # Undefined variable error'
2. app.js 'Use 'let' or 'const' instead of 'var'' 'WARNING' 'style' 'Line 1' 'var oldStyleVar = "should use let or const"; | '

📊 Error Analysis Summary:
   By Severity: {'ERROR': 2, 'WARNING': 2, 'INFORMATION': 4}
   By Category: {'undefined': 2, 'style': 6}
   By File: {'main.py': 2, 'app.js': 6}

💡 Fix Suggestions:
   app.js:1 - Replace 'var' with 'let' or 'const'
   app.js:7 - Replace 'var' with 'let' or 'const'
```

## 🏗️ Architecture

### SerenaErrorAnalyzer Class

The main analyzer class that orchestrates error detection:

```python
class SerenaErrorAnalyzer:
    """Enhanced error analyzer using LSP and graph-sitter capabilities."""
    
    async def analyze_codebase_errors(self, codebase_path: str) -> List[CodeError]
    def _perform_static_analysis(self, codebase: Codebase) -> List[CodeError]
    def _analyze_python_file(self, file) -> List[CodeError]
    def _analyze_js_file(self, file) -> List[CodeError]
```

### CodeError Data Structure

Each detected error is represented as:

```python
@dataclass
class CodeError:
    file_path: str
    line_number: int
    column: int
    severity: DiagnosticSeverity
    category: ErrorCategory
    message: str
    code: Optional[str]
    source: Optional[str]
    context_lines: Optional[List[str]]
    fix_suggestions: Optional[List[str]]
```

### Error Categories

```python
class ErrorCategory(Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    IMPORT = "import"
    UNDEFINED = "undefined"
```

## 🔧 Technical Implementation

### Multi-Language Codebase Handling

The system handles mixed-language codebases by separating files by language:

```python
# Separate files by language since Codebase.from_files requires single language
python_files = {}
js_files = {}

# Analyze each language separately
if python_files:
    python_codebase = Codebase.from_files(python_files)
    static_errors = self._perform_static_analysis(python_codebase)
    errors.extend(static_errors)

if js_files:
    js_codebase = Codebase.from_files(js_files)
    static_errors = self._perform_static_analysis(js_codebase)
    errors.extend(static_errors)
```

### Static Analysis Patterns

#### Python Analysis
- **Undefined Variables**: Regex patterns to detect potentially undefined variables
- **Import Issues**: Analysis of import statements and unused imports
- **Security Patterns**: Detection of hardcoded secrets, SQL injection vulnerabilities
- **Performance Issues**: Identification of inefficient code patterns

#### JavaScript Analysis
- **Variable Declarations**: Detection of `var` usage vs `let`/`const`
- **Console Statements**: Identification of debug statements for production cleanup
- **Syntax Issues**: Basic syntax error detection
- **Type Issues**: Basic type-related problem identification

## 🚀 Usage

### Basic Usage

```python
from enhanced_analytics_api import SerenaErrorAnalyzer

# Initialize analyzer
analyzer = SerenaErrorAnalyzer()

# Analyze a local directory
errors = await analyzer.analyze_codebase_errors("/path/to/codebase")

# Analyze a remote repository
errors = await analyzer.analyze_codebase_errors("https://github.com/user/repo")

# Process results
for error in errors:
    print(f"{error.file_path}:{error.line_number} - {error.message}")
```

### FastAPI Integration

The enhanced API includes a new endpoint for error analysis:

```python
@fastapi_app.post("/analyze_errors")
async def analyze_errors(request: RepoRequest) -> Dict[str, Any]:
    """Analyze repository for errors and return detailed diagnostics."""
    analyzer = SerenaErrorAnalyzer()
    errors = await analyzer.analyze_codebase_errors(request.repo_url)
    
    return {
        "total_errors": len(errors),
        "errors": [error.__dict__ for error in errors],
        "summary": generate_error_summary(errors)
    }
```

## 🧪 Testing

### Demo Script

Run the included demo to see the error detection in action:

```bash
python demo_with_errors.py
```

This creates a temporary repository with intentional errors and demonstrates the analysis capabilities.

### Test Suite

```bash
python test_enhanced_api.py
```

Comprehensive test suite covering:
- Error detection accuracy
- Multi-language support
- Edge cases and error handling
- Performance benchmarks

## 📈 Performance Considerations

- **Incremental Analysis**: Uses graph-sitter's incremental parsing capabilities
- **Language Separation**: Processes different languages in separate codebases for efficiency
- **Caching**: Leverages graph-sitter's built-in caching mechanisms
- **Memory Management**: Efficient handling of large codebases through streaming analysis

## 🔮 Future Enhancements

1. **Real-time LSP Integration**: Full LSP server integration for real-time error detection
2. **Custom Rule Engine**: User-defined error detection rules
3. **IDE Integration**: Direct integration with popular IDEs
4. **Machine Learning**: AI-powered error prediction and fix suggestions
5. **Team Analytics**: Team-wide code quality metrics and trends

## 🤝 Contributing

The implementation is designed to be extensible. To add new error detection patterns:

1. Extend the `ErrorCategory` enum
2. Add detection logic to `_analyze_python_file` or `_analyze_js_file`
3. Include appropriate fix suggestions
4. Add test cases

## 📝 License

This implementation builds upon the original analytics API and integrates with the Serena ecosystem. Please refer to the respective license terms for each component.

