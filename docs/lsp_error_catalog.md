# LSP Error Type Catalog

This document provides a comprehensive catalog of ALL LSP error types that can be detected across different language servers. This catalog serves as the foundation for the enhanced error handling system.

## Overview

The enhanced error handling system must detect, contextualize, and provide reasoning for every possible LSP error type. This catalog ensures 100% coverage of error detection capabilities.

## Error Categories

### 1. Syntax Errors

These are fundamental parsing errors that prevent code from being syntactically valid.

#### 1.1 Missing Punctuation
- **E001**: Missing colon after if/for/while/def/class statements
- **E002**: Missing comma in function parameters, lists, dictionaries
- **E003**: Missing semicolon (JavaScript/TypeScript)
- **E004**: Missing closing parenthesis, bracket, or brace
- **E005**: Missing opening parenthesis, bracket, or brace

#### 1.2 Invalid Operators
- **E010**: Invalid operator usage (e.g., `===` in Python)
- **E011**: Misplaced operators (e.g., `x = + 5`)
- **E012**: Invalid assignment targets (e.g., `5 = x`)

#### 1.3 String/Character Issues
- **E020**: Unterminated string literals
- **E021**: Invalid escape sequences
- **E022**: Invalid character encoding
- **E023**: Mixed quote types causing issues

#### 1.4 Indentation Errors (Python-specific)
- **E030**: Inconsistent indentation
- **E031**: Unexpected indent
- **E032**: Unindent does not match any outer indentation level
- **E033**: Mixed tabs and spaces

### 2. Semantic Errors

These are errors related to the meaning and context of code elements.

#### 2.1 Undefined References
- **S001**: Undefined variable
- **S002**: Undefined function
- **S003**: Undefined class
- **S004**: Undefined module/package
- **S005**: Undefined attribute/property

#### 2.2 Scope Violations
- **S010**: Variable used before definition
- **S011**: Variable referenced outside its scope
- **S012**: Accessing private members from outside class
- **S013**: Using `this`/`self` outside method context

#### 2.3 Name Conflicts
- **S020**: Variable shadows built-in name
- **S021**: Function/class name conflicts with existing definition
- **S022**: Parameter name conflicts with local variable
- **S023**: Import name conflicts with existing name

### 3. Type Errors

These are errors related to type checking and type annotations.

#### 3.1 Type Mismatches
- **T001**: Incompatible assignment (e.g., `str` to `int`)
- **T002**: Wrong function argument types
- **T003**: Wrong return type
- **T004**: Incompatible operand types for operators

#### 3.2 Type Annotation Issues
- **T010**: Invalid type annotation syntax
- **T011**: Unknown type in annotation
- **T012**: Missing type annotation (when required)
- **T013**: Redundant type annotation

#### 3.3 Generic Type Issues
- **T020**: Wrong number of type parameters
- **T021**: Invalid generic type usage
- **T022**: Type parameter constraints violated

### 4. Import Errors

These are errors related to module imports and dependencies.

#### 4.1 Missing Modules
- **I001**: Module not found
- **I002**: Package not installed
- **I003**: Relative import beyond top-level package
- **I004**: Import from non-existent submodule

#### 4.2 Circular Dependencies
- **I010**: Circular import detected
- **I011**: Mutual dependency between modules
- **I012**: Self-referential import

#### 4.3 Import Syntax Issues
- **I020**: Invalid import syntax
- **I021**: Import statement in wrong location
- **I022**: Wildcard import issues
- **I023**: Alias conflicts

### 5. Linting Errors

These are code quality and style-related issues.

#### 5.1 Unused Code
- **L001**: Unused variable
- **L002**: Unused function
- **L003**: Unused import
- **L004**: Unused parameter
- **L005**: Unreachable code

#### 5.2 Code Style
- **L010**: Line too long
- **L011**: Too many blank lines
- **L012**: Missing blank line
- **L013**: Trailing whitespace
- **L014**: Inconsistent naming convention

#### 5.3 Code Complexity
- **L020**: Function too complex (cyclomatic complexity)
- **L021**: Too many parameters
- **L022**: Too many local variables
- **L023**: Nested too deeply

### 6. False Positives

These are known patterns that LSP servers incorrectly flag as errors.

#### 6.1 LSP Server Initialization
- **F001**: Temporary parsing errors during server startup
- **F002**: Incomplete indexing causing false undefined references
- **F003**: Cache invalidation causing temporary errors

#### 6.2 Dynamic Code Patterns
- **F010**: Dynamic attribute access (e.g., `getattr`, `setattr`)
- **F011**: Metaprogramming patterns
- **F012**: Runtime code generation
- **F013**: Monkey patching

#### 6.3 Language-Specific Quirks
- **F020**: Python `__getattr__` magic methods
- **F021**: JavaScript prototype manipulation
- **F022**: TypeScript declaration merging
- **F023**: Conditional imports

### 7. Edge Cases

These are complex scenarios that require special handling.

#### 7.1 Multi-file Dependencies
- **E100**: Cross-file type dependencies
- **E101**: Cascading errors from dependency changes
- **E102**: Version conflicts between dependencies

#### 7.2 Runtime vs Static Analysis
- **E110**: Errors only detectable at runtime
- **E111**: Dynamic type resolution issues
- **E112**: Conditional code paths

#### 7.3 Language Interop
- **E120**: Foreign function interface errors
- **E121**: Mixed language project issues
- **E122**: Build system integration errors

## Language Server Specific Patterns

### Python (pylsp, mypy, pyright)
- **pylsp**: General Python language server errors
- **mypy**: Type checking specific errors
- **pyright**: Microsoft's Python type checker errors

### JavaScript/TypeScript (typescript-language-server)
- **tsc**: TypeScript compiler errors
- **eslint**: JavaScript/TypeScript linting errors
- **prettier**: Code formatting issues

### Other Languages
- **rust-analyzer**: Rust-specific errors
- **clangd**: C/C++ errors
- **gopls**: Go language server errors

## Error Context Requirements

For each error type, the system must provide:

1. **Context**: Surrounding code (±10 lines), symbol definitions, usage patterns
2. **Reasoning**: Root cause analysis, why the error occurred
3. **Impact Analysis**: What else breaks, cascading effects
4. **Fix Suggestions**: Specific, actionable recommendations
5. **Confidence Score**: Reliability of the error detection
6. **False Positive Likelihood**: Probability this is a false alarm

## Validation Requirements

- **100% Error Type Coverage**: Every error type must be detectable
- **>95% Context Accuracy**: Context and reasoning must be correct
- **<5% False Positive Rate**: Minimal false alarms
- **>90% Fix Success Rate**: Auto-fixes must work reliably

## Implementation Notes

1. Each error type should have corresponding test fixtures
2. False positive detection must be language-server aware
3. Context extraction should be semantic, not just textual
4. Fix suggestions should be validated before presentation
5. Performance must remain sub-100ms for cached errors

This catalog will be continuously updated as new error patterns are discovered and language servers evolve.

