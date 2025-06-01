# Comprehensive Graph-Sitter Codebase Analysis Framework

A powerful, extensible framework for comprehensive codebase analysis using Graph-Sitter's parsing capabilities, featuring dynamic analysis types, database persistence, and seamless integration with the Codegen ecosystem.

## 🚀 Features

### Core Analysis Capabilities
- **Cyclomatic Complexity Analysis** - Measure control flow complexity
- **Maintainability Index** - Calculate code maintainability scores
- **Dependency Graph Analysis** - Map import relationships and detect circular dependencies
- **Code Quality Metrics** - SLOC, LLOC, Halstead metrics, and more
- **Dead Code Detection** - Identify unused functions and variables
- **Security Analysis** - Detect potential security vulnerabilities
- **AI Impact Analysis** - Track AI vs human code contributions
- **Architecture Analysis** - Evaluate architectural patterns and violations

### Dynamic Analysis System
- **Configurable Analysis Types** - Add new analyses via SQL templates
- **Template-Based Architecture** - `analysis--XXFeaturenameXX.sql` pattern
- **Project-Specific Rules** - Customizable analysis criteria
- **Real-Time Execution** - On-demand and scheduled analysis runs

### Database Architecture
- **Modular Schema Design** - Separate concerns across 4 main domains
- **Comprehensive Tracking** - Full audit trail and versioning
- **Performance Optimized** - Indexed queries and efficient storage
- **Scalable Design** - Handles large codebases and analysis volumes

### Integration Ecosystem
- **Graph-Sitter SDK** - Native integration with parsing engine
- **Codegen API** - Seamless workflow automation
- **Webhook Support** - Real-time change notifications
- **REST API** - Programmatic access to all features

## 📁 Project Structure

```
analysis_framework/
├── database_schemas/           # SQL schema definitions
│   ├── tasks/                 # Task management and workflow
│   ├── codebase/             # Codebase storage and metadata
│   ├── prompts/              # Prompt templates and management
│   └── analytics/            # Analysis results and metrics
├── analysis_templates/        # Dynamic analysis SQL templates
│   ├── complexity/           # Complexity analysis templates
│   ├── quality/              # Code quality templates
│   ├── dependencies/         # Dependency analysis templates
│   ├── security/             # Security analysis templates
│   ├── performance/          # Performance analysis templates
│   └── architecture/         # Architecture analysis templates
├── integration_layer/         # Python integration components
│   ├── graph_sitter_integration.py  # Main integration class
│   ├── database_manager.py          # Database operations
│   ├── analysis_executor.py         # Analysis execution engine
│   └── codegen_integration.py       # Codegen SDK integration
└── documentation/            # Comprehensive documentation
    ├── graph_sitter_website_analysis_report.md
    └── usage_examples.md
```

## 🛠 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Graph-Sitter SDK
- Codegen SDK (optional)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd analysis_framework
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure database**
```bash
# Create PostgreSQL database
createdb analysis_framework

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/analysis_framework"
export CODEGEN_API_KEY="your-codegen-api-key"  # Optional
export CODEGEN_ORG_ID="your-organization-id"   # Optional
```

4. **Initialize database schema**
```python
import asyncio
from integration_layer.database_manager import DatabaseManager

async def setup():
    db = DatabaseManager("postgresql://user:password@localhost/analysis_framework")
    await db.initialize()
    print("Database schema initialized successfully")
    await db.close()

asyncio.run(setup())
```

## 🚀 Quick Start

### Basic Repository Analysis

```python
import asyncio
from integration_layer.graph_sitter_integration import GraphSitterIntegration

async def analyze_repository():
    # Initialize the integration
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_framework"
    )
    
    await integration.initialize()
    
    try:
        # Analyze a repository
        result = await integration.analyze_repository(
            repo_path_or_url="https://github.com/fastapi/fastapi.git",
            analysis_types=[
                "CyclomaticComplexity",
                "MaintainabilityIndex", 
                "DependencyGraph"
            ],
            language="python"
        )
        
        print(f"Analysis completed: {result['status']}")
        print(f"Repository ID: {result['repository_id']}")
        print(f"Execution time: {result['execution_time_seconds']:.2f}s")
        
        # Display results
        for analysis_type, analysis_result in result['analysis_results'].items():
            print(f"{analysis_type}: {analysis_result['score']}/100 (Grade: {analysis_result['grade']})")
            
    finally:
        await integration.close()

# Run the analysis
asyncio.run(analyze_repository())
```

