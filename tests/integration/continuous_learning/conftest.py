"""
Pytest configuration and fixtures for continuous learning integration tests.
"""

import asyncio
import pytest
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import tempfile
import os
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_config() -> Dict[str, Any]:
    """Test configuration for integration tests."""
    return {
        "database": {
            "url": "sqlite:///:memory:",
            "pool_size": 5,
            "max_overflow": 10
        },
        "openevolve": {
            "api_url": "http://localhost:8080/api/v1",
            "timeout": 30,
            "max_retries": 3
        },
        "performance": {
            "response_time_p95": 2000,  # milliseconds
            "error_rate": 0.1,  # percentage
            "availability": 99.9,  # percentage
            "mttr": 300  # seconds
        },
        "load_testing": {
            "concurrent_users": 100,  # Reduced for testing
            "ramp_up_duration": 30,
            "steady_state_duration": 60
        }
    }


@pytest.fixture
async def mock_database() -> AsyncGenerator[MagicMock, None]:
    """Mock database connection for testing."""
    db_mock = MagicMock()
    db_mock.execute = AsyncMock()
    db_mock.fetch_all = AsyncMock(return_value=[])
    db_mock.fetch_one = AsyncMock(return_value=None)
    db_mock.transaction = AsyncMock()
    yield db_mock


@pytest.fixture
async def mock_openevolve_client() -> AsyncGenerator[AsyncMock, None]:
    """Mock OpenEvolve client for testing."""
    client_mock = AsyncMock()
    client_mock.submit_evaluation = AsyncMock(return_value={"evaluation_id": "test-123"})
    client_mock.get_evaluation_result = AsyncMock(return_value={
        "status": "completed",
        "score": 0.85,
        "recommendations": ["Optimize query performance", "Add caching layer"]
    })
    client_mock.submit_feedback = AsyncMock(return_value={"feedback_id": "feedback-456"})
    yield client_mock


@pytest.fixture
async def mock_self_healing_system() -> AsyncGenerator[AsyncMock, None]:
    """Mock self-healing system for testing."""
    system_mock = AsyncMock()
    system_mock.detect_error = AsyncMock(return_value={
        "error_id": "error-789",
        "type": "performance_degradation",
        "severity": "medium",
        "detected_at": "2024-01-01T00:00:00Z"
    })
    system_mock.diagnose_error = AsyncMock(return_value={
        "diagnosis": "High memory usage in pattern analysis module",
        "root_cause": "Memory leak in data processing pipeline",
        "confidence": 0.9
    })
    system_mock.attempt_recovery = AsyncMock(return_value={
        "recovery_id": "recovery-101",
        "status": "success",
        "actions_taken": ["Restarted service", "Cleared cache"]
    })
    yield system_mock


@pytest.fixture
async def mock_pattern_analysis_engine() -> AsyncGenerator[AsyncMock, None]:
    """Mock pattern analysis engine for testing."""
    engine_mock = AsyncMock()
    engine_mock.analyze_patterns = AsyncMock(return_value={
        "patterns": [
            {
                "type": "performance_pattern",
                "confidence": 0.92,
                "description": "Query performance degrades during peak hours"
            }
        ],
        "predictions": [
            {
                "metric": "response_time",
                "predicted_value": 1800,
                "confidence": 0.88
            }
        ]
    })
    engine_mock.generate_recommendations = AsyncMock(return_value=[
        {
            "type": "optimization",
            "priority": "high",
            "description": "Add database indexing for frequently queried fields"
        }
    ])
    yield engine_mock


@pytest.fixture
async def test_data_directory() -> AsyncGenerator[Path, None]:
    """Create a temporary directory with test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create sample test data files
        (test_dir / "historical_data.json").write_text('{"events": []}')
        (test_dir / "performance_metrics.json").write_text('{"metrics": []}')
        (test_dir / "error_logs.json").write_text('{"errors": []}')
        
        yield test_dir


@pytest.fixture
async def integration_test_environment(
    test_config,
    mock_database,
    mock_openevolve_client,
    mock_self_healing_system,
    mock_pattern_analysis_engine,
    test_data_directory
) -> Dict[str, Any]:
    """Complete integration test environment setup."""
    return {
        "config": test_config,
        "database": mock_database,
        "openevolve_client": mock_openevolve_client,
        "self_healing_system": mock_self_healing_system,
        "pattern_analysis_engine": mock_pattern_analysis_engine,
        "test_data_dir": test_data_directory
    }


@pytest.fixture
def performance_metrics():
    """Sample performance metrics for testing."""
    return {
        "response_times": [100, 150, 200, 180, 220, 190, 160],
        "error_rates": [0.01, 0.02, 0.015, 0.008, 0.012],
        "throughput": [1000, 1200, 1100, 1300, 1150],
        "cpu_usage": [45.2, 52.1, 48.7, 55.3, 49.8],
        "memory_usage": [68.5, 72.1, 70.3, 75.2, 71.8]
    }


@pytest.fixture
def sample_error_scenarios():
    """Sample error scenarios for testing."""
    return [
        {
            "type": "database_connection_timeout",
            "severity": "high",
            "frequency": "rare",
            "recovery_strategy": "connection_pool_restart"
        },
        {
            "type": "memory_leak",
            "severity": "medium",
            "frequency": "occasional",
            "recovery_strategy": "service_restart"
        },
        {
            "type": "api_rate_limit_exceeded",
            "severity": "low",
            "frequency": "common",
            "recovery_strategy": "backoff_retry"
        }
    ]

