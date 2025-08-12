# 🔍 Codebase Analysis Dashboard

A comprehensive, interactive dashboard for analyzing codebases using **Reflex** and **graph-sitter**. This dashboard provides real-time codebase analysis with tree visualization, issue detection, dead code analysis, and important function identification.

## ✨ Features

### 🌳 **Interactive Tree Visualization**
- Navigate your codebase structure with visual indicators
- Color-coded nodes showing issues and importance levels
- Expandable/collapsible tree structure
- Real-time issue count display on folders and files

### 🐛 **Comprehensive Issue Detection**
- **Type Annotation Issues**: Missing type hints and annotations
- **Dead Code Detection**: Unused functions, classes, and imports
- **Empty Functions**: Functions with no implementation
- **Parameter Mismatches**: Function signature inconsistencies
- **Circular Dependencies**: Import cycle detection

### 💀 **Dead Code Analysis**
- Unused functions that are never called
- Unused classes with no instances
- Unused imports that can be safely removed
- Detailed context and removal suggestions

### ⭐ **Important Function Identification**
- **Entry Points**: Main functions and CLI entry points
- **Most Called Functions**: Frequently used functions
- **Recursive Functions**: Functions that call themselves
- **Important Functions**: High-impact functions based on usage patterns

### 📊 **Comprehensive Statistics**
- Total files, functions, classes, and lines of code
- Issue breakdown by severity (Critical, Major, Minor)
- Dead code statistics
- Test coverage metrics
- Complexity scores

## 🏗️ Architecture

### **Frontend (Reflex)**
- **Pure Python**: No JavaScript/HTML/CSS required
- **Reactive Components**: Automatic UI updates on state changes
- **Real-time Updates**: Live progress tracking during analysis
- **Professional UI**: Modern, responsive design with Tailwind CSS

### **Backend (FastAPI)**
- **RESTful API**: Clean, documented endpoints
- **Async Processing**: Background analysis with progress tracking
- **WebSocket Support**: Real-time communication
- **graph-sitter Integration**: Advanced code parsing and analysis

### **Analysis Engine (graph-sitter)**
- **Multi-language Support**: Python, JavaScript, TypeScript, Go, Rust, etc.
- **Incremental Parsing**: Efficient syntax tree updates
- **Robust Error Handling**: Works even with syntax errors
- **Symbol Resolution**: Function, class, and variable identification

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for Reflex frontend compilation)

### 1. Install Dependencies
```bash
cd dashboard
pip install -r requirements.txt
```

### 2. Start the Backend API Server
```bash
python backend_server.py
```
The API will be available at `http://localhost:8000`

### 3. Start the Reflex Dashboard
```bash
reflex init
reflex run
```
The dashboard will be available at `http://localhost:3000`

### 4. Analyze Your Codebase
1. Open `http://localhost:3000` in your browser
2. Enter a repository URL or local path:
   - GitHub: `https://github.com/owner/repository`
   - Local: `./path/to/your/project`
3. Click "Analyze" and watch the real-time progress
4. Explore the results in the interactive tree view

## 📁 Project Structure

```
dashboard/
├── 📄 dashboard.py              # Main Reflex application
├── 📄 rxconfig.py              # Reflex configuration
├── 📄 backend_server.py        # FastAPI backend server
├── 📄 requirements.txt         # Python dependencies
├── 📄 README.md               # This file
└── src/                       # Source code
    ├── state/                 # Application state management
    │   └── app_state.py      # Central state management
    ├── pages/                 # Page components
    │   └── dashboard_page.py # Main dashboard page
    ├── components/            # Reusable UI components
    │   ├── common/           # Common components
    │   │   ├── loading_spinner.py
    │   │   ├── error_modal.py
    │   │   └── progress_bar.py
    │   ├── analysis/         # Analysis-specific components
    │   │   ├── repository_input.py
    │   │   └── analysis_progress.py
    │   └── layout/           # Layout components
    │       ├── header.py
    │       └── footer.py
    ├── services/             # External service integrations
    │   └── api_client.py    # Backend API client
    ├── utils/                # Utility functions
    │   ├── exceptions.py    # Custom exceptions
    │   ├── validators.py    # Input validation
    │   └── formatters.py    # Data formatting
    └── styles/               # Styling and themes
        └── theme.py         # Global theme configuration
```

