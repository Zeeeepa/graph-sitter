# 🔍 Codebase Analysis Dashboard

A comprehensive, interactive dashboard for analyzing codebases using **Reflex** and **graph-sitter**. This dashboard provides powerful visualization of codebase structure, issue detection, dead code analysis, and important function identification.

## ✨ Features

### 🎯 Core Capabilities
- **Interactive Tree Visualization**: Navigate your codebase structure with visual indicators
- **Comprehensive Issue Detection**: Find untyped parameters, unused functions, missing annotations
- **Dead Code Analysis**: Identify unused functions, classes, and imports
- **Entry Point Detection**: Discover main functions and critical code paths
- **Real-time Analysis**: Live progress updates during codebase analysis

### 🔍 Analysis Types
- **Type Annotation Issues**: Missing parameter and return type annotations
- **Unused Code Detection**: Functions, classes, and imports that are never used
- **Complexity Analysis**: Functions with high cyclomatic complexity
- **Function Call Analysis**: Most called functions and call patterns
- **Recursive Function Detection**: Identify recursive implementations

### 🎨 Visual Indicators
- **⚠️ Critical Issues**: High-priority problems requiring immediate attention
- **👉 Major Issues**: Important issues that should be addressed
- **🔍 Minor Issues**: Style and best practice improvements
- **🚀 Entry Points**: Main functions and application entry points
- **⭐ Important Functions**: Frequently called or complex functions
- **💀 Dead Code**: Unused code that can be removed

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (recommended: Python 3.13+)
- Node.js 16+ (for Reflex frontend)
- Git

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Zeeeepa/graph-sitter.git
cd graph-sitter
```

2. **Install graph-sitter**:
```bash
pip install -e .
```

3. **Install dashboard dependencies**:
```bash
cd codebase_dashboard
pip install -r requirements.txt
```

4. **Install Reflex** (if not already installed):
```bash
pip install reflex
```

### Running the Dashboard

1. **Start the backend API server**:
```bash
cd analyze/web_dashboard/backend
python dashboard_server.py
```
The API will be available at `http://localhost:8000`

2. **Start the Reflex frontend** (in a new terminal):
```bash
cd codebase_dashboard
reflex run
```
The dashboard will be available at `http://localhost:3000`

## 📖 Usage Guide

### Analyzing a Repository

1. **Enter Repository URL**: Input a GitHub repository URL or local path
   - GitHub: `https://github.com/owner/repository`
   - Local: `/path/to/local/repository`

2. **Click "Analyze"**: Start the comprehensive analysis process

3. **Monitor Progress**: Watch real-time progress updates during analysis

4. **Explore Results**: Navigate through the interactive tree and analysis panels

### Understanding the Interface

#### 🌳 Tree View
- **File Structure**: Hierarchical view of your codebase
- **Issue Indicators**: Color-coded badges showing issue counts
- **Status Markers**: 
  - `EP` = Entry Point (yellow)
  - `IMP` = Important Function (orange)  
  - `DEAD` = Dead Code (red)

#### 📊 Statistics Panel
- **Files**: Total source files analyzed
- **Functions**: Total functions discovered
- **Classes**: Total classes found
- **Lines of Code**: Total lines analyzed
- **Issues**: Total issues detected
- **Dead Code**: Total unused code elements

#### 🐛 Issues Panel
- **Filter by Severity**: View critical, major, or minor issues
- **Detailed Context**: Click issues for full context and suggestions
- **File Location**: Jump to specific files and line numbers

#### 💀 Dead Code Panel
- **Functions**: Unused functions that can be removed
- **Classes**: Unused classes that can be removed
- **Imports**: Unused imports that can be cleaned up

#### ⭐ Important Functions Panel
- **Entry Points**: Main functions and application entry points
- **Most Called**: Frequently called functions
- **Complex**: Functions with high complexity
- **Recursive**: Functions that call themselves

## 🏗️ Architecture

