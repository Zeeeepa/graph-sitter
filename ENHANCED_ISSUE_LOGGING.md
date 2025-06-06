# 🔍 Enhanced Issue Logging System

## Overview

The enhanced issue logging system provides comprehensive, precise issue detection and reporting for Python codebases. It goes beyond basic static analysis to provide detailed context, parameter-specific analysis, and actionable suggestions.

## 🚀 Key Features

### **1. Comprehensive Issue Detection**
- **Security Issues**: Detects `eval()`, `exec()`, and other security vulnerabilities
- **Performance Issues**: Identifies string concatenation in loops, inefficient patterns
- **Maintainability Issues**: Long functions, deep nesting, complex code structures
- **Parameter Issues**: Type annotations, naming conventions, mutable defaults, parameter count
- **Documentation Issues**: Missing docstrings, inadequate documentation
- **File-level Issues**: File length, structure problems

### **2. Detailed Issue Context**
- **Precise Location**: Line numbers, column positions, code ranges
- **Code Context**: Surrounding code lines for better understanding
- **Function/Class Context**: Identifies containing functions and classes
- **Import Context**: Related imports and dependencies

### **3. Parameter-Specific Analysis**
- **Type Annotation Checking**: Identifies missing type hints
- **Naming Convention Validation**: Enforces snake_case conventions
- **Mutable Default Detection**: Finds dangerous mutable default arguments
- **Parameter Count Analysis**: Flags functions with too many parameters
- **Usage Pattern Analysis**: Tracks how parameters are used

### **4. Advanced Reporting**
- **Multiple Output Formats**: Console, JSON, HTML reports
- **Severity Filtering**: Filter by critical, major, minor, info levels
- **Interactive HTML Reports**: Tabbed interface with detailed views
- **Actionable Suggestions**: Specific recommendations for each issue
- **Auto-fix Indicators**: Shows which issues can be automatically resolved

## 📋 Usage Examples

### **Basic Enhanced Analysis**
```bash
# Run with detailed issue detection
python src/graph_sitter/adapters/analyze_codebase.py . --detailed-issues

# Include parameter-specific analysis
python src/graph_sitter/adapters/analyze_codebase.py . --detailed-issues --show-parameter-issues

# Filter by severity level
python src/graph_sitter/adapters/analyze_codebase.py . --detailed-issues --issue-severity-filter major
```

### **HTML Report Generation**
```bash
# Generate comprehensive HTML report
python src/graph_sitter/adapters/analyze_codebase.py . --issue-report-html issues_report.html

# Generate filtered HTML report
python src/graph_sitter/adapters/analyze_codebase.py . --issue-report-html critical_issues.html --issue-severity-filter critical
```

### **Programmatic Usage**
```python
from graph_sitter.adapters.analyze_codebase import ComprehensiveCodebaseAnalyzer

# Initialize analyzer with enhanced issue detection
analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=True)

# Analyze codebase
result = analyzer.analyze_codebase("/path/to/code")

# Access detailed issues
for issue in result.detailed_issues:
    print(f"Issue: {issue.message}")
    print(f"File: {issue.file_path}:{issue.line_start}")
    print(f"Severity: {issue.severity}")
    print(f"Category: {issue.category}")
    
    # Parameter-specific issues
    for param_issue in issue.parameter_issues:
        print(f"Parameter {param_issue.parameter_name}: {param_issue.description}")
    
    # Code context
    if issue.context:
        print(f"Function: {issue.context.function_name}")
        print(f"Class: {issue.context.class_name}")
```

## 🎯 Issue Categories

### **Security Issues (SEC)**
- **SEC001**: `eval()` function usage
- **SEC002**: `exec()` function usage
- **SEC003**: Unsafe input handling
- **SEC004**: Hardcoded credentials

### **Performance Issues (PERF)**
- **PERF001**: String concatenation in loops
- **PERF002**: Inefficient data structures
- **PERF003**: Unnecessary computations
- **PERF004**: Memory leaks

### **Maintainability Issues (MAINT)**
- **MAINT001**: Functions too long (>50 lines)
- **MAINT002**: Deep nesting (>4 levels)
- **MAINT003**: High cyclomatic complexity
- **MAINT004**: Code duplication

### **Parameter Issues (PARAM)**
- **PARAM_MISSING_TYPE**: Missing type annotations
- **PARAM_TOO_MANY**: Too many parameters (>7)
- **PARAM_MUTABLE_DEFAULT**: Mutable default arguments
- **PARAM_NAMING_CONVENTION**: Non-snake_case parameter names

### **Documentation Issues (DOC)**
- **DOC001**: Missing function docstrings
- **DOC002**: Missing class docstrings
- **DOC003**: Inadequate documentation

### **File Issues (FILE)**
- **FILE001**: File too long (>1000 lines)
- **FILE002**: Poor file organization
- **FILE003**: Missing file headers

