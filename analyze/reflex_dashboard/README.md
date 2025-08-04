# 🚀 Graph-Sitter Reflex Dashboard

A comprehensive interactive dashboard for codebase analysis built with Reflex and graph-sitter.

## ✨ Features

### 🎯 **Current Implementation (Steps 1-3)**
- ✅ **Interactive Dashboard Layout**: Clean, responsive UI with sidebar navigation
- ✅ **Codebase Selection**: Browse and select different codebases for analysis
- ✅ **File Tree Navigation**: Interactive file explorer with search and filtering
- ✅ **Analysis Engine Integration**: Real-time comprehensive codebase analysis
- ✅ **Progress Tracking**: Live progress indicators for long-running operations
- ✅ **Error Handling**: Comprehensive error handling and user feedback

### 🔮 **Planned Features (Steps 4-10)**
- 📊 **Analysis Results Dashboard**: Detailed metrics, charts, and health indicators
- 🔍 **LSP Diagnostics Display**: Complete error/warning panels with navigation
- 🌳 **Symbol Tree Visualization**: Interactive symbol hierarchy and relationships
- 💀 **Dead Code Analysis**: Unused function/parameter detection
- ⚡ **Real-time Updates**: WebSocket-based live analysis updates
- ⚙️ **Settings Management**: Configurable analysis parameters
- 📤 **Export Capabilities**: JSON, CSV, HTML export of results

## 🏗️ **Architecture**

### **State Management**
- `DashboardState`: Main application state and coordination
- `CodebaseState`: File tree navigation and file operations
- `AnalysisState`: Analysis results and progress (planned)
- `DiagnosticsState`: LSP error management (planned)

### **Components**
- `layout.py`: Main dashboard layout and navigation
- `file_tree.py`: Interactive file tree with search/filtering
- `analysis_results.py`: Analysis display components (planned)
- `diagnostics_panel.py`: Error/warning display (planned)

### **Analysis Engine**
- `unified_analyzer.py`: Comprehensive analysis integration
- Adapts the full UnifiedSerenaAnalyzer for Reflex state management
- Supports LSP diagnostics, symbol analysis, and health metrics

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.9+
- Reflex framework
- Graph-sitter (optional, for full analysis features)

### **Installation**
```bash
# Navigate to the dashboard directory
cd analyze/reflex_dashboard

# Install dependencies
pip install -r requirements.txt

# Initialize Reflex (if needed)
reflex init

# Run the dashboard
reflex run
```

### **Usage**
1. **Select Codebase**: Choose from available codebases in the sidebar
2. **Load Codebase**: Click "Load Codebase" to initialize analysis
3. **Explore Files**: Use the File Tree tab to browse and view files
4. **Run Analysis**: Click "Analyze" to perform comprehensive analysis
5. **View Results**: Navigate through different tabs to explore results

## 🎨 **UI Components**

### **Header**
- Logo and title
- Quick stats badges (files, errors, warnings, symbols)
- Analysis button with progress indication
- Theme toggle and settings

### **Sidebar**
- Codebase selection dropdown
- Navigation tabs (Overview, Files, Symbols, Diagnostics, etc.)
- Real-time analysis progress indicator

### **Main Content**
- Tabbed interface for different analysis views
- Responsive layout with proper error handling
- Interactive components with real-time updates

### **File Tree**
- Hierarchical directory/file display
- Search and filtering capabilities
- File type indicators and error badges
- File details panel with content viewer

## 🔧 **Technical Details**

### **Integration with Graph-Sitter**
- Direct integration with graph-sitter's Codebase class
- Support for LSP diagnostics via Serena integration
- Symbol analysis and dead code detection
- Comprehensive health metrics calculation

### **Real-time Features**
- Async analysis with progress callbacks
- Non-blocking UI updates during long operations
- Error handling with user-friendly messages
- State persistence across navigation

### **Performance Optimizations**
- Lazy loading of file tree nodes
- Content truncation for large files
- Efficient filtering and search algorithms
- Background processing for analysis tasks

## 📊 **Analysis Capabilities**

### **LSP Diagnostics**
- Error, warning, info, and hint collection
- Source attribution (pylsp, mypy, etc.)
- File-level error aggregation
- Interactive error navigation

### **Symbol Analysis**
- Function and class detection
- Complexity scoring
- Dependency tracking
- Documentation extraction

### **Codebase Health**
- Maintainability index calculation
- Technical debt scoring
- Test coverage estimation
- File size and complexity metrics

### **Serena Integration**
- LSP server status monitoring
- Code intelligence features
- Real-time error detection
- Advanced refactoring capabilities

## 🛠️ **Development**

### **Project Structure**
```
analyze/reflex_dashboard/
├── main.py                 # Main Reflex application
├── components/             # UI components
│   ├── layout.py          # Main layout
│   └── file_tree.py       # File tree component
├── state/                  # State management
│   ├── dashboard_state.py # Main state
│   └── codebase_state.py  # File operations
├── analysis/              # Analysis engine
│   └── unified_analyzer.py # Analysis integration
└── requirements.txt       # Dependencies
```

### **Adding New Features**
1. Create new state classes for complex features
2. Build reusable components in the components directory
3. Integrate with the unified analyzer for data processing
4. Add navigation items to the main layout
5. Update the README with new capabilities

### **Testing**
```bash
# Run the dashboard in development mode
reflex run --env dev

# Check for type errors
mypy analyze/reflex_dashboard/

# Format code
black analyze/reflex_dashboard/
isort analyze/reflex_dashboard/
```

## 🎯 **Next Steps**

The dashboard is built incrementally following the 10-step implementation plan:

1. ✅ **Foundation**: Basic layout and navigation
2. ✅ **File Tree**: Interactive file browser
3. ✅ **Analysis Engine**: Core analysis integration
4. 🔄 **Analysis Results**: Metrics and charts display
5. 🔄 **LSP Diagnostics**: Error/warning management
6. 🔄 **Symbol Tree**: Symbol visualization
7. 🔄 **Dead Code Analysis**: Unused code detection
8. 🔄 **Real-time Updates**: WebSocket integration
9. 🔄 **Settings**: Configuration management
10. 🔄 **Polish**: Export and documentation

## 🤝 **Contributing**

This dashboard is designed to be extensible and maintainable:

- Follow the existing state management patterns
- Create reusable components for common UI elements
- Integrate with the unified analyzer for data processing
- Maintain responsive design principles
- Add comprehensive error handling

## 📝 **License**

Part of the graph-sitter project. See the main project license for details.
