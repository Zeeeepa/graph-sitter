# OpenEvolve-Graph-Sitter Integration API Specification

## Overview

This document provides detailed API specifications for the integrated OpenEvolve-Graph-Sitter system. The API enables seamless interaction between evolutionary code optimization and advanced code analysis capabilities.

## Base Configuration

- **Base URL**: `https://api.graph-sitter.com/v1`
- **Authentication**: Bearer token
- **Content-Type**: `application/json`
- **Rate Limiting**: 1000 requests/hour per API key

## Authentication

All API requests require authentication using a Bearer token:

```http
Authorization: Bearer <your-api-token>
```

## Core APIs

### 1. Task Management API

#### Create Optimization Task

**Endpoint**: `POST /tasks`

**Description**: Creates a new code optimization task using evolutionary algorithms.

**Request Body**:
```json
{
  "task_definition": {
    "type": "code_optimization",
    "name": "Optimize Database Queries",
    "description": "Improve performance of database query functions",
    "repository": {
      "url": "https://github.com/user/repo",
      "branch": "main",
      "commit": "abc123"
    },
    "target_files": [
      "src/database/queries.py",
      "src/database/models.py"
    ],
    "constraints": {
      "max_iterations": 1000,
      "time_limit_minutes": 60,
      "preserve_functionality": true,
      "maintain_api_compatibility": true
    }
  },
  "evaluation_criteria": {
    "performance_weight": 0.4,
    "maintainability_weight": 0.3,
    "correctness_weight": 0.3
  },
  "optimization_config": {
    "population_size": 500,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8,
    "selection_pressure": 0.7
  }
}
```

**Response**:
```json
{
  "task_id": "task_123456",
  "status": "created",
  "created_at": "2024-01-15T14:30:00Z",
  "estimated_completion": "2024-01-15T15:30:00Z",
  "resource_allocation": {
    "cpu_cores": 8,
    "memory_gb": 16,
    "gpu_enabled": true
  }
}
```

#### Get Task Status

**Endpoint**: `GET /tasks/{task_id}`

**Response**:
```json
{
  "task_id": "task_123456",
  "status": "running",
  "progress": {
    "current_iteration": 245,
    "max_iterations": 1000,
    "completion_percentage": 24.5,
    "elapsed_time_minutes": 15.2,
    "estimated_remaining_minutes": 45.8
  },
  "metrics": {
    "best_score": 0.87,
    "average_score": 0.72,
    "improvement_trend": "increasing",
    "convergence_rate": 0.05
  },
  "current_best": {
    "program_id": "prog_789",
    "generation": 12,
    "fitness_scores": {
      "performance": 0.92,
      "maintainability": 0.85,
      "correctness": 0.95
    },
    "code_preview": "def optimized_query(...):\n    # Optimized implementation\n    ..."
  },
  "resource_usage": {
    "cpu_utilization": 0.85,
    "memory_usage_gb": 12.4,
    "gpu_utilization": 0.67
  }
}
```

#### List Tasks

**Endpoint**: `GET /tasks`

**Query Parameters**:
- `status`: Filter by status (created, running, completed, failed)
- `repository`: Filter by repository URL
- `limit`: Number of results (default: 50, max: 200)
- `offset`: Pagination offset