## 📊 Report Formats

### **Console Output**
```
🔍 DETAILED ISSUE ANALYSIS REPORT
================================================================================

📋 CRITICAL ISSUES (2)
--------------------------------------------------

🔸 [analyze_codebase_123_security_eval_1] Use of eval() function detected
   📁 File: src/example.py:45
   🏷️  Type: security_vulnerability | Category: security
   📊 Confidence: 90.0% | Fix: medium
   💻 Code: eval(user_input)
   💡 Suggestion: Replace eval() with safer alternatives like ast.literal_eval()
   📍 Location: Class: DataProcessor → Function: process_input

📈 SUMMARY: 15 total issues found
   Critical: 2, Major: 5, Minor: 6, Info: 2
```

### **HTML Report**
Interactive HTML report with:
- **Summary Dashboard**: Issue counts by severity and category
- **Tabbed Interface**: View by severity, category, or file
- **Detailed Issue Cards**: Complete context and suggestions
- **Code Snippets**: Syntax-highlighted code examples
- **Parameter Analysis**: Dedicated parameter issue sections

### **JSON Output**
```json
{
  "detailed_issues": [
    {
      "id": "analyze_codebase_123_security_eval_1",
      "type": "security_vulnerability",
      "severity": "critical",
      "category": "security",
      "message": "Use of eval() function detected",
      "file_path": "src/example.py",
      "line_start": 45,
      "code_snippet": "eval(user_input)",
      "context": {
        "function_name": "process_input",
        "class_name": "DataProcessor",
        "surrounding_lines": ["43: def process_input(self, user_input):", "44:     try:", "45:         result = eval(user_input)", "46:         return result", "47:     except Exception:"]
      },
      "parameter_issues": [],
      "rule_id": "SEC001",
      "confidence": 0.9,
      "fix_complexity": "medium",
      "suggestion": "Replace eval() with safer alternatives like ast.literal_eval()",
      "auto_fixable": false,
      "impact_scope": "project"
    }
  ]
}
```

## 🔧 Configuration Options

### **Command Line Arguments**
- `--detailed-issues`: Enable comprehensive issue analysis
- `--issue-report-html <file>`: Generate HTML report
- `--show-parameter-issues`: Include parameter-specific analysis
- `--issue-severity-filter <level>`: Filter by minimum severity
- `--no-graph-sitter`: Use AST-only analysis (fallback mode)

### **Programmatic Configuration**
```python
# Configure issue detector
detector = EnhancedIssueDetector(use_graph_sitter=True)

# Analyze specific file
issues = detector.analyze_file_issues("path/to/file.py", source_code)

# Generate custom reports
html_report = generate_detailed_issue_report(issues)
```

## 🎨 Customization

### **Adding Custom Issue Types**
```python
class CustomIssueDetector(EnhancedIssueDetector):
    def detect_custom_issues(self, node: ast.AST, file_path: str) -> List[DetailedCodeIssue]:
        issues = []
        # Add custom detection logic
        return issues
```

### **Custom Report Templates**
```python
def custom_issue_formatter(issue: DetailedCodeIssue) -> str:
    return f"Custom format: {issue.message} in {issue.file_path}"
```

## 📈 Performance

- **Fast Analysis**: Optimized AST traversal and caching
- **Memory Efficient**: Streaming analysis for large codebases
- **Scalable**: Handles projects with thousands of files
- **Configurable**: Adjustable analysis depth and scope

## 🔄 Integration

### **CI/CD Integration**
```yaml
# GitHub Actions example
- name: Code Quality Analysis
  run: |
    python src/graph_sitter/adapters/analyze_codebase.py . \
      --detailed-issues \
      --issue-report-html quality-report.html \
      --issue-severity-filter major
```

### **Pre-commit Hooks**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: enhanced-analysis
        name: Enhanced Code Analysis
        entry: python src/graph_sitter/adapters/analyze_codebase.py
        args: [--detailed-issues, --issue-severity-filter, critical]
        language: system
```

## 🚀 Future Enhancements

- **Machine Learning Integration**: AI-powered issue detection
- **Custom Rule Engine**: User-defined issue detection rules
- **Real-time Analysis**: Live issue detection during development
- **Multi-language Support**: Extended language support beyond Python
- **Integration APIs**: REST API for external tool integration

## 📝 Examples

See `test_enhanced_issues.py` for a comprehensive example demonstrating all issue types and reporting capabilities.

## 🤝 Contributing

To add new issue detection capabilities:

1. Extend the `EnhancedIssueDetector` class
2. Add new issue types to the appropriate category
3. Update the HTML report template
4. Add tests for new detection logic
5. Update documentation

## 📄 License

This enhanced issue logging system is part of the graph-sitter project and follows the same licensing terms.

