# Enhanced Repository Analytics API with Serena LSP Integration

This enhanced Modal API provides comprehensive repository analysis with advanced error detection capabilities using Serena's LSP (Language Server Protocol) integration.

## 🚀 Features

### Core Capabilities
- **Basic Repository Metrics**: File counts, function counts, class counts
- **Comprehensive Error Analysis**: Multi-category error detection with context
- **Serena LSP Integration**: Advanced language server protocol capabilities
- **Security Scanning**: Detection of hardcoded secrets and vulnerabilities
- **Performance Analysis**: Identification of performance anti-patterns
- **Style Checking**: Code style and best practice validation

### Error Categories Detected
- **Syntax Errors**: Parse errors and syntax issues
- **Type Errors**: Type-related problems
- **Logic Errors**: Undefined variables and logic issues
- **Style Issues**: Code style violations (var usage, console.log statements)
- **Security Issues**: Hardcoded passwords, API keys, secrets
- **Performance Issues**: Inefficient loops and patterns
- **Import Issues**: Unused imports and import problems
- **Complexity Issues**: High complexity functions and code

## 📡 API Endpoints

### 1. Basic Repository Analysis
```
GET /analyze_repo?repo_name=owner/repo
```

**Response Format:**
```json
{
  "num_files": 150,
  "num_functions": 45,
  "num_classes": 12,
  "status": "success",
  "error": ""
}
```

### 2. Comprehensive Error Analysis
```
GET /analyze_repo_errors?repo_name=owner/repo
```

**Response Format:**
```json
{
  "total_errors": 23,
  "errors_by_severity": {
    "ERROR": 8,
    "WARNING": 10,
    "INFORMATION": 3,
    "HINT": 2
  },
  "errors_by_category": {
    "undefined": 3,
    "security": 5,
    "style": 8,
    "performance": 4,
    "import": 3
  },
  "errors_by_file": {
    "src/main.py": 12,
    "src/utils.py": 8,
    "src/config.py": 3
  },
  "errors": [
    {
      "file_path": "src/main.py",
      "line_number": 45,
      "column": 12,
      "severity": "ERROR",
      "category": "security",
      "message": "Hardcoded API key detected",
      "code": "hardcoded-secret",
      "source": "serena-security-analysis",
      "context_lines": [
        "    def authenticate():",
        "        # Security issue",
        ">>>     api_key = \"sk-1234567890abcdef\"",
        "        return api_key"
      ],
      "fix_suggestions": [
        "Move secrets to environment variables",
        "Use a secure configuration management system",
        "Never commit secrets to version control"
      ]
    }
  ],
  "analysis_summary": {
    "total_files_analyzed": 25,
    "files_with_errors": 8,
    "most_problematic_files": [
      ["src/main.py", 12],
      ["src/utils.py", 8],
      ["src/config.py", 3]
    ],
    "error_density": 0.92,
    "critical_issues": 8,
    "serena_integration_status": "available"
  },
  "serena_status": {
    "serena_available": true,
    "lsp_integration_active": true,
    "analysis_capabilities": [
      "static_analysis",
      "undefined_variable_detection",
      "import_analysis",
      "style_checking",
      "security_scanning",
      "performance_analysis"
    ]
  },
  "fix_suggestions": [
    "Move secrets to environment variables",
    "Define variables before use",
    "Remove unused imports",
    "Replace 'var' with 'let' or 'const'",
    "Use enumerate() for index and value"
  ],
  "status": "success",
  "error": ""
}
```

## 🛠️ Deployment

### Local Development
```bash
# Install dependencies
pip install modal fastapi pydantic

# Test the API locally
python test_enhanced_modal_api.py
```

### Modal Deployment
```bash
# Serve locally for testing
modal serve api.py

# Deploy to Modal
modal deploy api.py
```

## 🧪 Testing

The enhanced API includes comprehensive testing:

```bash
# Run the test suite
python test_enhanced_modal_api.py
```

**Test Coverage:**
- ✅ Enhanced API component loading
- ✅ Error analysis functionality
- ✅ Multiple error categories detection
- ✅ Context extraction and fix suggestions
- ✅ API response format validation
- ✅ Serena LSP integration status

## 🔍 Error Detection Examples

### Security Issues
```python
# Detected: Hardcoded secrets
password = "secret123"
api_key = "sk-1234567890abcdef"
```

### Performance Issues
```python
# Detected: Inefficient loops
for i in range(len(items)):
    print(items[i])

# Suggested: Use enumerate()
for i, item in enumerate(items):
    print(item)
```

