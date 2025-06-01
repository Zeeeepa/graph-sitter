# Codebase Analysis Dashboard System

This document describes the comprehensive codebase analysis dashboard system that provides interactive, hierarchical views of code quality, issues, and dependencies with expandable React components.

## 🎯 Overview

The dashboard system transforms static code analysis into an interactive exploration tool that allows developers to:

- **View Code Problems**: Identify implementation issues, wrong parameters, and function call problems
- **Analyze Impact**: Understand blast radius and dependencies across modules
- **Explore Function Flows**: Visualize call sequences and function relationships
- **AI-Powered Analysis**: Get intelligent recommendations for code improvements
- **Hierarchical Navigation**: Drill down from codebase overview to specific issues

## 🏗️ Architecture

### Core Components

1. **CodebaseAnalyzer**: Main analysis engine that detects issues and builds impact graphs
2. **Dashboard API**: FastAPI-based REST service for serving analysis data
3. **React Components**: Interactive UI components for expandable dashboard views
4. **Issue Detection System**: Pluggable detectors for different problem types

### Data Flow

```
Codebase → CodebaseAnalyzer → Issues + Impact Graph → Dashboard API → React UI
    ↓              ↓                    ↓                  ↓           ↓
Static Code → Analysis Engine → Structured Data → REST Endpoints → Interactive UI
```

## 📊 Issue Detection System

### Issue Categories

The system detects issues across multiple categories:

- **Implementation**: Logic errors, wrong implementations
- **Documentation**: Missing or poor documentation
- **Performance**: Inefficient code patterns
- **Security**: Potential security vulnerabilities
- **Maintainability**: Complex or hard-to-maintain code
- **Dead Code**: Unused functions and classes
- **Dependencies**: Circular dependencies, import issues
- **Parameters**: Too many parameters, missing type annotations
- **Error Handling**: Missing try-catch blocks, poor error handling

### Severity Levels

Issues are classified by severity:

- **Critical**: Major problems that could cause system failures
- **High**: Important issues that should be addressed soon
- **Medium**: Moderate issues that affect code quality
- **Low**: Minor issues or style improvements
- **Info**: Informational notices

### Issue Detection Examples

```python
from graph_sitter.codebase.codebase_analysis import CodebaseAnalyzer

# Initialize analyzer
codebase = Codebase("./my_project")
analyzer = CodebaseAnalyzer(codebase)

# Detect all issues
issues = analyzer.detect_issues()

# Filter by severity
critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]

# Filter by category
doc_issues = [i for i in issues if i.category == IssueCategory.DOCUMENTATION]
```

## 🌳 Hierarchical Data Structure

### AnalysisNode Structure

The dashboard uses a hierarchical `AnalysisNode` structure:

```python
@dataclass
class AnalysisNode:
    id: str                    # Unique identifier
    name: str                  # Display name
    type: str                  # Node type (codebase, category, file, etc.)
    summary: Dict[str, Any]    # Summary statistics
    issues: List[CodeIssue]    # Issues at this level
    children: List[AnalysisNode]  # Child nodes
    metadata: Dict[str, Any]   # Additional metadata
    expandable: bool = True    # Whether node can be expanded
```

### Node Types

- **codebase**: Root node containing overall analysis
- **category**: Issue category groupings
- **files**: File-based analysis grouping
- **file**: Individual file analysis
- **flows**: Function flow analysis grouping
- **function_flow**: Individual function flow analysis

### Example Hierarchy

```
Codebase Analysis (root)
├── Documentation Issues (category)
│   ├── Missing docstring: process_data
│   └── Missing docstring: validate_input
├── Dead Code Issues (category)
│   └── Unused function: legacy_helper
├── Files Analysis (files)
│   ├── src/main.py (file)
│   │   ├── 3 functions, 1 class
│   │   └── 2 issues
│   └── src/utils.py (file)
└── Function Flows (flows)
    └── Flow: process_data (function_flow)
        ├── 5 incoming calls
        └── 8 outgoing calls
```

## 🔧 API Endpoints

### Core Endpoints

#### Initialize Codebase
```http
POST /codebase/{codebase_id}
Content-Type: application/json

{
  "path": "/path/to/codebase"
}
```

#### Get Dashboard Data
```http
GET /dashboard/{codebase_id}
```

Returns hierarchical `AnalysisNode` structure for expandable UI.

