# Enhanced Code Analysis Module

This module provides comprehensive code analysis capabilities following the patterns from [graph-sitter.com/tutorials/at-a-glance](https://graph-sitter.com/tutorials/at-a-glance) with enhanced issue detection and comprehensive reporting.

## Features

### 🔍 Comprehensive Analysis
- **File Analysis**: Analyzes all Python files in a codebase
- **Issue Detection**: Identifies code issues with severity levels
- **Dead Code Detection**: Finds unused functions and classes
- **Metrics Calculation**: Computes complexity and maintainability metrics

### 🏗️ Enhanced Capabilities
- **Top-Level Symbol Identification**: Finds top-level functions and classes
- **Inheritance Hierarchy Analysis**: Maps class inheritance relationships
- **Files with Issues Tracking**: Numbered list of problematic files
- **Comprehensive Reporting**: Enhanced output formatting

## Usage

### Basic Usage

```python
from graph_sitter import Codebase

# Analyze local repository
codebase = Codebase("path/to/git/repo")
result = codebase.Analysis()

# Analyze remote repository  
codebase = Codebase.from_repo("fastapi/fastapi")
result = codebase.Analysis()
```

### Direct Import Usage

```python
from graph_sitter.adapters.analysis import analyze_codebase, format_analysis_results

# Analyze a codebase
result = analyze_codebase("path/to/code")

# Format results for display
formatted_output = format_analysis_results(result)
print(formatted_output)

# Get JSON output
json_data = result.to_dict()
```

### Command Line Usage

```bash
# Analyze current directory
python -m graph_sitter.adapters.analysis.analysis .

# Analyze specific directory with JSON output
python -m graph_sitter.adapters.analysis.analysis /path/to/code --format json

# Save results to file
python -m graph_sitter.adapters.analysis.analysis /path/to/code --output results.txt
```

## Analysis Results

### Summary Metrics
- **Total Files**: Number of Python files analyzed
- **Total Functions**: Count of all functions found
- **Total Classes**: Count of all classes found
- **Maintainability Index**: Code maintainability score
- **Technical Debt Ratio**: Estimated technical debt
- **Test Coverage Estimate**: Estimated test coverage percentage

### Enhanced Features

#### 📁 Files with Issues (Numbered List)
```
Files with Issues (3):
  1. src/module/core.py
     Issues: 5
     Top-Level Functions: process_data, validate_input
     Top-Level Classes: DataProcessor, Validator
     Inheritance: 2 classes with inheritance

  2. src/module/utils.py
     Issues: 2
     Top-Level Functions: helper_function
     Top-Level Classes: UtilityClass
```

#### 🔝 Top-Level Symbols
```
Top-Level Functions (10):
  1. main_function
  2. process_data
  3. validate_input
  ...

Top-Level Classes (5):
  1. BaseProcessor
  2. DataValidator
  3. ConfigManager
  ...
```

#### 🏗️ Inheritance Hierarchy
```
Inheritance Hierarchy (8 classes):
  1. BaseClass
     File: src/base.py:15
     Depth: 0

  2.   ChildClass
     File: src/child.py:20
     Parents: BaseClass
     Depth: 1
```

#### 💀 Dead Code Detection
```
Dead Code Items: 5
  1. Function: unused_helper
     Location: src/utils.py:45-60
     Reason: Function is defined but never called
     Confidence: 80.0%
```

#### ⚠️ Issue Detection
```
Issues: 12
  Critical: 1
    • Security vulnerability detected
      Location: src/auth.py:25
      Suggestion: Use secure password hashing

  Major: 3
    • High cyclomatic complexity (15)
      Location: src/complex.py:100
      Suggestion: Consider breaking into smaller functions

  Minor: 8
    • Line too long (150 > 120 characters)
      Location: src/long_line.py:42
      Suggestion: Break line into multiple lines
```

## Data Classes

### Core Classes

#### `AnalysisResult`
Main result container with all analysis data:
- `total_files`, `total_functions`, `total_classes`
- `files_with_issues`: List of `FileIssueInfo` objects
- `inheritance_hierarchy`: List of `InheritanceInfo` objects
- `top_level_functions`, `top_level_classes`: Lists of symbol names
- `issues`, `dead_code_items`: Detected problems
- `function_metrics`, `class_metrics`: Complexity metrics

#### `FileIssueInfo`
Information about files containing issues:
- `file_path`: Path to the file
- `issue_count`: Number of issues found
- `top_level_functions`, `top_level_classes`: Symbols in this file
- `inheritance_info`: Class inheritance data for this file

#### `InheritanceInfo`
Class inheritance relationship data:
- `class_name`: Name of the class
- `file_path`, `line_start`: Location information
- `parent_classes`, `child_classes`: Inheritance relationships
- `inheritance_depth`: Depth in inheritance hierarchy
- `is_top_level`: Whether this is a base class

#### `CodeIssue`
Individual code issue:
- `type`, `severity`: Issue classification
- `message`: Description of the issue
- `file_path`, `line_start`, `line_end`: Location
- `suggestion`: Recommended fix
- `rule_id`: Identifier for the rule that detected this issue

## Output Formats

### Text Format
Human-readable formatted output with:
- Summary statistics
- Numbered lists of files with issues
- Top-level symbols with numbering
- Inheritance hierarchy with visual indentation
- Issue details grouped by severity

### JSON Format
Structured data output including:
- `summary`: Key metrics and counts
- `top_level_symbols`: Functions and classes
- `files_with_issues`: Detailed file information
- `inheritance_hierarchy`: Class relationship data
- `issues`, `dead_code_items`: Problem details
- `function_metrics`, `class_metrics`: Complexity data

## Examples

### Example Output

```
📊 Analysis Results:
  • Total Files: 25
  • Total Functions: 150
  • Total Classes: 45
  • Maintainability Index: 75.2/100
  • Technical Debt Ratio: 0.15

🔝 Top-Level Symbols:
  • Top-Level Functions (12):
    1. main
    2. process_data
    3. validate_input
    ...

📁 Files with Issues (3):
  1. src/core/processor.py
     Issues: 8
     Top-Level Functions: process, validate
     Top-Level Classes: DataProcessor
     Inheritance: 1 classes with inheritance

🏗️ Inheritance Hierarchy (15 classes):
  1. BaseProcessor
     File: src/base.py:20
     Depth: 0

  2.   DataProcessor
     File: src/core.py:15
     Parents: BaseProcessor
     Children: AdvancedProcessor
     Depth: 1
```

## Integration

The analysis module integrates with the main graph-sitter framework and can be used:

1. **As part of Codebase class**: `codebase.Analysis()`
2. **Direct function calls**: `analyze_codebase(path)`
3. **Command line tool**: `python -m graph_sitter.adapters.analysis.analysis`
4. **JSON API**: Export results as structured data

## Requirements

- Python 3.7+
- AST parsing capabilities (built-in)
- File system access for code analysis
- Optional: graph-sitter library for enhanced parsing

## Performance

- Optimized for large codebases
- Efficient AST parsing and analysis
- Memory-conscious processing
- Parallel analysis capabilities (future enhancement)