### Custom Analysis Template

Create a new analysis template in `analysis_templates/custom/`:

```sql
-- analysis_templates/custom/analysis--MyCustomAnalysis.sql

WITH custom_metrics AS (
    SELECT 
        s.file_id,
        COUNT(*) as symbol_count,
        AVG(s.complexity_score) as avg_complexity
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    WHERE f.repository_id = $1
    GROUP BY s.file_id
)

SELECT 
    'custom' as analysis_type,
    'my_custom_analysis' as analysis_subtype,
    $1 as repository_id,
    'custom_analyzer' as analyzer_name,
    '1.0.0' as analyzer_version,
    NOW() as analysis_date,
    
    jsonb_build_object(
        'summary', jsonb_build_object(
            'total_files', COUNT(*),
            'avg_symbols_per_file', AVG(symbol_count),
            'avg_complexity', AVG(avg_complexity)
        )
    ) as results,
    
    jsonb_build_object(
        'symbols_per_file', AVG(symbol_count),
        'complexity_score', AVG(avg_complexity)
    ) as metrics,
    
    GREATEST(0, LEAST(100, 100 - AVG(avg_complexity) * 5)) as score,
    
    CASE 
        WHEN AVG(avg_complexity) <= 5 THEN 'A'
        WHEN AVG(avg_complexity) <= 10 THEN 'B'
        WHEN AVG(avg_complexity) <= 15 THEN 'C'
        WHEN AVG(avg_complexity) <= 20 THEN 'D'
        ELSE 'F'
    END as grade,
    
    85.0 as confidence_level,
    ARRAY[]::text[] as recommendations,
    ARRAY[]::text[] as warnings,
    '{}'::jsonb as metadata

FROM custom_metrics;
```

## 📊 Analysis Types

### Built-in Analysis Templates

| Analysis Type | Description | Key Metrics |
|---------------|-------------|-------------|
| **CyclomaticComplexity** | Measures control flow complexity | Average complexity, high-complexity functions |
| **MaintainabilityIndex** | Calculates maintainability scores | MI score, low-maintainability functions |
| **DependencyGraph** | Analyzes import relationships | Fan-in/fan-out, circular dependencies |
| **CodeQuality** | Overall code quality assessment | Quality score, issue count |
| **DeadCodeDetection** | Identifies unused code | Dead functions, unused variables |
| **SecurityAnalysis** | Detects security vulnerabilities | Vulnerability count by severity |

### Creating Custom Analyses

1. **Create SQL Template**: Add `analysis--YourAnalysisName.sql` to appropriate category folder
2. **Follow Template Pattern**: Use the standard result structure
3. **Register Analysis**: Add to analysis executor configuration
4. **Test and Validate**: Ensure proper scoring and grading

## 🗄 Database Schema

### Core Tables

#### Tasks Schema
- `tasks` - Task management and workflow
- `task_executions` - Execution history and audit trail
- `task_schedules` - Recurring task scheduling
- `task_templates` - Reusable task definitions

#### Codebase Schema
- `repositories` - Repository metadata and configuration
- `files` - File system structure and metadata
- `symbols` - Code symbols (functions, classes, variables)
- `imports` - Import relationships and dependencies
- `commits` - Git commit information

#### Analytics Schema
- `analysis_results` - Comprehensive analysis results
- `code_metrics` - Aggregated metrics at different levels
- `quality_assessments` - Quality scores and assessments
- `security_analysis` - Security vulnerability tracking
- `trend_analysis` - Trend data over time

#### Prompts Schema
- `prompt_templates` - AI prompt templates
- `prompt_executions` - Prompt execution history
- `prompt_chains` - Multi-step prompt workflows
- `prompt_evaluations` - Quality assessments

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL="postgresql://user:password@localhost/analysis_framework"
DATABASE_POOL_SIZE=10

# Codegen Integration (Optional)
CODEGEN_API_KEY="your-api-key"
CODEGEN_ORG_ID="your-organization-id"

# Analysis Configuration
DEFAULT_ANALYSIS_TYPES="CyclomaticComplexity,MaintainabilityIndex,DependencyGraph"
ANALYSIS_TIMEOUT_SECONDS=3600
ENABLE_CACHING=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Analysis Configuration

