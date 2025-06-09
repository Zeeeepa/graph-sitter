# Enhanced Codebase Analytics 📊

> Advanced code analysis with interactive issue detection powered by Graph-Sitter

## 🚀 Features

### 🔍 Advanced Code Analysis
- **Graph-Sitter Integration**: Leverages the powerful graph-sitter library for precise code parsing and analysis
- **Multi-Language Support**: Analyze Python, TypeScript, JavaScript, and more
- **Real-time Processing**: Fast analysis using local graph-sitter instead of external APIs

### 🌳 Interactive Repository Structure
- **Tree View Navigation**: Explore your codebase with an interactive file tree
- **Issue Visualization**: See issue counts and severity levels at a glance
- **Drill-down Analysis**: Click on files to view detailed issue information

### 🐛 Intelligent Issue Detection
- **Critical Issues**: Implementation errors, misspelled functions, incorrect logic
- **Functional Issues**: Missing validation, incomplete implementations, TODOs
- **Minor Issues**: Unused parameters, redundant code, formatting issues
- **Context-Aware**: Provides code context and suggestions for each issue

### 📈 Comprehensive Metrics
- **Line Metrics**: LOC, LLOC, SLOC, comments, comment density
- **Complexity Metrics**: Cyclomatic complexity, Halstead metrics, maintainability index
- **Inheritance Analysis**: Depth of inheritance tracking
- **Commit Activity**: Monthly commit frequency visualization

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Graph-Sitter**: Advanced code parsing and analysis
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Recharts**: Data visualization library
- **Lucide React**: Beautiful icons

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd enhanced-codebase-analytics
   ```

2. **Install dependencies**
   ```bash
   # Install all dependencies
   npm run install:all
   
   # Or install separately
   npm run backend:install
   npm run frontend:install
   ```

3. **Start development servers**
   ```bash
   # Start both backend and frontend
   npm run dev
   
   # Or start separately
   npm run backend:dev  # Backend on http://localhost:8000
   npm run frontend:dev # Frontend on http://localhost:3000
   ```

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

## 📖 Usage

1. **Open the application** at `http://localhost:3000`

2. **Enter a repository URL** in the format:
   - `owner/repo` (e.g., `facebook/react`)
   - Full GitHub URL (e.g., `https://github.com/facebook/react`)

3. **Click "Analyze Repository"** to start the analysis

4. **Explore the results** across four main tabs:
   - **📊 Overview**: High-level metrics and charts
   - **🌳 Repository Structure**: Interactive file tree with issue counts
   - **🔍 Issues Analysis**: Detailed issue breakdown with context
   - **📈 Detailed Metrics**: Comprehensive code quality metrics

## 🔧 API Endpoints

### POST `/analyze_repo`
Analyze a repository and return comprehensive metrics.

**Request Body:**
```json
{
  "repo_url": "owner/repo"
}
```

**Response:**
```json
{
  "repo_url": "owner/repo",
  "description": "Repository description",
  "basic_metrics": {
    "files": 150,
    "functions": 500,
    "classes": 75,
    "modules": 42
  },
  "line_metrics": {
    "total": {
      "loc": 15000,
      "lloc": 12000,
      "sloc": 13000,
      "comments": 2000,
      "comment_density": 13.3
    }
  },
  "complexity_metrics": {
    "cyclomatic_complexity": { "average": 3.2 },
    "maintainability_index": { "average": 75 },
    "halstead_metrics": { "total_volume": 50000, "average_volume": 100 }
  },
  "repository_structure": { /* Interactive tree structure */ },
  "issues_summary": {
    "total": 25,
    "critical": 3,
    "functional": 12,
    "minor": 10
  },
  "detailed_issues": [ /* Array of issue details */ ]
}
```

### GET `/health`
Health check endpoint.

## 🎯 Issue Detection

The system detects various types of code issues:

### ⚠️ Critical Issues
- **Misspelled function names**: `commiter` instead of `committer`
- **Incorrect logic**: Checking `@staticmethod` instead of `@classmethod`
- **Runtime type checking**: Using `assert` for type validation
- **Null reference potential**: Calling methods without type checking

### 🐞 Functional Issues
- **Incomplete implementations**: TODO comments indicating unfinished work
- **Missing validation**: Functions that don't validate input parameters
- **Redundant decorators**: Using multiple caching decorators simultaneously

### 🔍 Minor Issues
- **Unused parameters**: Function parameters that aren't used in the implementation
- **Redundant code**: Unnecessary variable initialization or duplicate logic
- **Code style**: Formatting and style inconsistencies

## 🏗️ Architecture

```
enhanced-codebase-analytics/
├── backend/                 # FastAPI backend
│   ├── api.py              # Main API application
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js App Router
│   ├── components/        # React components
│   │   ├── ui/           # Reusable UI components
│   │   └── repo-analytics-dashboard.tsx
│   ├── lib/              # Utility functions
│   └── package.json      # Node.js dependencies
├── docker-compose.yml     # Docker configuration
└── package.json          # Root package.json for scripts
```

## 🔮 Future Enhancements

- **Multi-language Support**: Extend analysis to Java, C++, Go, and more
- **Custom Rules**: Allow users to define custom issue detection rules
- **Historical Analysis**: Track code quality metrics over time
- **Team Collaboration**: Share analysis results and collaborate on improvements
- **CI/CD Integration**: Integrate with GitHub Actions, GitLab CI, and other platforms
- **Performance Optimization**: Caching and incremental analysis for large repositories

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Graph-Sitter**: For providing the powerful code parsing foundation
- **Codegen Team**: For the original modal repo analytics inspiration
- **Open Source Community**: For the amazing tools and libraries that make this possible

---

**Built with ❤️ by the Enhanced Analytics Team**

