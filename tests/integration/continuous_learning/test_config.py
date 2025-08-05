"""
Test configuration and data models for continuous learning integration tests.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class TestScenario(Enum):
    """Test scenario types."""
    NORMAL_OPERATIONS = "normal_operations"
    HIGH_LOAD = "high_load"
    ERROR_INJECTION = "error_injection"
    COMPONENT_FAILURE = "component_failure"


class ComponentType(Enum):
    """System component types."""
    OPENEVOLVE = "openevolve"
    SELF_HEALING = "self_healing"
    PATTERN_ANALYSIS = "pattern_analysis"
    DATABASE = "database"
    API_GATEWAY = "api_gateway"


@dataclass
class TestConfig:
    """Configuration for integration tests."""
    database_size: str = "test_scale"
    concurrent_users: int = 100
    test_duration: int = 300  # seconds
    data_retention: str = "1_day"
    
    # Performance targets
    response_time_p95: int = 2000  # milliseconds
    error_rate: float = 0.1  # percentage
    availability: float = 99.9  # percentage
    mttr: int = 300  # seconds
    
    # Load testing
    ramp_up_duration: int = 30  # seconds
    steady_state_duration: int = 60  # seconds
    scenarios: List[str] = None
    
    def __post_init__(self):
        if self.scenarios is None:
            self.scenarios = [scenario.value for scenario in TestScenario]


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    throughput: float
    cpu_usage: float
    memory_usage: float
    timestamp: str


@dataclass
class ErrorEvent:
    """Error event data structure."""
    error_id: str
    component: ComponentType
    error_type: str
    severity: str
    message: str
    timestamp: str
    resolved: bool = False
    resolution_time: Optional[int] = None


@dataclass
class LearningEvent:
    """Learning event data structure."""
    event_id: str
    component: ComponentType
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    processed: bool = False


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    status: str  # "passed", "failed", "skipped"
    duration: float
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: str = ""


@dataclass
class IntegrationTestSuite:
    """Integration test suite configuration."""
    name: str
    description: str
    components: List[ComponentType]
    scenarios: List[TestScenario]
    expected_duration: int  # seconds
    success_criteria: Dict[str, Any]


# Predefined test suites
OPENEVOLVE_INTEGRATION_SUITE = IntegrationTestSuite(
    name="OpenEvolve Integration",
    description="Test OpenEvolve evaluation and feedback loops",
    components=[ComponentType.OPENEVOLVE, ComponentType.DATABASE],
    scenarios=[TestScenario.NORMAL_OPERATIONS, TestScenario.ERROR_INJECTION],
    expected_duration=600,
    success_criteria={
        "evaluation_success_rate": 0.95,
        "feedback_loop_latency": 5000,  # milliseconds
        "api_response_time": 2000  # milliseconds
    }
)

SELF_HEALING_SUITE = IntegrationTestSuite(
    name="Self-Healing Workflow",
    description="Test error detection, diagnosis, and recovery",
    components=[ComponentType.SELF_HEALING, ComponentType.DATABASE],
    scenarios=[TestScenario.ERROR_INJECTION, TestScenario.COMPONENT_FAILURE],
    expected_duration=900,
    success_criteria={
        "error_detection_rate": 0.95,
        "recovery_success_rate": 0.70,
        "mttr": 300  # seconds
    }
)

PATTERN_ANALYSIS_SUITE = IntegrationTestSuite(
    name="Pattern Analysis Pipeline",
    description="Test pattern detection and optimization recommendations",
    components=[ComponentType.PATTERN_ANALYSIS, ComponentType.DATABASE],
    scenarios=[TestScenario.NORMAL_OPERATIONS, TestScenario.HIGH_LOAD],
    expected_duration=1200,
    success_criteria={
        "pattern_detection_accuracy": 0.80,
        "recommendation_relevance": 0.85,
        "processing_latency": 10000  # milliseconds
    }
)

CROSS_COMPONENT_SUITE = IntegrationTestSuite(
    name="Cross-Component Integration",
    description="Test data flow and coordination between all components",
    components=[
        ComponentType.OPENEVOLVE,
        ComponentType.SELF_HEALING,
        ComponentType.PATTERN_ANALYSIS,
        ComponentType.DATABASE
    ],
    scenarios=[scenario for scenario in TestScenario],
    expected_duration=1800,
    success_criteria={
        "data_flow_integrity": 0.99,
        "component_coordination": 0.95,
        "end_to_end_latency": 15000  # milliseconds
    }
)