```python
# Custom analysis configuration
config = {
    "complexity_thresholds": {
        "low": 5,
        "medium": 10,
        "high": 15,
        "critical": 25
    },
    "maintainability_thresholds": {
        "excellent": 60,
        "good": 40,
        "moderate": 20,
        "poor": 10
    },
    "security_scan_level": "comprehensive",
    "include_test_files": True,
    "exclude_patterns": ["*.min.js", "node_modules/*"]
}
```

## 📈 Monitoring and Alerting

### Health Monitoring

```python
# Get system health status
async def check_system_health():
    db_manager = DatabaseManager(DATABASE_URL)
    await db_manager.initialize()
    
    stats = await db_manager.get_database_stats()
    print(f"System Health: {stats}")
    
    # Check for failed analyses
    failed_analyses = await db_manager.execute_query(
        "SELECT COUNT(*) FROM analysis_results WHERE score < 50",
        fetch="val"
    )
    
    if failed_analyses > 10:
        print("WARNING: High number of low-scoring analyses detected")
    
    await db_manager.close()
```

### Automated Alerts

Set up automated alerts for:
- Analysis failures
- Critical security vulnerabilities
- Performance degradation
- System resource usage

## 🔌 API Integration

### REST API Endpoints

```python
from fastapi import FastAPI
from integration_layer.graph_sitter_integration import GraphSitterIntegration

app = FastAPI()
integration = GraphSitterIntegration(DATABASE_URL)

@app.post("/analyze")
async def analyze_repository(request: AnalysisRequest):
    """Trigger repository analysis"""
    result = await integration.analyze_repository(
        repo_path_or_url=request.repo_url,
        analysis_types=request.analysis_types
    )
    return result

@app.get("/results/{repo_id}")
async def get_analysis_results(repo_id: str):
    """Get analysis results for a repository"""
    results = await integration.get_analysis_results(repo_id)
    return results

@app.get("/health")
async def health_check():
    """System health check"""
    return {"status": "healthy", "timestamp": datetime.now()}
```

### Webhook Integration

```python
@app.post("/webhook/github")
async def github_webhook(payload: dict, background_tasks: BackgroundTasks):
    """Handle GitHub webhook for automatic analysis"""
    
    if payload.get("action") == "push":
        repo_url = payload["repository"]["clone_url"]
        branch = payload["ref"].split("/")[-1]
        
        # Schedule background analysis
        background_tasks.add_task(
            integration.analyze_repository,
            repo_path_or_url=repo_url,
            branch=branch
        )
        
        return {"status": "analysis_scheduled"}
    
    return {"status": "no_action"}
```

## 🧪 Testing

### Unit Tests

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run with coverage
python -m pytest --cov=analysis_framework tests/
```

### Test Analysis Templates

```python
import asyncio
from integration_layer.analysis_executor import AnalysisExecutor

async def test_analysis_template():
    """Test a specific analysis template"""
    
    executor = AnalysisExecutor(db_manager)
    
    # Test with sample repository
    result = await executor.execute_analysis(
        "CyclomaticComplexity",
        sample_repo_id
    )
    
    assert result['score'] >= 0
    assert result['score'] <= 100
    assert result['grade'] in ['A', 'B', 'C', 'D', 'F']
    assert 'results' in result
    assert 'metrics' in result

asyncio.run(test_analysis_template())
```

## 📚 Documentation

- **[Website Analysis Report](documentation/graph_sitter_website_analysis_report.md)** - Comprehensive Graph-Sitter capabilities analysis
- **[Usage Examples](documentation/usage_examples.md)** - Detailed usage examples and tutorials
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Database Schema](docs/database_schema.md)** - Detailed schema documentation

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Add your analysis template** or **improve existing functionality**
4. **Write tests** for your changes
5. **Update documentation** as needed
6. **Submit a pull request**

### Adding New Analysis Types

1. Create SQL template in appropriate category folder
2. Follow the standard result structure
3. Add comprehensive test coverage
4. Update documentation
5. Submit PR with example usage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Graph-Sitter Team** - For the powerful parsing engine
- **Codegen Team** - For the integration ecosystem
- **Open Source Community** - For inspiration and best practices

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/analysis-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/analysis-framework/discussions)
- **Documentation**: [Wiki](https://github.com/your-org/analysis-framework/wiki)

---

**Built with ❤️ for the developer community**