#### Get Issues
```http
GET /issues/{codebase_id}?severity=high&category=documentation&limit=50
```

Returns filtered list of issues with optional filtering by severity and category.

#### Get Function Context
```http
GET /function/{codebase_id}/{function_name}
```

Returns detailed context including dependencies, usages, call sites, and function calls.

#### Get Blast Radius
```http
GET /blast_radius/{codebase_id}/{symbol_name}?symbol_type=Function
```

Returns impact analysis showing all symbols affected by changes to the target symbol.

#### AI Analysis
```http
POST /analyze/{codebase_id}/ai
Content-Type: application/json

{
  "issue_id": "doc_missing_process_data"
}
```

Triggers AI-powered analysis of a specific issue.

### Response Examples

#### Dashboard Data Response
```json
{
  "id": "codebase_root",
  "name": "Codebase Analysis",
  "type": "codebase",
  "summary": {
    "total_files": 45,
    "total_functions": 123,
    "total_classes": 28,
    "total_issues": 15
  },
  "issues": [],
  "children": [
    {
      "id": "category_documentation",
      "name": "Documentation",
      "type": "category",
      "summary": {
        "total_issues": 8,
        "severity_breakdown": {
          "high": 3,
          "medium": 5
        }
      },
      "issues": [
        {
          "id": "doc_missing_process_data",
          "title": "Missing docstring: process_data",
          "description": "Function 'process_data' lacks documentation",
          "severity": "high",
          "category": "documentation",
          "file_path": "src/processor.py",
          "line_start": 45,
          "symbol_name": "process_data",
          "symbol_type": "Function",
          "impact_score": 7.5,
          "suggested_fix": "Add a comprehensive docstring describing the function's purpose, parameters, and return value"
        }
      ],
      "children": []
    }
  ]
}
```

## ⚛️ React Components

### Main Components

#### CodebaseAnalysisDashboard
Main dashboard component that fetches and displays analysis data.

```tsx
<CodebaseAnalysisDashboard codebaseId="my-project" />
```

#### AnalysisNodeComponent
Expandable component for hierarchical analysis nodes.

```tsx
<AnalysisNodeComponent 
  node={analysisNode} 
  level={0}
  onAnalyzeWithAI={handleAIAnalysis}
/>
```

#### IssueCard
Individual issue display with expandable details.

```tsx
<IssueCard 
  issue={codeIssue} 
  onAnalyzeWithAI={handleAIAnalysis}
/>
```

### Key Features

- **Expandable Hierarchy**: Click to expand/collapse nodes
- **Issue Filtering**: Filter by severity and category
- **AI Integration**: Trigger AI analysis for specific issues
- **Impact Visualization**: Show blast radius and affected symbols
- **Real-time Updates**: Refresh data when analysis changes

### Styling

Components use Tailwind CSS for styling with:
- Severity-based color coding
- Responsive grid layouts
- Smooth animations and transitions
- Accessible design patterns

## 🚀 Usage Examples

### Basic Setup

```python
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import CodebaseAnalyzer

# Initialize codebase
codebase = Codebase("./my_project")

# Create analyzer
analyzer = CodebaseAnalyzer(codebase)

# Generate dashboard data
dashboard_data = analyzer.generate_dashboard_data()

# Convert to JSON for API
json_data = analyzer.to_json(dashboard_data)
```

### Running the API Server

```python
from graph_sitter.dashboard.api import app
import uvicorn

# Start the API server
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### React Integration

```tsx
import CodebaseAnalysisDashboard from './components/CodebaseAnalysisDashboard';

function App() {
  return (
    <div className="App">
      <CodebaseAnalysisDashboard codebaseId="my-project" />
    </div>
  );
}
```

## 🔍 Advanced Features

### Impact Analysis

The system builds an impact graph to calculate blast radius:

```python
# Get blast radius for a function
blast_radius = analyzer.get_blast_radius("process_data", "Function")
print(f"Changing process_data affects {len(blast_radius)} symbols")
```

### AI-Powered Analysis

Integration with enhanced codebase AI for intelligent issue analysis:

```python
# Analyze issue with AI
issue = issues[0]
ai_analysis = await analyzer.analyze_with_ai(issue)
print(f"AI recommendation: {ai_analysis}")
```

### Function Context Analysis

Detailed context gathering for functions:

```python
from graph_sitter.codebase.codebase_analysis import get_function_context