### Frontend (Reflex)
- **Framework**: Reflex (Python-based web framework)
- **Components**: Modular, reusable UI components
- **State Management**: Centralized application state
- **Real-time Updates**: WebSocket integration for live progress

### Backend (FastAPI)
- **API Server**: FastAPI with comprehensive REST endpoints
- **Analysis Engine**: graph-sitter integration for code analysis
- **Background Processing**: Async analysis with progress tracking
- **Data Models**: Structured data for tree visualization and issues

### Analysis Engine (graph-sitter)
- **Code Parsing**: Tree-sitter for syntax tree generation
- **Symbol Resolution**: Comprehensive symbol and dependency tracking
- **Issue Detection**: Multiple analysis patterns for code quality
- **Dead Code Detection**: Usage analysis for unused code identification

## 🔧 API Endpoints

### Analysis Management
- `POST /api/analyze` - Start new analysis
- `GET /api/analysis/{id}/status` - Get analysis status
- `GET /api/analysis/{id}/tree` - Get tree structure
- `GET /api/analysis/{id}/issues` - Get detected issues
- `GET /api/analysis/{id}/dead_code` - Get dead code analysis
- `GET /api/analysis/{id}/important_functions` - Get important functions
- `GET /api/analysis/{id}/stats` - Get codebase statistics

### Health & Info
- `GET /api/health` - Health check
- `GET /` - API information

## 🎯 Example Analysis Output

### Tree Structure
```
📁 my-project/
├── 📄 main.py [🚀 EP] [⚠️ 2] [👉 1]
├── 📁 src/
│   ├── 📄 utils.py [⭐ IMP] [🔍 3]
│   └── 📄 models.py [💀 DEAD] [👉 2]
└── 📁 tests/
    └── 📄 test_main.py [🔍 1]
```

### Issue Detection
- **Critical**: Unused function `process_data` in `models.py:45`
- **Major**: Function `calculate` lacks return type annotation
- **Minor**: Parameter `data` lacks type annotation in `utils.py:12`

### Dead Code Analysis
- **Functions**: 3 unused functions found
- **Classes**: 1 unused class found  
- **Imports**: 5 unused imports found

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the existing code style
4. **Add tests**: Ensure your changes are tested
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes

### Development Setup

1. **Install development dependencies**:
```bash
pip install -e ".[dev]"
```

2. **Run tests**:
```bash
pytest tests/
```

3. **Run linting**:
```bash
ruff check .
mypy .
```

## 📝 Configuration

### Backend Configuration
Edit `analyze/web_dashboard/backend/dashboard_server.py`:
- **Port**: Change the API server port
- **CORS**: Configure allowed origins
- **Timeout**: Adjust analysis timeout settings

### Frontend Configuration  
Edit `codebase_dashboard/rxconfig.py`:
- **Ports**: Configure frontend and backend ports
- **API URL**: Set the backend API URL
- **Environment**: Set development/production mode

## 🐛 Troubleshooting

### Common Issues

**Analysis fails to start**:
- Ensure graph-sitter is properly installed: `pip install -e .`
- Check repository URL is accessible
- Verify backend server is running on port 8000

**Frontend won't load**:
- Ensure Reflex is installed: `pip install reflex`
- Check if port 3000 is available
- Verify backend API is accessible

**Empty analysis results**:
- Check if repository contains supported file types (Python, TypeScript, etc.)
- Ensure repository is not empty
- Check backend logs for analysis errors

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/graph-sitter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/graph-sitter/discussions)
- **Documentation**: [graph-sitter.com](https://graph-sitter.com)

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Tree-sitter](https://tree-sitter.github.io/)**: Incremental parsing library
- **[Reflex](https://reflex.dev/)**: Python web framework
- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern Python web framework
- **[graph-sitter](https://graph-sitter.com)**: Codebase analysis platform

---

**Built with ❤️ using Reflex and graph-sitter**

For more information, visit [graph-sitter.com](https://graph-sitter.com)
