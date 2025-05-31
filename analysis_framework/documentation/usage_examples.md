# Graph-Sitter Codebase Analysis Framework - Usage Examples

## Overview

This document provides comprehensive usage examples for the Graph-Sitter Codebase Analysis Framework, demonstrating how to leverage the dynamic analysis system, database schemas, and integration capabilities.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Repository Analysis](#repository-analysis)
3. [Dynamic Analysis Templates](#dynamic-analysis-templates)
4. [Database Operations](#database-operations)
5. [Integration with Codegen SDK](#integration-with-codegen-sdk)
6. [Custom Analysis Development](#custom-analysis-development)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Performance Optimization](#performance-optimization)

## Basic Setup

### Environment Configuration

```bash
# Install dependencies
pip install asyncpg graph-sitter psycopg2-binary

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/analysis_db"
export CODEGEN_API_KEY="your-codegen-api-key"
export CODEGEN_ORG_ID="your-organization-id"
```

### Database Initialization

```python
import asyncio
from analysis_framework.integration_layer.database_manager import DatabaseManager

async def setup_database():
    """Initialize the analysis framework database"""
    db_manager = DatabaseManager(
        database_url="postgresql://user:password@localhost/analysis_db"
    )
    
    await db_manager.initialize()
    print("Database schema initialized successfully")
    
    # Verify setup
    stats = await db_manager.get_database_stats()
    print(f"Database statistics: {stats}")
    
    await db_manager.close()

# Run setup
asyncio.run(setup_database())
```

## Repository Analysis

### Basic Repository Analysis

```python
import asyncio
from analysis_framework.integration_layer.graph_sitter_integration import GraphSitterIntegration

async def analyze_repository():
    """Perform comprehensive repository analysis"""
    
    # Initialize integration
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_db",
        codegen_api_key="your-api-key",
        codegen_org_id="your-org-id"
    )
    
    await integration.initialize()
    
    try:
        # Analyze a GitHub repository
        result = await integration.analyze_repository(
            repo_path_or_url="https://github.com/fastapi/fastapi.git",
            analysis_types=[
                "CyclomaticComplexity",
                "MaintainabilityIndex", 
                "DependencyGraph",
                "SecurityAnalysis"
            ],
            language="python",
            branch="main",
            config={
                "include_tests": True,
                "complexity_threshold": 15,
                "security_scan_level": "comprehensive"
            }
        )
        
        print(f"Analysis Status: {result['status']}")
        print(f"Repository ID: {result['repository_id']}")
        print(f"Execution Time: {result['execution_time_seconds']:.2f}s")
        
        # Display summary
        summary = result['codebase_summary']
        print(f"\nCodebase Summary:")
        print(f"  Files: {summary['file_count']}")
        print(f"  Functions: {summary['function_count']}")
        print(f"  Classes: {summary['class_count']}")
        print(f"  Total Lines: {summary['total_lines']:,}")
        print(f"  Languages: {', '.join(summary['languages'])}")
        
        # Display analysis results
        for analysis_type, analysis_result in result['analysis_results'].items():
            if analysis_result.get('status') == 'completed':
                print(f"\n{analysis_type} Analysis:")
                print(f"  Score: {analysis_result['score']}/100")
                print(f"  Grade: {analysis_result['grade']}")
                print(f"  Confidence: {analysis_result['confidence_level']}%")
        
    finally:
        await integration.close()

# Run analysis
asyncio.run(analyze_repository())
```

### Local Repository Analysis

```python
async def analyze_local_repository():
    """Analyze a local repository"""
    
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_db"
    )
    
    await integration.initialize()
    
    try:
        result = await integration.analyze_repository(
            repo_path_or_url="/path/to/local/repository",
            analysis_types=["CyclomaticComplexity", "MaintainabilityIndex"],
            language="typescript"
        )
        
        print(f"Local analysis completed: {result['status']}")
        
    finally:
        await integration.close()

asyncio.run(analyze_local_repository())
```

## Dynamic Analysis Templates

### Running Specific Analysis Templates

```python
from analysis_framework.integration_layer.analysis_executor import AnalysisExecutor
from analysis_framework.integration_layer.database_manager import DatabaseManager

async def run_specific_analysis():
    """Run a specific analysis template"""
    
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    executor = AnalysisExecutor(db_manager)
    
    # Get repository ID
    repo = await db_manager.get_repository_by_name("fastapi/fastapi")
    repo_id = repo['id']
    
    # Run cyclomatic complexity analysis
    complexity_result = await executor.execute_analysis(
        "CyclomaticComplexity", 
        repo_id
    )
    
    print("Complexity Analysis Results:")
    print(f"Average Complexity: {complexity_result['metrics']['average_complexity']}")
    print(f"High Complexity Functions: {complexity_result['metrics']['high_complexity_ratio']}%")
    
    # Run maintainability analysis
    maintainability_result = await executor.execute_analysis(
        "MaintainabilityIndex",
        repo_id
    )
    
    print("\nMaintainability Analysis Results:")
    print(f"Average Maintainability: {maintainability_result['metrics']['average_maintainability']}")
    print(f"Low Maintainability Ratio: {maintainability_result['metrics']['low_maintainability_ratio']}%")
    
    await db_manager.close()

asyncio.run(run_specific_analysis())
```

### Creating Custom Analysis Templates

```sql
-- analysis_templates/custom/analysis--CodeDocumentation.sql
-- Custom analysis template for documentation coverage

WITH file_documentation AS (
    SELECT 
        f.id as file_id,
        f.file_path,
        f.language,
        f.line_count,
        COUNT(s.id) as total_symbols,
        COUNT(CASE WHEN s.docstring IS NOT NULL AND LENGTH(s.docstring) > 10 THEN 1 END) as documented_symbols,
        -- Calculate documentation ratio
        CASE 
            WHEN COUNT(s.id) > 0 THEN 
                (COUNT(CASE WHEN s.docstring IS NOT NULL AND LENGTH(s.docstring) > 10 THEN 1 END)::decimal / COUNT(s.id)) * 100
            ELSE 0
        END as documentation_ratio
    FROM files f
    LEFT JOIN symbols s ON f.id = s.file_id
    WHERE f.repository_id = $1
    AND s.symbol_type IN ('function', 'class', 'method')
    GROUP BY f.id, f.file_path, f.language, f.line_count
),
repository_documentation AS (
    SELECT 
        $1 as repository_id,
        COUNT(*) as total_files,
        SUM(total_symbols) as total_symbols,
        SUM(documented_symbols) as documented_symbols,
        AVG(documentation_ratio) as avg_documentation_ratio,
        COUNT(CASE WHEN documentation_ratio < 50 THEN 1 END) as poorly_documented_files
    FROM file_documentation
    WHERE total_symbols > 0
)

SELECT 
    'quality' as analysis_type,
    'code_documentation' as analysis_subtype,
    rd.repository_id,
    'documentation_analyzer' as analyzer_name,
    '1.0.0' as analyzer_version,
    NOW() as analysis_date,
    
    -- Results JSON
    jsonb_build_object(
        'summary', jsonb_build_object(
            'total_files', rd.total_files,
            'total_symbols', rd.total_symbols,
            'documented_symbols', rd.documented_symbols,
            'avg_documentation_ratio', ROUND(rd.avg_documentation_ratio, 2),
            'poorly_documented_files', rd.poorly_documented_files
        ),
        'file_breakdown', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'file_path', file_path,
                    'language', language,
                    'documentation_ratio', ROUND(documentation_ratio, 2),
                    'total_symbols', total_symbols,
                    'documented_symbols', documented_symbols
                )
            )
            FROM file_documentation
            ORDER BY documentation_ratio ASC
            LIMIT 20
        )
    ) as results,
    
    -- Metrics
    jsonb_build_object(
        'documentation_coverage', ROUND(rd.avg_documentation_ratio, 2),
        'documented_symbols_ratio', ROUND((rd.documented_symbols::decimal / rd.total_symbols) * 100, 2)
    ) as metrics,
    
    -- Score (0-100)
    GREATEST(0, LEAST(100, rd.avg_documentation_ratio)) as score,
    
    -- Grade
    CASE 
        WHEN rd.avg_documentation_ratio >= 80 THEN 'A'
        WHEN rd.avg_documentation_ratio >= 60 THEN 'B'
        WHEN rd.avg_documentation_ratio >= 40 THEN 'C'
        WHEN rd.avg_documentation_ratio >= 20 THEN 'D'
        ELSE 'F'
    END as grade,
    
    90.0 as confidence_level,
    
    -- Recommendations
    ARRAY[
        CASE WHEN rd.avg_documentation_ratio < 50 THEN 
            'Documentation coverage is below 50%. Consider adding docstrings to key functions and classes.'
        END,
        CASE WHEN rd.poorly_documented_files > rd.total_files * 0.3 THEN 
            'More than 30% of files have poor documentation. Implement documentation standards.'
        END
    ]::text[] as recommendations,
    
    -- Metadata
    jsonb_build_object(
        'analysis_parameters', jsonb_build_object(
            'minimum_docstring_length', 10,
            'symbol_types_analyzed', ARRAY['function', 'class', 'method']
        )
    ) as metadata

FROM repository_documentation rd
WHERE rd.repository_id = $1;
```

## Database Operations

### Querying Analysis Results

```python
async def query_analysis_results():
    """Query and analyze stored results"""
    
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    # Get repository
    repo = await db_manager.get_repository_by_name("fastapi/fastapi")
    repo_id = str(repo['id'])
    
    # Get all analysis results
    results = await db_manager.get_analysis_results(repo_id)
    
    print(f"Found {len(results)} analysis results")
    
    for result in results:
        print(f"\nAnalysis: {result['analysis_type']} - {result['analysis_subtype']}")
        print(f"Date: {result['analysis_date']}")
        print(f"Score: {result['score']}/100 (Grade: {result['grade']})")
        print(f"Analyzer: {result['analyzer_name']} v{result['analyzer_version']}")
        
        if result['warnings']:
            print(f"Warnings: {len(result['warnings'])}")
            for warning in result['warnings'][:3]:  # Show first 3 warnings
                print(f"  - {warning}")
    
    # Get specific metrics
    complexity_metrics = await db_manager.get_code_metrics(
        repo_id, 
        metric_type="complexity"
    )
    
    print(f"\nComplexity Metrics: {len(complexity_metrics)} entries")
    
    # Get security issues
    security_issues = await db_manager.get_security_issues(repo_id)
    print(f"Security Issues: {len(security_issues)} open issues")
    
    await db_manager.close()

asyncio.run(query_analysis_results())
```

### Trend Analysis

```python
async def analyze_trends():
    """Analyze trends over time"""
    
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    repo = await db_manager.get_repository_by_name("fastapi/fastapi")
    repo_id = str(repo['id'])
    
    # Get trend data for complexity
    trend_data = await db_manager.get_trend_data(
        repo_id,
        metric_type="complexity",
        metric_name="average_complexity",
        time_period="weekly"
    )
    
    if trend_data:
        print("Complexity Trend Analysis:")
        print(f"Trend Direction: {trend_data['trend_direction']}")
        print(f"Trend Strength: {trend_data['trend_strength']}")
        
        # Parse data points
        import json
        data_points = json.loads(trend_data['data_points'])
        print(f"Data Points: {len(data_points)}")
        
        for point in data_points[-5:]:  # Last 5 data points
            print(f"  {point['date']}: {point['value']}")
    
    await db_manager.close()

asyncio.run(analyze_trends())
```

## Integration with Codegen SDK

### Automated Analysis Workflow

```python
from codegen import Agent
from analysis_framework.integration_layer.graph_sitter_integration import GraphSitterIntegration

async def automated_analysis_workflow():
    """Automated workflow using Codegen SDK"""
    
    # Initialize Codegen agent
    agent = Agent(
        org_id="your-org-id",
        token="your-api-token"
    )
    
    # Initialize analysis framework
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_db",
        codegen_api_key="your-api-key",
        codegen_org_id="your-org-id"
    )
    
    await integration.initialize()
    
    try:
        # Analyze repository
        repo_url = "https://github.com/example/project.git"
        analysis_result = await integration.analyze_repository(repo_url)
        
        # Check for critical issues
        critical_issues = []
        for analysis_type, result in analysis_result['analysis_results'].items():
            if result.get('grade') in ['D', 'F']:
                critical_issues.append(f"{analysis_type}: {result['grade']}")
        
        if critical_issues:
            # Create Codegen task for remediation
            remediation_prompt = f"""
            The following critical code quality issues were found in {repo_url}:
            
            {chr(10).join(critical_issues)}
            
            Please analyze the repository and create a plan to address these issues.
            Focus on the most critical problems first.
            """
            
            task = agent.run(prompt=remediation_prompt)
            print(f"Created remediation task: {task.id}")
            
            # Monitor task progress
            while task.status in ['pending', 'running']:
                await asyncio.sleep(30)
                task.refresh()
                print(f"Task status: {task.status}")
            
            if task.status == 'completed':
                print(f"Remediation plan: {task.result}")
        
    finally:
        await integration.close()

asyncio.run(automated_analysis_workflow())
```

### Webhook Integration

```python
from fastapi import FastAPI, BackgroundTasks
from analysis_framework.integration_layer.graph_sitter_integration import GraphSitterIntegration

app = FastAPI()
integration = GraphSitterIntegration("postgresql://user:password@localhost/analysis_db")

@app.on_event("startup")
async def startup():
    await integration.initialize()

@app.on_event("shutdown") 
async def shutdown():
    await integration.close()

@app.post("/webhook/repository-updated")
async def repository_updated(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """Handle repository update webhook"""
    
    repo_url = payload.get('repository', {}).get('clone_url')
    branch = payload.get('ref', 'refs/heads/main').split('/')[-1]
    
    if repo_url:
        # Schedule analysis in background
        background_tasks.add_task(
            analyze_repository_background,
            repo_url,
            branch
        )
        
        return {"status": "analysis_scheduled"}
    
    return {"status": "no_action"}

async def analyze_repository_background(repo_url: str, branch: str):
    """Background task for repository analysis"""
    try:
        result = await integration.analyze_repository(
            repo_path_or_url=repo_url,
            branch=branch,
            analysis_types=["CyclomaticComplexity", "SecurityAnalysis"]
        )
        
        # Send notifications if needed
        if any(r.get('grade') == 'F' for r in result['analysis_results'].values()):
            # Send alert for critical issues
            await send_alert(repo_url, result)
            
    except Exception as e:
        print(f"Background analysis failed: {str(e)}")

async def send_alert(repo_url: str, result: dict):
    """Send alert for critical issues"""
    # Implementation depends on your notification system
    print(f"ALERT: Critical issues found in {repo_url}")
```

## Custom Analysis Development

### Creating a New Analysis Type

```python
# analysis_framework/analyzers/custom_analyzer.py

from typing import Dict, Any, List
from uuid import UUID

class CustomAnalyzer:
    """Custom analyzer for specific code patterns"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    async def analyze(self, repository_id: UUID) -> Dict[str, Any]:
        """Perform custom analysis"""
        
        # Get repository data
        async with self.db_manager.get_connection() as conn:
            # Custom analysis logic here
            files = await conn.fetch(
                "SELECT * FROM files WHERE repository_id = $1",
                repository_id
            )
            
            symbols = await conn.fetch(
                """
                SELECT s.* FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.repository_id = $1
                """,
                repository_id
            )
        
        # Perform analysis
        analysis_results = self._perform_custom_analysis(files, symbols)
        
        # Calculate score and grade
        score = self._calculate_score(analysis_results)
        grade = self._calculate_grade(score)
        
        return {
            'analysis_type': 'custom',
            'analysis_subtype': 'pattern_detection',
            'repository_id': str(repository_id),
            'analyzer_name': 'custom_pattern_analyzer',
            'analyzer_version': '1.0.0',
            'results': analysis_results,
            'score': score,
            'grade': grade,
            'confidence_level': 85.0,
            'recommendations': self._generate_recommendations(analysis_results),
            'warnings': self._generate_warnings(analysis_results),
            'metadata': {
                'patterns_analyzed': ['singleton', 'factory', 'observer'],
                'methodology': 'AST pattern matching with heuristics'
            }
        }
    
    def _perform_custom_analysis(self, files: List, symbols: List) -> Dict[str, Any]:
        """Implement custom analysis logic"""
        # Your custom analysis implementation
        return {
            'patterns_found': [],
            'anti_patterns': [],
            'recommendations': []
        }
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Calculate analysis score"""
        # Your scoring logic
        return 85.0
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade"""
        if score >= 90: return 'A'
        elif score >= 80: return 'B'
        elif score >= 70: return 'C'
        elif score >= 60: return 'D'
        else: return 'F'
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations"""
        return []
    
    def _generate_warnings(self, results: Dict[str, Any]) -> List[str]:
        """Generate warnings"""
        return []
```

## Monitoring and Alerting

### Health Check Dashboard

```python
async def create_health_dashboard():
    """Create a health monitoring dashboard"""
    
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    # Get overall system health
    stats = await db_manager.get_database_stats()
    
    # Get recent analysis activity
    recent_analyses = await db_manager.execute_query(
        """
        SELECT 
            analysis_type,
            COUNT(*) as count,
            AVG(score) as avg_score,
            MAX(analysis_date) as last_run
        FROM analysis_results 
        WHERE analysis_date >= NOW() - INTERVAL '7 days'
        GROUP BY analysis_type
        ORDER BY count DESC
        """,
        fetch="all"
    )
    
    # Get failed tasks
    failed_tasks = await db_manager.execute_query(
        """
        SELECT name, error_message, updated_at
        FROM tasks 
        WHERE status = 'failed' 
        AND updated_at >= NOW() - INTERVAL '24 hours'
        ORDER BY updated_at DESC
        """,
        fetch="all"
    )
    
    print("=== Analysis Framework Health Dashboard ===")
    print(f"Database Size: {stats['database_size']}")
    print(f"Total Repositories: {stats['repositories_count']}")
    print(f"Total Analysis Results: {stats['analysis_results_count']}")
    
    print("\n=== Recent Analysis Activity (7 days) ===")
    for analysis in recent_analyses:
        print(f"{analysis['analysis_type']}: {analysis['count']} runs, "
              f"avg score: {analysis['avg_score']:.1f}, "
              f"last run: {analysis['last_run']}")
    
    print(f"\n=== Failed Tasks (24 hours) ===")
    for task in failed_tasks:
        print(f"{task['name']}: {task['error_message']}")
    
    await db_manager.close()

asyncio.run(create_health_dashboard())
```

### Automated Alerting

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def check_and_alert():
    """Check system health and send alerts if needed"""
    
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    alerts = []
    
    # Check for repositories with failing analysis
    failing_repos = await db_manager.execute_query(
        """
        SELECT r.name, r.full_name, r.analysis_status, r.last_analyzed_at
        FROM repositories r
        WHERE r.analysis_status = 'failed'
        AND r.last_analyzed_at >= NOW() - INTERVAL '24 hours'
        """,
        fetch="all"
    )
    
    if failing_repos:
        alerts.append(f"Found {len(failing_repos)} repositories with failed analysis")
    
    # Check for high-severity security issues
    critical_security = await db_manager.execute_query(
        """
        SELECT COUNT(*) as count
        FROM security_analysis
        WHERE severity_level = 'critical'
        AND status = 'open'
        AND analysis_date >= NOW() - INTERVAL '7 days'
        """,
        fetch="val"
    )
    
    if critical_security > 0:
        alerts.append(f"Found {critical_security} critical security issues")
    
    # Check for system performance issues
    slow_analyses = await db_manager.execute_query(
        """
        SELECT COUNT(*) as count
        FROM analysis_results
        WHERE execution_time_ms > 300000  -- 5 minutes
        AND analysis_date >= NOW() - INTERVAL '24 hours'
        """,
        fetch="val"
    )
    
    if slow_analyses > 5:
        alerts.append(f"Found {slow_analyses} slow analysis executions")
    
    # Send alerts if any issues found
    if alerts:
        await send_email_alert(alerts)
    
    await db_manager.close()

async def send_email_alert(alerts: List[str]):
    """Send email alert"""
    
    msg = MIMEMultipart()
    msg['From'] = "analysis-system@company.com"
    msg['To'] = "devops@company.com"
    msg['Subject'] = "Analysis Framework Alert"
    
    body = "The following issues were detected:\n\n"
    body += "\n".join(f"- {alert}" for alert in alerts)
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email (configure SMTP settings)
    # server = smtplib.SMTP('smtp.company.com', 587)
    # server.send_message(msg)
    
    print(f"Alert sent: {body}")

# Schedule this to run periodically
asyncio.run(check_and_alert())
```

## Performance Optimization

### Batch Processing

```python
async def batch_analyze_repositories():
    """Analyze multiple repositories in batch"""
    
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_db"
    )
    
    await integration.initialize()
    
    repositories = [
        "https://github.com/fastapi/fastapi.git",
        "https://github.com/django/django.git", 
        "https://github.com/flask/flask.git"
    ]
    
    # Create analysis tasks
    task_ids = []
    for repo_url in repositories:
        task_id = await integration.create_analysis_task(
            repo_path_or_url=repo_url,
            analysis_types=["CyclomaticComplexity", "MaintainabilityIndex"],
            priority=3
        )
        task_ids.append(task_id)
        print(f"Created task {task_id} for {repo_url}")
    
    # Monitor task completion
    completed_tasks = 0
    while completed_tasks < len(task_ids):
        await asyncio.sleep(60)  # Check every minute
        
        for task_id in task_ids:
            # Check task status (implementation depends on task executor)
            pass
    
    await integration.close()

asyncio.run(batch_analyze_repositories())
```

### Caching and Optimization

```python
import redis
import json
from functools import wraps

# Redis cache for analysis results
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_analysis_result(expiry_seconds=3600):
    """Decorator to cache analysis results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"analysis:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiry_seconds, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

@cache_analysis_result(expiry_seconds=7200)  # Cache for 2 hours
async def get_repository_analysis(repo_id: str):
    """Get cached repository analysis"""
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    await db_manager.initialize()
    
    try:
        results = await db_manager.get_analysis_results(repo_id)
        return results
    finally:
        await db_manager.close()
```

This comprehensive usage guide demonstrates the full capabilities of the Graph-Sitter Codebase Analysis Framework, from basic setup to advanced customization and optimization techniques. The framework provides a robust foundation for building sophisticated code analysis workflows that can scale with your organization's needs.

