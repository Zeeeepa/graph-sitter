# 🔍 Enhanced Codebase Analytics

A robust, comprehensive codebase analysis tool with advanced visualization, error detection, and one-click resolution capabilities.

## ✨ Features

### 🎯 Core Analytics
- **Comprehensive Metrics**: Lines of code, complexity analysis, function/class counts
- **Dependency Analysis**: Module dependencies with NetworkX-based visualization
- **Call Graph Analysis**: Function call relationships and execution flows
- **Complexity Assessment**: Cyclomatic complexity with distribution analysis

### 🔍 Advanced Error Detection
- **Import Resolution Errors**: Unresolved imports and circular dependencies
- **Symbol Resolution Issues**: Undefined variables and missing definitions
- **Dead Code Detection**: Unused functions and variables
- **Complexity Issues**: High complexity functions requiring refactoring
- **Configuration Errors**: Invalid parameters and settings

### 🎨 Interactive Visualizations
- **Dependency Graphs**: Module relationship mapping with hierarchical layout
- **Call Graphs**: Function call traces with complexity-based sizing
- **Complexity Heatmaps**: Visual complexity distribution across files
- **Error Blast Radius**: Impact analysis of detected errors
- **File Tree Browser**: Hierarchical file structure with metrics

### 🔧 One-Click Resolution
- **Auto-Fix Capabilities**: Automatic resolution of common issues
- **Smart Suggestions**: AI-powered fix recommendations
- **Batch Processing**: Resolve multiple errors simultaneously
- **Preview Changes**: See fixes before applying them

## 🚀 Quick Start

### Installation

```bash
# Clone or download the enhanced_codebase_analytics directory
cd enhanced_codebase_analytics

# Install dependencies
pip install -r requirements.txt

# Install graph-sitter (if not already installed)
pip install graph-sitter
```

### Demo Analysis

```bash
# Run interactive demo
python run_demo.py

# Analyze specific repository
python run_demo.py "fastapi/fastapi"

# Analyze local directory
python run_demo.py "/path/to/your/project"
```

### Web Dashboard

```bash
# Start the API server
python backend/api_server.py

# Open browser to http://localhost:5000
# Use the interactive dashboard for full visualization
```

## 📊 Usage Examples

### Command Line Analysis

```python
from enhanced_analytics import analyze_codebase_enhanced

# Analyze a GitHub repository
results = analyze_codebase_enhanced("fastapi/fastapi")

# Access results
print(f"Total errors: {results.metrics_summary['total_errors']}")
print(f"Average complexity: {results.metrics_summary['average_complexity']}")

# Get fixable errors
analyzer = EnhancedCodebaseAnalyzer(codebase)
fixable_errors = analyzer.get_fixable_errors()
```

### API Usage

```bash
# Analyze repository via API
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "fastapi/fastapi"}'

# Get detected errors
curl http://localhost:5000/api/errors

# Fix auto-fixable errors
curl -X POST http://localhost:5000/api/fix-errors

# Get metrics summary
curl http://localhost:5000/api/metrics
```

## 🎨 Visualization Dashboard

The web dashboard provides interactive visualizations:

### 📈 Metrics Overview
- Real-time metrics display
- Error count tracking
- Complexity distribution
- File and function statistics

### 🔗 Dependency Graph
- Interactive network visualization
- Module relationship mapping
- Import dependency tracking
- Circular dependency detection

### 📞 Call Graph
- Function call relationships
- Complexity-based node sizing
- Interactive exploration
- Call trace analysis

### 🌡️ Complexity Heatmap
- File-level complexity visualization
- Color-coded complexity levels
- Interactive bar charts
- Hotspot identification

### 💥 Error Blast Radius
- Error impact visualization
- Affected file mapping
- Severity-based coloring
- Interactive error exploration

### 🌳 File Tree Browser
- Hierarchical file structure
- Error count indicators
- Complexity scoring
- Interactive navigation

## 🔧 Error Resolution

### Supported Auto-Fixes

1. **Import Errors**
   - Missing import statements
   - Incorrect import paths
   - Circular import resolution

2. **Dead Code Removal**
   - Unused function elimination
   - Orphaned variable cleanup
   - Unreachable code detection

3. **Configuration Fixes**
   - Parameter validation
   - Path correction
   - Settings optimization

### Resolution Workflow

```python
# Get fixable errors
fixable_errors = analyzer.get_fixable_errors()

# Apply all auto-fixes
results = analyzer.apply_auto_fixes()

# Fix specific error type
analyzer._fix_import_error(error)
analyzer._fix_dead_code(error)
```

## 🏗️ Architecture

### Backend Components

```
backend/
├── enhanced_analytics.py    # Core analysis engine
├── api_server.py           # Flask API server
└── requirements.txt        # Dependencies
```

### Frontend Components

```
frontend/
└── visualization_dashboard.html  # Interactive web dashboard
```

### Key Classes

- **`EnhancedCodebaseAnalyzer`**: Main analysis engine
- **`ErrorInfo`**: Error representation with resolution data
- **`FileTreeNode`**: Hierarchical file structure
- **`VisualizationData`**: Complete visualization dataset

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze repository |
| `/api/errors` | GET | Get detected errors |
| `/api/fix-errors` | POST | Apply auto-fixes |
| `/api/fix-error/<type>/<symbol>` | POST | Fix specific error |
| `/api/metrics` | GET | Get metrics summary |
| `/api/file-tree` | GET | Get file tree structure |
| `/api/visualizations/<type>` | GET | Get visualization data |
| `/api/health` | GET | Health check |
| `/api/demo` | POST | Demo with mock data |

## 🎯 Configuration

### Analysis Options

```python
# Custom analysis configuration
analyzer = EnhancedCodebaseAnalyzer(codebase)

# Configure complexity thresholds
analyzer.complexity_threshold = 20

# Configure error detection
analyzer.detect_dead_code = True
analyzer.detect_import_errors = True
```

### Visualization Settings

```javascript
// Customize visualization colors
const COLOR_PALETTE = {
    "low_complexity": "#00ff00",
    "medium_complexity": "#ffff00", 
    "high_complexity": "#ff8800",
    "critical_complexity": "#ff0000"
};
```

## 🔬 Advanced Features

### Blast Radius Analysis
- Calculate impact scope of changes
- Identify affected files and symbols
- Risk assessment visualization
- Change propagation mapping

### Symbol Attribution
- Code authorship tracking
- AI vs human contribution analysis
- Change frequency mapping
- Ownership boundary identification

### Quality Metrics
- Technical debt assessment
- Maintainability scoring
- Code health indicators
- Trend analysis over time

## 🧪 Testing

```bash
# Run demo analysis
python run_demo.py

# Test API endpoints
python backend/api_server.py
# Then test with curl or browser

# Validate visualizations
# Open http://localhost:5000 in browser
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your enhancements
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run code formatting
black backend/
flake8 backend/

# Run tests
pytest tests/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built on top of [graph-sitter](https://github.com/codegen-sh/graph-sitter)
- Visualization powered by [vis.js](https://visjs.org/) and [Plotly](https://plotly.com/)
- Network analysis using [NetworkX](https://networkx.org/)

## 🔮 Future Enhancements

- [ ] Real-time analysis updates
- [ ] Git integration for change tracking
- [ ] Machine learning-based error prediction
- [ ] Custom rule engine for error detection
- [ ] Integration with popular IDEs
- [ ] Multi-language support expansion
- [ ] Performance optimization for large codebases
- [ ] Cloud deployment options

---

**🚀 Transform your codebase analysis with enhanced visualization and one-click error resolution!**