# Get comprehensive function context
function = codebase.get_function("process_data")
context = get_function_context(function)

print(f"Dependencies: {len(context['dependencies'])}")
print(f"Usages: {len(context['usages'])}")
print(f"Call sites: {len(context['call_sites'])}")
```

### Training Data Generation

Generate training data for ML models:

```python
from graph_sitter.codebase.codebase_analysis import run_training_data_generation

# Generate training data
training_data = run_training_data_generation(codebase)

# Save for ML training
with open("training_data.json", "w") as f:
    json.dump(training_data, f, indent=2)
```

## 📈 Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Load child nodes only when expanded
2. **Caching**: Cache analysis results for repeated requests
3. **Pagination**: Limit number of issues/nodes returned
4. **Incremental Analysis**: Update only changed parts of the codebase

### Scalability

- **Large Codebases**: Use sampling for initial analysis
- **Real-time Updates**: WebSocket connections for live updates
- **Distributed Analysis**: Split analysis across multiple workers
- **Database Storage**: Store analysis results for persistence

## 🛠️ Configuration

### Environment Variables

```bash
# API Configuration
DASHBOARD_API_HOST=0.0.0.0
DASHBOARD_API_PORT=8000

# Analysis Configuration
MAX_ISSUES_PER_CATEGORY=100
ENABLE_AI_ANALYSIS=true
AI_ANALYSIS_TIMEOUT=30

# Caching
ENABLE_CACHING=true
CACHE_TTL=3600
```

### Analysis Configuration

```python
# Configure analysis behavior
analyzer = CodebaseAnalyzer(codebase)
analyzer.config = {
    "max_blast_radius_depth": 10,
    "enable_ai_analysis": True,
    "issue_severity_threshold": IssueSeverity.MEDIUM,
    "max_function_complexity": 50
}
```

## 🧪 Testing

### Unit Tests

```python
def test_issue_detection():
    codebase = Codebase("./test_project")
    analyzer = CodebaseAnalyzer(codebase)
    issues = analyzer.detect_issues()
    
    assert len(issues) > 0
    assert any(i.category == IssueCategory.DOCUMENTATION for i in issues)

def test_dashboard_data_generation():
    analyzer = CodebaseAnalyzer(codebase)
    dashboard_data = analyzer.generate_dashboard_data()
    
    assert dashboard_data.type == "codebase"
    assert len(dashboard_data.children) > 0
```

### API Tests

```python
def test_dashboard_endpoint():
    response = client.get("/dashboard/test-codebase")
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == "codebase"
    assert "children" in data
```

## 📚 Integration Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Codebase Analysis
  run: |
    python -m graph_sitter.dashboard.analyze \
      --codebase-path . \
      --output analysis-report.json \
      --fail-on-critical
```

### IDE Integration

```python
# VS Code extension integration
def analyze_current_file():
    file_path = get_current_file_path()
    codebase = Codebase(".")
    analyzer = CodebaseAnalyzer(codebase)
    
    file_issues = [i for i in analyzer.detect_issues() 
                   if i.file_path == file_path]
    
    display_issues_in_editor(file_issues)
```

### Webhook Integration

```python
# Webhook for real-time updates
@app.post("/webhook/code-change")
async def handle_code_change(payload: dict):
    codebase_id = payload["codebase_id"]
    changed_files = payload["changed_files"]
    
    # Incremental analysis
    analyzer = get_analyzer(codebase_id)
    new_issues = analyzer.analyze_files(changed_files)
    
    # Notify dashboard clients
    await notify_dashboard_clients(codebase_id, new_issues)
```

## 🔮 Future Enhancements

### Planned Features

1. **Real-time Analysis**: Live updates as code changes
2. **Machine Learning**: AI-powered issue prediction
3. **Multi-language Support**: Extend beyond Python
4. **Collaborative Features**: Team-based issue tracking
5. **Integration Ecosystem**: Plugins for popular tools

### Roadmap

- **Q1**: Enhanced AI analysis capabilities
- **Q2**: Real-time dashboard updates
- **Q3**: Multi-language support (TypeScript/JavaScript)
- **Q4**: Machine learning-based issue prediction

This comprehensive dashboard system provides a powerful foundation for interactive codebase analysis while maintaining flexibility for future enhancements and integrations.

