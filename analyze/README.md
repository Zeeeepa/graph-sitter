# 🚀 Graph-Sitter Comprehensive Analysis Engine

This directory contains the consolidated analysis capabilities for graph-sitter, combining all 25 original analysis files into a streamlined, powerful analysis toolkit.

## 📁 Directory Structure

```
analyze/
├── full_analysis.py                    # 🎯 Main comprehensive analysis engine
├── web_dashboard/                      # 🌐 Interactive visualization dashboard
│   ├── backend/                        # 🔧 FastAPI backend with analysis integration
│   │   ├── comprehensive_analysis_integration.py  # 🚀 Full analysis integration
│   │   ├── main.py                     # 📡 Enhanced main backend with analysis routes
│   │   └── ...                         # Other backend components
│   └── frontend/                       # 🎨 React frontend for visualization
└── README.md                          # 📖 This documentation

```

## 🎯 Core Components

### 1. `full_analysis.py` - Comprehensive Analysis Engine

**Consolidates ALL capabilities from 25 original files:**

- ✅ **Serena LSP Error Detection** - Real-time error analysis with LSP integration
- ✅ **Deep Codebase Metrics** - Complexity analysis, maintainability scoring
- ✅ **Symbol Analysis** - Function/class relationship mapping
- ✅ **Dead Code Detection** - Automated cleanup recommendations
- ✅ **Code Quality Assessment** - Health scoring and quality metrics
- ✅ **Dashboard Integration** - Optimized data for visualization
- ✅ **Performance Monitoring** - Real-time analysis feedback
- ✅ **Import Management** - Deduplication and optimization tools

**Usage:**
```python
from full_analysis import ComprehensiveAnalysisEngine

# Initialize engine
engine = ComprehensiveAnalysisEngine("/path/to/codebase")

# Run comprehensive analysis
results = await engine.run_full_analysis()

# Get dashboard data
dashboard_data = engine.get_dashboard_data()
```

**Command Line:**
```bash
# Run analysis with output
python full_analysis.py --path /path/to/codebase --output results.json --dashboard

# Quick analysis
python full_analysis.py --path .
```

### 2. `web_dashboard/` - Interactive Visualization

**Enhanced dashboard with comprehensive analysis integration:**

- 🌐 **Real-time Analysis** - Live updates via WebSocket
- 📊 **Advanced Visualizations** - Error heatmaps, complexity charts
- 🎨 **Interactive UI** - React-based dashboard with rich components
- 📡 **API Integration** - RESTful endpoints for analysis data
- 🔄 **Background Processing** - Async analysis execution

**Backend Features:**
- `/api/analysis/run` - Start comprehensive analysis
- `/api/analysis/dashboard-data` - Get visualization data
- `/api/analysis/visualization/error-heatmap` - Error visualization
- `/api/analysis/visualization/complexity` - Complexity analysis
- `/api/analysis/ws` - WebSocket for real-time updates

## 🚀 Quick Start

### 1. Run Comprehensive Analysis

```bash
cd analyze
python full_analysis.py --path /path/to/your/codebase --output analysis_results.json --dashboard
```

### 2. Start Web Dashboard

```bash
cd analyze/web_dashboard/backend
python main.py
```

Then open `http://localhost:8000` for the API or start the frontend for the full dashboard.

### 3. API Usage

```python
import requests

# Start analysis
response = requests.post("http://localhost:8000/api/analysis/run", json={
    "codebase_path": "/path/to/codebase",
    "include_lsp_diagnostics": True,
    "include_dead_code": True
})

analysis_id = response.json()["analysis_id"]

# Get results
results = requests.get(f"http://localhost:8000/api/analysis/results/{analysis_id}")
```

## 📊 Analysis Capabilities

### Error Detection & Analysis
- **LSP Integration** - Real-time error detection from language servers
- **Comprehensive Diagnostics** - Error, warning, and info level analysis
- **Error Heatmaps** - Visual representation of error distribution
- **Severity Analysis** - Categorized error reporting

### Code Quality Metrics
- **Complexity Analysis** - Function and class complexity scoring
- **Maintainability Index** - Overall codebase health assessment
- **File Size Analysis** - Large file detection and recommendations
- **Import Analysis** - Dependency health and optimization

### Dead Code Detection
- **Unused Functions** - Detection of potentially unused code
- **Unused Imports** - Import optimization recommendations
- **Cleanup Suggestions** - Automated refactoring recommendations

### Visualization & Reporting
- **Interactive Charts** - Pie charts, bar graphs, histograms
- **File Tree Heatmaps** - Error distribution visualization
- **Complexity Visualization** - Function and file complexity mapping
- **Real-time Updates** - Live analysis progress and results

## 🔧 Configuration

The analysis engine supports various configuration options:

```python
engine = ComprehensiveAnalysisEngine(
    codebase_path="/path/to/codebase"
)

# Customize analysis
results = await engine.run_full_analysis()
```

## 📈 Performance

**Optimized for large codebases:**
- Async processing for non-blocking analysis
- Incremental analysis capabilities
- Memory-efficient processing
- Background task execution

## 🎨 Dashboard Features

**Enhanced visualization capabilities:**
- Error severity distribution charts
- File type analysis
- Complexity distribution visualization
- Interactive file tree with error highlighting
- Real-time analysis progress
- Comprehensive reporting tables

## 🔗 Integration

**Easy integration with existing tools:**
- FastAPI backend for REST API access
- WebSocket support for real-time updates
- JSON output for external tool integration
- Command-line interface for automation
- Python API for programmatic access

## 📝 Migration from Original Files

This consolidated version replaces 25 original analysis files:

**High-Value Consolidated:**
- `serena_analyzer.py` → Integrated into `ComprehensiveAnalysisEngine`
- `enhanced_serena_codebase_analyzer.py` → Core analysis methods
- `deep_comprehensive_analysis.py` → Metrics and visualization
- `dashboard_api_tester.py` → Web dashboard integration
- `lsp_serena_integration_demo.py` → LSP error detection

**All capabilities preserved and enhanced with:**
- Better error handling
- Improved performance
- Unified API
- Enhanced visualization
- Real-time updates

## 🚀 Future Enhancements

- **AI-Powered Suggestions** - Intelligent code improvement recommendations
- **Custom Analysis Rules** - User-defined analysis patterns
- **Integration Plugins** - IDE and editor extensions
- **Collaborative Features** - Team analysis and sharing
- **Advanced Metrics** - Machine learning-based code quality assessment

---

**🎉 The graph-sitter analysis directory now provides a complete, production-ready codebase analysis ecosystem with capabilities far beyond typical extensions!**