## 🎯 Usage Examples

### Analyzing a GitHub Repository
```python
# Enter in the dashboard:
https://github.com/Zeeeepa/graph-sitter
```

### Analyzing a Local Project
```python
# Enter in the dashboard:
./my-local-project
```

### API Usage (Direct)
```python
import httpx

# Start analysis
response = httpx.post("http://localhost:8000/api/analyze", 
                     json={"repo_url": "https://github.com/owner/repo"})
analysis_id = response.json()["analysis_id"]

# Check status
status = httpx.get(f"http://localhost:8000/api/analysis/{analysis_id}/status")
print(status.json())

# Get results (when completed)
tree = httpx.get(f"http://localhost:8000/api/analysis/{analysis_id}/tree")
issues = httpx.get(f"http://localhost:8000/api/analysis/{analysis_id}/issues")
```

## 🔧 Configuration

### Backend Configuration
Edit `backend_server.py` to customize:
- **Port**: Change the port from 8000
- **CORS**: Modify allowed origins
- **Analysis Settings**: Adjust analysis parameters

### Frontend Configuration
Edit `rxconfig.py` to customize:
- **Styling**: Modify Tailwind theme
- **API URL**: Change backend endpoint
- **Ports**: Adjust frontend/backend ports

### Theme Customization
Edit `src/styles/theme.py` to customize:
- **Colors**: Primary, success, warning, error colors
- **Typography**: Font families and sizes
- **Spacing**: Consistent spacing scale
- **Components**: Button, card, input styles

## 🛠️ Development

### Adding New Analysis Features
1. **Backend**: Add new endpoints in `backend_server.py`
2. **API Client**: Add methods in `src/services/api_client.py`
3. **State**: Update `src/state/app_state.py`
4. **Components**: Create new components in `src/components/`

### Adding New UI Components
1. Create component in appropriate `src/components/` subdirectory
2. Follow the existing pattern with proper typing
3. Use the theme system from `src/styles/theme.py`
4. Add to the main page or layout as needed

### Testing
```bash
# Test backend API
python -m pytest tests/

# Test frontend components
reflex test
```

## 🤝 Integration with graph-sitter

This dashboard is designed to work seamlessly with the **graph-sitter** codebase analysis engine. The backend automatically detects if graph-sitter is available and falls back to mock data for demonstration purposes.

### Full Integration
To enable full analysis capabilities:
1. Install graph-sitter: `pip install graph-sitter`
2. Ensure the graph-sitter source is available
3. The backend will automatically use real analysis

### Mock Mode
When graph-sitter is not available, the dashboard runs in mock mode with sample data to demonstrate all features.

## 📊 Analysis Output Format

The dashboard provides structured output that can be used by other tools:

### Tree Structure
```json
{
  "name": "project-root",
  "type": "folder",
  "path": "/",
  "issues": [...],
  "children": [...]
}
```

### Issues Format
```json
{
  "id": "issue-1",
  "type": "missing_type_annotation",
  "severity": "major",
  "message": "Function missing type annotations",
  "file_path": "/src/module.py",
  "line_number": 45,
  "context": "def function(data):",
  "suggestion": "Add type hints: def function(data: Dict[str, Any]):"
}
```

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Mode**: Automatic theme detection
- **Keyboard Navigation**: Full keyboard accessibility
- **Real-time Updates**: Live progress and status updates
- **Professional Styling**: Modern, clean interface
- **Interactive Elements**: Hover effects, animations, transitions

## 🚀 Deployment

### Development
```bash
# Start both servers
python backend_server.py &
reflex run
```

### Production
```bash
# Build frontend
reflex export

# Deploy backend
gunicorn backend_server:app -w 4 -k uvicorn.workers.UvicornWorker

# Serve frontend
nginx -c nginx.conf
```

## 📝 License

This project is part of the graph-sitter ecosystem and follows the same licensing terms.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- **Documentation**: Check the inline code documentation
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Join the graph-sitter community discussions

---

**Built with ❤️ using Reflex, FastAPI, and graph-sitter**