### Style Issues
```javascript
// Detected: Old-style variable declarations
var oldStyleVar = "should use let or const";
console.log("Debug statement");

// Suggested: Modern syntax
const modernVar = "better approach";
// Remove console.log for production
```

### Undefined Variables
```python
# Detected: Undefined variable usage
def process_data():
    return undefined_variable + 1  # ERROR: undefined_variable not defined
```

## 🏗️ Architecture

### Core Components

1. **SerenaErrorAnalyzer**: Main analysis engine
   - File-by-file error detection
   - Pattern-based static analysis
   - Context extraction and suggestions

2. **Error Categories**: Comprehensive classification
   - Syntax, Type, Logic, Style
   - Security, Performance, Import
   - Undefined, Unused, Complexity

3. **LSP Integration**: Advanced language server features
   - Real-time error detection
   - Symbol analysis and context
   - Fix suggestions and refactoring

### Error Detection Pipeline

```
Repository → Codebase → Files → Analysis → Categorization → Response
     ↓           ↓        ↓         ↓            ↓            ↓
   Clone    Initialize  Parse   Patterns    Severity    JSON API
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Configure analysis depth
SERENA_MAX_ERRORS=1000
SERENA_CONTEXT_LINES=5
SERENA_ENABLE_SECURITY_SCAN=true
```

### Analysis Options
- **Context Size**: Number of lines around errors (default: 2)
- **Max Errors**: Maximum errors to return (default: unlimited)
- **Severity Filter**: Filter by error severity levels
- **Category Filter**: Focus on specific error categories

## 📊 Performance

### Benchmarks
- **Small Repository** (< 50 files): ~2-5 seconds
- **Medium Repository** (50-200 files): ~5-15 seconds  
- **Large Repository** (200+ files): ~15-30 seconds

### Optimization Features
- Parallel file processing
- Efficient pattern matching
- Smart caching mechanisms
- Incremental analysis support

## 🤝 Integration Examples

### Python Client
```python
import requests

# Basic analysis
response = requests.get(
    "https://your-modal-app.modal.run/analyze_repo",
    params={"repo_name": "owner/repo"}
)
metrics = response.json()

# Comprehensive error analysis
response = requests.get(
    "https://your-modal-app.modal.run/analyze_repo_errors", 
    params={"repo_name": "owner/repo"}
)
errors = response.json()

print(f"Found {errors['total_errors']} errors")
for error in errors['errors'][:5]:
    print(f"  {error['file_path']}:{error['line_number']} - {error['message']}")
```

### JavaScript/Node.js Client
```javascript
const axios = require('axios');

async function analyzeRepository(repoName) {
  try {
    const response = await axios.get(
      'https://your-modal-app.modal.run/analyze_repo_errors',
      { params: { repo_name: repoName } }
    );
    
    const analysis = response.data;
    console.log(`Analysis complete: ${analysis.total_errors} errors found`);
    
    // Process errors by severity
    Object.entries(analysis.errors_by_severity).forEach(([severity, count]) => {
      console.log(`${severity}: ${count} issues`);
    });
    
    return analysis;
  } catch (error) {
    console.error('Analysis failed:', error.message);
  }
}

analyzeRepository('owner/repo');
```

## 🔮 Future Enhancements

### Planned Features
- **Real-time Analysis**: WebSocket-based live error detection
- **Custom Rules**: User-defined error patterns and rules
- **Multi-language Support**: JavaScript, TypeScript, Go, Rust support
- **IDE Integration**: VS Code extension and LSP server
- **Batch Analysis**: Multiple repository analysis
- **Historical Tracking**: Error trend analysis over time

### Advanced Capabilities
- **AI-Powered Suggestions**: Machine learning-based fix recommendations
- **Automated Fixes**: One-click error resolution
- **Team Analytics**: Team-wide code quality metrics
- **Integration Hooks**: CI/CD pipeline integration
- **Custom Dashboards**: Visual analytics and reporting

## 📝 License

This enhanced API builds upon the graph-sitter project and integrates with Serena's LSP capabilities. Please refer to the respective license terms for each component.

## 🆘 Support

For issues, questions, or contributions:
- **Documentation**: See the main graph-sitter documentation
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Join the community discussions
- **Examples**: Check the examples directory for more use cases

---

**Ready to analyze your codebase with advanced error detection? Deploy this enhanced API and get comprehensive insights into your code quality!** 🚀