**Response**:
```json
{
  "tasks": [
    {
      "task_id": "task_123456",
      "name": "Optimize Database Queries",
      "status": "running",
      "created_at": "2024-01-15T14:30:00Z",
      "progress": 24.5,
      "repository": "https://github.com/user/repo"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### 2. Evaluation API

#### Evaluate Program

**Endpoint**: `POST /evaluate`

**Description**: Evaluates a code program using both OpenEvolve and Graph-Sitter analysis.

**Request Body**:
```json
{
  "program": {
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "language": "python",
    "entry_point": "fibonacci",
    "test_cases": [
      {"input": [5], "expected_output": 5},
      {"input": [10], "expected_output": 55}
    ]
  },
  "evaluation_context": {
    "task_type": "algorithm_optimization",
    "repository": "https://github.com/user/repo",
    "file_path": "src/algorithms/fibonacci.py",
    "dependencies": ["math", "typing"]
  },
  "evaluation_options": {
    "include_semantic_analysis": true,
    "include_performance_metrics": true,
    "include_complexity_analysis": true,
    "cascade_evaluation": true,
    "timeout_seconds": 30
  }
}
```

**Response**:
```json
{
  "evaluation_id": "eval_456789",
  "program_id": "prog_789",
  "status": "completed",
  "metrics": {
    "functional_correctness": 1.0,
    "performance_score": 0.45,
    "time_complexity": "O(2^n)",
    "space_complexity": "O(n)",
    "maintainability": 0.78,
    "readability": 0.85,
    "semantic_correctness": 0.95
  },
  "analysis": {
    "complexity_metrics": {
      "cyclomatic_complexity": 3,
      "cognitive_complexity": 4,
      "halstead_volume": 45.6,
      "lines_of_code": 4,
      "maintainability_index": 78.2
    },
    "performance_metrics": {
      "execution_time_ms": 1250.5,
      "memory_usage_mb": 2.4,
      "cpu_cycles": 2500000,
      "cache_misses": 150
    },
    "semantic_analysis": {
      "function_count": 1,
      "recursive_calls": 2,
      "variable_usage": {
        "n": {"reads": 3, "writes": 0}
      },
      "type_annotations": 0.0
    },
    "dependency_analysis": {
      "imports": [],
      "exports": ["fibonacci"],
      "internal_dependencies": [],
      "external_dependencies": []
    }
  },
  "recommendations": [
    {
      "type": "performance_optimization",
      "description": "Consider using memoization to improve time complexity",
      "severity": "high",
      "estimated_improvement": 0.8,
      "code_suggestion": "from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef fibonacci(n):\n    ..."
    },
    {
      "type": "code_quality",
      "description": "Add type annotations for better code clarity",
      "severity": "medium",
      "code_suggestion": "def fibonacci(n: int) -> int:"
    }
  ],
  "evaluation_time_ms": 234.5
}
```

#### Batch Evaluation

**Endpoint**: `POST /evaluate/batch`

**Description**: Evaluates multiple programs in parallel.

**Request Body**:
```json
{
  "programs": [
    {
      "program_id": "prog_1",
      "code": "...",
      "language": "python"
    },
    {
      "program_id": "prog_2", 
      "code": "...",
      "language": "python"
    }
  ],
  "evaluation_options": {
    "parallel_evaluations": 4,
    "timeout_seconds": 30
  }
}
```

**Response**:
```json
{
  "batch_id": "batch_123",
  "status": "completed",
  "results": [
    {
      "program_id": "prog_1",
      "status": "completed",
      "metrics": {...},
      "analysis": {...}
    },
    {
      "program_id": "prog_2",
      "status": "failed",
      "error": {
        "code": "TIMEOUT",
        "message": "Evaluation exceeded time limit"
      }
    }
  ],
  "summary": {
    "total_programs": 2,
    "successful_evaluations": 1,
    "failed_evaluations": 1,
    "total_time_ms": 1500.2
  }
}
```

### 3. Code Analysis API

#### Analyze Code Structure

**Endpoint**: `POST /analyze`

**Description**: Performs comprehensive code analysis using Graph-Sitter.

**Request Body**:
```json
{
  "code": "class DatabaseManager:\n    def __init__(self, connection_string):\n        self.connection = connect(connection_string)\n    \n    def execute_query(self, query, params=None):\n        return self.connection.execute(query, params)",
  "language": "python",
  "analysis_types": [
    "complexity",
    "dependencies", 
    "semantic",
    "security",
    "performance"
  ],
  "context": {
    "repository": "https://github.com/user/repo",
    "file_path": "src/database/manager.py",
    "project_type": "web_application"
  }
}
```

**Response**:
```json
{
  "analysis_id": "analysis_789",
  "status": "completed",
  "results": {
    "complexity": {
      "cyclomatic_complexity": 5,
      "cognitive_complexity": 7,
      "nesting_depth": 2,
      "halstead_metrics": {
        "volume": 156.3,
        "difficulty": 8.5,
        "effort": 1328.6
      },
      "maintainability_index": 82.4
    },
    "dependencies": {
      "imports": [
        {
          "module": "connect",
          "type": "function",
          "source": "unknown"
        }
      ],
      "exports": [
        {
          "name": "DatabaseManager",
          "type": "class",
          "public": true
        }
      ],
      "internal_dependencies": [],
      "external_dependencies": ["connect"],
      "dependency_graph": {
        "nodes": ["DatabaseManager", "connect"],
        "edges": [["DatabaseManager", "connect"]]
      }
    },
    "semantic": {
      "classes": [
        {
          "name": "DatabaseManager",
          "methods": ["__init__", "execute_query"],
          "attributes": ["connection"],
          "inheritance": [],
          "complexity": 5
        }
      ],
      "functions": [
        {
          "name": "__init__",
          "parameters": ["self", "connection_string"],
          "return_type": "None",
          "complexity": 1
        },
        {
          "name": "execute_query",
          "parameters": ["self", "query", "params"],
          "return_type": "unknown",
          "complexity": 2
        }
      ],
      "variables": [
        {
          "name": "connection_string",
          "scope": "parameter",
          "type": "unknown"
        },
        {
          "name": "connection",
          "scope": "instance",
          "type": "unknown"
        }
      ]
    },
    "security": {
      "vulnerabilities": [
        {
          "type": "sql_injection",
          "severity": "high",
          "location": {"line": 6, "column": 32},
          "description": "Potential SQL injection vulnerability in execute_query method",
          "recommendation": "Use parameterized queries or ORM"
        }
      ],
      "security_score": 0.6
    },
    "performance": {
      "potential_issues": [
        {
          "type": "resource_leak",
          "severity": "medium",
          "location": {"line": 3, "column": 25},
          "description": "Database connection not properly closed",
          "recommendation": "Implement context manager or explicit close method"
        }
      ],
      "performance_score": 0.7
    }
  },
  "recommendations": [
    {
      "category": "security",
      "priority": "high",
      "description": "Implement parameterized queries to prevent SQL injection",
      "code_example": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    },
    {
      "category": "performance",
      "priority": "medium", 
      "description": "Add connection pooling for better resource management",
      "code_example": "from sqlalchemy import create_engine\nengine = create_engine(connection_string, pool_size=10)"
    }
  ],
  "analysis_time_ms": 145.7
}
```

### 4. Evolution API

#### Start Evolution Process

**Endpoint**: `POST /evolution/start`

**Description**: Starts an evolutionary optimization process for code improvement.

**Request Body**:
```json
{
  "initial_program": {
    "code": "def sort_array(arr):\n    return sorted(arr)",
    "language": "python"
  },
  "evolution_config": {
    "population_size": 100,
    "max_generations": 50,
    "mutation_rate": 0.1,
    "crossover_rate": 0.8,
    "selection_method": "tournament",
    "fitness_function": "performance_and_correctness"
  },
  "constraints": {
    "preserve_functionality": true,
    "max_code_length": 1000,
    "allowed_libraries": ["numpy", "pandas"],
    "performance_target": 0.9
  },
  "evaluation_criteria": {
    "correctness_weight": 0.5,
    "performance_weight": 0.3,
    "maintainability_weight": 0.2
  }
}
```

**Response**:
```json
{
  "evolution_id": "evo_456",
  "status": "started",
  "initial_population": {
    "size": 100,
    "diversity_score": 0.85,
    "average_fitness": 0.45
  },
  "estimated_completion": "2024-01-15T15:45:00Z"
}
```

#### Get Evolution Status

**Endpoint**: `GET /evolution/{evolution_id}`

**Response**:
```json
{
  "evolution_id": "evo_456",
  "status": "running",
  "progress": {
    "current_generation": 23,
    "max_generations": 50,
    "completion_percentage": 46.0
  },
  "population_stats": {
    "size": 100,
    "best_fitness": 0.92,
    "average_fitness": 0.78,
    "diversity_score": 0.67,
    "convergence_rate": 0.03
  },
  "best_individual": {
    "program_id": "prog_best_123",
    "generation": 23,
    "fitness": 0.92,
    "metrics": {
      "correctness": 1.0,
      "performance": 0.89,
      "maintainability": 0.87
    },
    "code_preview": "def sort_array(arr):\n    # Optimized implementation\n    ..."
  },
  "evolution_history": [
    {
      "generation": 1,
      "best_fitness": 0.45,
      "average_fitness": 0.32
    },
    {
      "generation": 23,
      "best_fitness": 0.92,
      "average_fitness": 0.78
    }
  ]
}
```

### 5. Repository Integration API

#### Analyze Repository

**Endpoint**: `POST /repository/analyze`

**Description**: Analyzes an entire repository for optimization opportunities.

**Request Body**:
```json
{
  "repository": {
    "url": "https://github.com/user/repo",
    "branch": "main",
    "access_token": "github_token_123"
  },
  "analysis_scope": {
    "include_patterns": ["*.py", "*.js", "*.ts"],
    "exclude_patterns": ["*test*", "*__pycache__*"],
    "max_files": 1000
  },
  "analysis_types": [
    "complexity",
    "performance",
    "security",
    "maintainability"
  ]
}
```

**Response**:
```json
{
  "analysis_id": "repo_analysis_789",
  "repository": "https://github.com/user/repo",
  "status": "completed",
  "summary": {
    "total_files": 245,
    "analyzed_files": 198,
    "lines_of_code": 15420,
    "average_complexity": 6.8,
    "overall_quality_score": 0.76
  },
  "findings": {
    "high_priority_issues": 12,
    "medium_priority_issues": 34,
    "low_priority_issues": 67,
    "optimization_opportunities": 23
  },
  "file_analysis": [
    {
      "file_path": "src/main.py",
      "complexity_score": 8.5,
      "quality_score": 0.72,
      "issues": [
        {
          "type": "complexity",
          "severity": "high",
          "line": 45,
          "description": "Function exceeds complexity threshold"
        }
      ],
      "optimization_potential": 0.85
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "performance",
      "description": "Optimize database queries in user service",
      "affected_files": ["src/services/user_service.py"],
      "estimated_improvement": 0.4
    }
  ]
}
```

## WebSocket APIs

### Real-time Task Updates

**Endpoint**: `wss://api.graph-sitter.com/v1/ws/tasks/{task_id}`

