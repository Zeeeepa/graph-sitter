# Enhanced Codebase Analytics 📊

A comprehensive code analysis platform that provides detailed insights into repository structure, code quality, and potential issues. Built with FastAPI backend and Next.js frontend, featuring interactive visualizations and real-time analysis.

## 🚀 Features

### Core Analysis Capabilities
- **Repository Structure Visualization**: Interactive tree view of your codebase
- **Issue Detection**: Identifies Critical, Functional, and Minor code issues
- **Metrics Calculation**: Lines of code, complexity metrics, and maintainability scores
- **Git History Analysis**: Commit activity and contribution patterns
- **Multi-language Support**: Python, JavaScript, TypeScript, JSX, TSX

### Issue Detection Categories
- **🔴 Critical Issues**: Implementation errors, misspelled functions, incorrect logic
- **🟡 Functional Issues**: Missing validation, incomplete implementations, TODOs
- **🔵 Minor Issues**: Unused parameters, redundant code, formatting issues

### Visualizations
- Repository structure with issue counts
- Complexity metrics charts
- Commit activity timeline
- Issue distribution analysis

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and serialization
- **Git Integration**: Repository cloning and analysis
- **Code Analysis**: Custom static analysis engine

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Interactive data visualizations
- **Radix UI**: Accessible component primitives

## 📦 Installation & Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Docker (optional, for containerized deployment)

### Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Zeeeepa/codebase-analytics.git
   cd codebase-analytics
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start development servers**
   ```bash
   # Option 1: Use the development deployment script
   ./dev-deploy.sh --install-deps
   
   # Option 2: Start services manually
   # Terminal 1 - Backend
   cd backend && python api.py
   
   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

### Production Deployment

#### Docker Deployment (Recommended)
```bash
# Build and start all services
./deploy.sh --env production --rebuild

# Services will be available at:
# - Frontend: http://localhost
# - API: http://localhost/api
# - API Docs: http://localhost/api/docs
```

#### Manual Production Deployment
```bash
# Backend
cd backend
pip install -r requirements.txt
python api.py

# Frontend
cd frontend
npm install
npm run build
npm start
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend
PYTHONUNBUFFERED=1

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Configuration
The application includes comprehensive Docker setup:
- **Backend Dockerfile**: Python 3.11 with security optimizations
- **Frontend Dockerfile**: Multi-stage Node.js build
- **Nginx Configuration**: Load balancing and security headers
- **Docker Compose**: Orchestrated multi-service deployment

## 📖 API Documentation

### Health Check
```bash
GET /health
```

### Repository Analysis
```bash
POST /analyze_repo
Content-Type: application/json

{
  "repo_url": "https://github.com/owner/repo"
}
```

**Response Structure:**
```json
{
  "repo_url": "string",
  "description": "string",
  "basic_metrics": {
    "files": 0,
    "functions": 0,
    "classes": 0,
    "modules": 0
  },
  "line_metrics": {
    "total": {
      "loc": 0,
      "lloc": 0,
      "comments": 0,
      "comment_density": 0.0
    }
  },
  "complexity_metrics": {
    "cyclomatic_complexity": {"average": 0.0},
    "maintainability_index": {"average": 0.0}
  },
  "repository_structure": {
    "name": "string",
    "type": "directory",
    "children": []
  },
  "issues_summary": {
    "total": 0,
    "critical": 0,
    "functional": 0,
    "minor": 0
  },
  "detailed_issues": [],
  "monthly_commits": {}
}
```

## 🎯 Usage Examples

### Analyze a Repository
```bash
curl -X POST "http://localhost:8000/analyze_repo" \\
     -H "Content-Type: application/json" \\
     -d '{"repo_url": "https://github.com/facebook/react"}'
```

### Frontend Integration
```typescript
const analyzeRepository = async (repoUrl: string) => {
  const response = await fetch('/api/analyze_repo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl })
  });
  return response.json();
};
```

## 🔍 Issue Detection Examples

### Critical Issues
- **Misspelled Functions**: `def commiter()` → Should be `committer`
- **Incorrect Logic**: Checking `@staticmethod` instead of `@classmethod`
- **Runtime Errors**: Using `assert` for type checking in production

### Functional Issues
- **Incomplete Work**: TODO comments indicating unfinished features
- **Redundant Code**: Multiple caching decorators on same function
- **Missing Validation**: Functions without input validation

### Minor Issues
- **Code Quality**: Unused function parameters
- **Style Issues**: Inconsistent formatting
- **Documentation**: Missing or incomplete docstrings

## 🚀 Deployment Scripts

### Development Deployment
```bash
# Start both services
./dev-deploy.sh

# Backend only
./dev-deploy.sh --backend-only

# Frontend only
./dev-deploy.sh --frontend-only

# Install dependencies first
./dev-deploy.sh --install-deps
```

### Production Deployment
```bash
# Full production deployment
./deploy.sh --env production

# Force rebuild
./deploy.sh --env production --rebuild

# Show logs
./deploy.sh --env production --logs
```

## 🔒 Security Features

- **Rate Limiting**: API and frontend request throttling
- **Security Headers**: XSS protection, content type validation
- **CORS Configuration**: Controlled cross-origin requests
- **Input Validation**: Comprehensive request validation
- **Non-root Containers**: Security-hardened Docker images

## 📊 Monitoring & Health Checks

- **Health Endpoints**: `/health` for service monitoring
- **Docker Health Checks**: Automated container health monitoring
- **Service Dependencies**: Proper startup ordering
- **Graceful Shutdown**: Clean service termination

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the deployment logs

## 🎉 Acknowledgments

- Built with modern web technologies
- Inspired by code quality tools
- Community-driven development

---

**Ready to analyze your codebase? Start with the quick deployment guide above! 🚀**

