"""
Configuration and fixtures for system validation tests.
"""

import pytest
import tempfile
import os
import shutil
import sqlite3
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def test_database():
    """Create a test database for integration tests."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create database schema
    conn = sqlite3.connect(db_path)
    schema_sql = """
    CREATE TABLE IF NOT EXISTS test_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT NOT NULL,
        status TEXT NOT NULL,
        duration REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS test_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_run_id INTEGER,
        metric_name TEXT NOT NULL,
        metric_value REAL,
        FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
    );
    """
    
    for statement in schema_sql.split(';'):
        if statement.strip():
            conn.execute(statement)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture(scope="session")
def test_workspace():
    """Create a temporary workspace for integration tests."""
    workspace_dir = tempfile.mkdtemp(prefix="integration_test_")
    
    # Create workspace structure
    subdirs = [
        "projects",
        "artifacts", 
        "logs",
        "configs",
        "temp"
    ]
    
    for subdir in subdirs:
        os.makedirs(os.path.join(workspace_dir, subdir), exist_ok=True)
    
    yield workspace_dir
    
    # Cleanup
    shutil.rmtree(workspace_dir)


@pytest.fixture
def mock_system_config():
    """Mock system configuration for testing."""
    return {
        "database": {
            "type": "sqlite",
            "connection_string": ":memory:",
            "pool_size": 5
        },
        "external_apis": {
            "linear": {
                "api_key": "test_linear_key",
                "base_url": "https://api.linear.app/graphql"
            },
            "github": {
                "token": "test_github_token",
                "base_url": "https://api.github.com"
            }
        },
        "performance": {
            "max_concurrent_tasks": 10,
            "timeout_seconds": 300,
            "retry_attempts": 3
        },
        "monitoring": {
            "enabled": True,
            "metrics_interval": 60,
            "log_level": "INFO"
        }
    }


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for integration tests."""
    return {
        "response_time_ms": {
            "fast": 100,
            "acceptable": 500,
            "slow": 2000
        },
        "throughput": {
            "min_requests_per_second": 10,
            "target_requests_per_second": 50
        },
        "resource_usage": {
            "max_memory_mb": 512,
            "max_cpu_percent": 80
        },
        "error_rates": {
            "max_error_rate": 0.01,  # 1%
            "max_timeout_rate": 0.005  # 0.5%
        }
    }


@pytest.fixture
def integration_test_data():
    """Test data for integration tests."""
    return {
        "sample_code": {
            "python": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    print(fibonacci(10))

if __name__ == "__main__":
    main()
""",
            "typescript": """
interface User {
    id: number;
    name: string;
    email: string;
}

class UserService {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }
    
    getUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}

export { User, UserService };
""",
            "javascript": """
const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
"""
        },
        "sample_projects": [
            {
                "name": "web-app",
                "language": "typescript",
                "framework": "react",
                "size": "medium"
            },
            {
                "name": "api-service",
                "language": "python",
                "framework": "fastapi",
                "size": "large"
            },
            {
                "name": "mobile-app",
                "language": "dart",
                "framework": "flutter",
                "size": "small"
            }
        ],
        "test_scenarios": [
            {
                "name": "basic_analysis",
                "description": "Basic code analysis scenario",
                "complexity": "low",
                "expected_duration": 30
            },
            {
                "name": "full_generation",
                "description": "Complete code generation workflow",
                "complexity": "high",
                "expected_duration": 300
            },
            {
                "name": "multi_project",
                "description": "Multi-project parallel processing",
                "complexity": "medium",
                "expected_duration": 120
            }
        ]
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for testing."""
    services = {}
    
    # Mock Linear API
    linear_mock = Mock()
    linear_mock.get_issues.return_value = {
        "data": {"issues": {"nodes": []}}
    }
    linear_mock.create_issue.return_value = {
        "data": {"issueCreate": {"issue": {"id": "test_issue"}}}
    }
    services["linear"] = linear_mock
    
    # Mock GitHub API
    github_mock = Mock()
    github_mock.get_repositories.return_value = []
    github_mock.create_pull_request.return_value = {
        "id": 123,
        "number": 456,
        "html_url": "https://github.com/test/repo/pull/456"
    }
    services["github"] = github_mock
    
    # Mock CI/CD Pipeline
    cicd_mock = Mock()
    cicd_mock.trigger_build.return_value = {
        "build_id": "build_123",
        "status": "started"
    }
    cicd_mock.get_build_status.return_value = {
        "status": "success",
        "duration": 120
    }
    services["cicd"] = cicd_mock
    
    return services


@pytest.fixture
def test_metrics_collector():
    """Test metrics collector for performance monitoring."""
    class MetricsCollector:
        def __init__(self):
            self.metrics = {}
        
        def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append({
                "value": value,
                "tags": tags or {},
                "timestamp": time.time()
            })
        
        def get_metric_summary(self, name: str) -> Dict[str, Any]:
            if name not in self.metrics:
                return {}
            
            values = [m["value"] for m in self.metrics[name]]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "total": sum(values)
            }
        
        def get_all_metrics(self) -> Dict[str, Any]:
            return {name: self.get_metric_summary(name) for name in self.metrics.keys()}
    
    return MetricsCollector()


@pytest.fixture
def integration_test_runner():
    """Integration test runner with common utilities."""
    class IntegrationTestRunner:
        def __init__(self):
            self.test_results = []
        
        def run_test_scenario(self, scenario_name: str, test_func, *args, **kwargs):
            """Run a test scenario and collect results."""
            import time
            
            start_time = time.time()
            try:
                result = test_func(*args, **kwargs)
                status = "success"
                error = None
            except Exception as e:
                result = None
                status = "failed"
                error = str(e)
            
            duration = time.time() - start_time
            
            test_result = {
                "scenario": scenario_name,
                "status": status,
                "duration": duration,
                "result": result,
                "error": error,
                "timestamp": start_time
            }
            
            self.test_results.append(test_result)
            return test_result
        
        def get_test_summary(self) -> Dict[str, Any]:
            """Get summary of all test results."""
            total_tests = len(self.test_results)
            successful_tests = len([r for r in self.test_results if r["status"] == "success"])
            failed_tests = total_tests - successful_tests
            
            total_duration = sum(r["duration"] for r in self.test_results)
            avg_duration = total_duration / total_tests if total_tests > 0 else 0
            
            return {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "results": self.test_results
            }
    
    return IntegrationTestRunner()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add integration marker to all tests in this directory
        if "system_validation" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might take longer
        if any(keyword in item.name.lower() for keyword in ["performance", "load", "stress", "end_to_end"]):
            item.add_marker(pytest.mark.slow)
        
        # Add external marker to tests that use external services
        if any(keyword in item.name.lower() for keyword in ["github", "linear", "external", "api"]):
            item.add_marker(pytest.mark.external)


@pytest.fixture(autouse=True)
def setup_test_environment(test_workspace, mock_system_config):
    """Setup test environment for each test."""
    # Set environment variables
    os.environ["TEST_WORKSPACE"] = test_workspace
    os.environ["TEST_MODE"] = "integration"
    
    yield
    
    # Cleanup environment variables
    os.environ.pop("TEST_WORKSPACE", None)
    os.environ.pop("TEST_MODE", None)