**Connection**: WebSocket connection for real-time task progress updates.

**Message Format**:
```json
{
  "type": "progress_update",
  "task_id": "task_123456",
  "timestamp": "2024-01-15T14:35:00Z",
  "data": {
    "current_iteration": 250,
    "best_score": 0.88,
    "improvement": 0.01,
    "estimated_remaining_minutes": 42.3
  }
}
```

**Event Types**:
- `progress_update`: Regular progress updates
- `best_solution_found`: New best solution discovered
- `task_completed`: Task finished successfully
- `task_failed`: Task encountered an error
- `resource_warning`: Resource usage approaching limits

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error context",
      "suggestion": "Recommended action"
    },
    "timestamp": "2024-01-15T14:30:00Z",
    "request_id": "req_123456",
    "documentation_url": "https://docs.graph-sitter.com/errors/ERROR_CODE"
  }
}
```

### Error Codes

#### Authentication Errors (4xx)
- `INVALID_TOKEN`: Authentication token is invalid or expired
- `INSUFFICIENT_PERMISSIONS`: Token lacks required permissions
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded

#### Request Errors (4xx)
- `INVALID_REQUEST`: Request format is invalid
- `MISSING_REQUIRED_FIELD`: Required field is missing
- `INVALID_FIELD_VALUE`: Field value is invalid
- `RESOURCE_NOT_FOUND`: Requested resource does not exist

#### Processing Errors (5xx)
- `EVALUATION_FAILED`: Program evaluation encountered an error
- `TIMEOUT`: Operation exceeded time limit
- `RESOURCE_LIMIT_EXCEEDED`: System resource limits exceeded
- `INTERNAL_ERROR`: Unexpected internal error

#### Domain-Specific Errors
- `INVALID_CODE`: Provided code is syntactically invalid
- `COMPILATION_ERROR`: Code compilation failed
- `DEPENDENCY_ERROR`: Required dependencies not available
- `EVOLUTION_CONVERGENCE_FAILED`: Evolution process failed to converge

## Rate Limiting

### Limits by Endpoint Category

- **Task Management**: 100 requests/hour
- **Evaluation**: 1000 requests/hour  
- **Analysis**: 500 requests/hour
- **Evolution**: 50 requests/hour
- **Repository**: 20 requests/hour

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
X-RateLimit-Window: 3600
```

## SDK Examples

### Python SDK

```python
from graph_sitter_client import GraphSitterClient

# Initialize client
client = GraphSitterClient(api_token="your_token_here")

# Create optimization task
task = client.tasks.create({
    "task_definition": {
        "type": "code_optimization",
        "repository": {"url": "https://github.com/user/repo"},
        "target_files": ["src/main.py"]
    }
})

# Monitor progress
for update in client.tasks.stream_progress(task.id):
    print(f"Progress: {update.completion_percentage}%")
    if update.status == "completed":
        break

# Get results
result = client.tasks.get_result(task.id)
print(f"Best solution score: {result.best_score}")
```

### JavaScript SDK

```javascript
import { GraphSitterClient } from '@graph-sitter/client';

const client = new GraphSitterClient({ apiToken: 'your_token_here' });

// Evaluate code
const evaluation = await client.evaluate({
  program: {
    code: 'def fibonacci(n): ...',
    language: 'python'
  },
  evaluation_options: {
    include_semantic_analysis: true
  }
});

console.log('Performance score:', evaluation.metrics.performance_score);
```

## Versioning

The API uses semantic versioning with the version specified in the URL path:
- Current version: `v1`
- Backward compatibility maintained within major versions
- Deprecation notices provided 6 months before breaking changes

## Support

- **Documentation**: https://docs.graph-sitter.com/api
- **Status Page**: https://status.graph-sitter.com
- **Support Email**: api-support@graph-sitter.com
- **Community Forum**: https://community.graph-sitter.com

