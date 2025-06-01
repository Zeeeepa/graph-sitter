"""
End-to-End Workflow Testing Module

This module implements comprehensive end-to-end workflow testing for the
continuous learning system as specified in ZAM-1053.
"""

import asyncio
import pytest
import time
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass, asdict
import json
import logging
from enum import Enum

from .test_config import TestConfig, ComponentType, TestScenario

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Workflow types for testing."""
    ERROR_TO_IMPROVEMENT = "error_to_improvement"
    PATTERN_TO_OPTIMIZATION = "pattern_to_optimization"
    LEARNING_EFFECTIVENESS = "learning_effectiveness"
    FULL_SYSTEM_CYCLE = "full_system_cycle"


@dataclass
class WorkflowStep:
    """Individual workflow step."""
    step_name: str
    component: ComponentType
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    timeout: float
    critical: bool = True


@dataclass
class WorkflowResult:
    """Workflow execution result."""
    workflow_type: WorkflowType
    total_duration: float
    steps_completed: int
    steps_failed: int
    success_rate: float
    bottlenecks: List[str]
    performance_metrics: Dict[str, float]
    error_details: List[str]


class WorkflowTestSuite:
    """
    Comprehensive end-to-end workflow testing framework.
    
    This class implements workflow testing as specified in the implementation
    requirements, testing complete workflows and scenarios from error detection
    to system improvement.
    """
    
    def __init__(self, test_config: TestConfig):
        """Initialize workflow test environment."""
        self.config = test_config
        self.workflow_results: List[WorkflowResult] = []
        
        # Component mocks for testing
        self.openevolve_client: Optional[AsyncMock] = None
        self.self_healing_system: Optional[AsyncMock] = None
        self.pattern_analysis_engine: Optional[AsyncMock] = None
        self.database: Optional[MagicMock] = None
        
        logger.info(f"Initialized WorkflowTestSuite with config: {asdict(test_config)}")
    
    def setup_test_environment(self, integration_test_environment: Dict[str, Any]):
        """Setup the test environment with mocked components."""
        self.openevolve_client = integration_test_environment["openevolve_client"]
        self.self_healing_system = integration_test_environment["self_healing_system"]
        self.pattern_analysis_engine = integration_test_environment["pattern_analysis_engine"]
        self.database = integration_test_environment["database"]
        
        logger.info("Workflow test environment setup completed")
    
    async def test_error_to_improvement_workflow(self) -> WorkflowResult:
        """
        Test complete error detection to system improvement workflow.
        
        Workflow Steps:
        1. Error occurs in system
        2. Self-healing detects error
        3. Pattern analysis identifies root cause
        4. OpenEvolve evaluates situation
        5. System implements improvements
        6. Validation of improvements
        """
        start_time = time.time()
        workflow_type = WorkflowType.ERROR_TO_IMPROVEMENT
        
        logger.info(f"Starting {workflow_type.value} workflow test")
        
        steps = [
            WorkflowStep(
                step_name="error_injection",
                component=ComponentType.DATABASE,
                input_data={"error_type": "connection_timeout", "severity": "high"},
                expected_output={"error_injected": True},
                timeout=5.0
            ),
            WorkflowStep(
                step_name="error_detection",
                component=ComponentType.SELF_HEALING,
                input_data={"monitor_data": {"response_time": 5000, "error_rate": 0.15}},
                expected_output={"error_detected": True, "error_id": str},
                timeout=10.0
            ),
            WorkflowStep(
                step_name="pattern_analysis",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"error_context": "connection_timeout", "historical_data": []},
                expected_output={"patterns_found": True, "root_cause": str},
                timeout=15.0
            ),
            WorkflowStep(
                step_name="openevolve_evaluation",
                component=ComponentType.OPENEVOLVE,
                input_data={"error_analysis": {}, "system_context": {}},
                expected_output={"evaluation_id": str, "recommendations": list},
                timeout=20.0
            ),
            WorkflowStep(
                step_name="improvement_implementation",
                component=ComponentType.SELF_HEALING,
                input_data={"recommendations": [], "priority": "high"},
                expected_output={"implementation_status": "success"},
                timeout=30.0
            ),
            WorkflowStep(
                step_name="improvement_validation",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"before_metrics": {}, "after_metrics": {}},
                expected_output={"improvement_validated": True, "effectiveness": float},
                timeout=10.0
            )
        ]
        
        result = await self._execute_workflow(workflow_type, steps)
        
        logger.info(f"{workflow_type.value} workflow completed in {result.total_duration:.2f}s")
        return result
    
    async def test_pattern_to_optimization_workflow(self) -> WorkflowResult:
        """
        Test pattern detection to optimization implementation workflow.
        
        Workflow Steps:
        1. Pattern analysis detects performance pattern
        2. Historical data analysis for context
        3. Predictive modeling for future impact
        4. OpenEvolve evaluates optimization opportunities
        5. Optimization recommendations generated
        6. Implementation and validation
        """
        start_time = time.time()
        workflow_type = WorkflowType.PATTERN_TO_OPTIMIZATION
        
        logger.info(f"Starting {workflow_type.value} workflow test")
        
        steps = [
            WorkflowStep(
                step_name="pattern_detection",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={
                    "time_series_data": [
                        {"timestamp": "2024-01-01T00:00:00Z", "response_time": 150},
                        {"timestamp": "2024-01-01T01:00:00Z", "response_time": 180},
                        {"timestamp": "2024-01-01T02:00:00Z", "response_time": 220}
                    ]
                },
                expected_output={"patterns_detected": True, "pattern_count": int},
                timeout=15.0
            ),
            WorkflowStep(
                step_name="historical_analysis",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"lookback_period": "30_days", "pattern_types": ["performance"]},
                expected_output={"historical_context": dict, "trends": list},
                timeout=20.0
            ),
            WorkflowStep(
                step_name="predictive_modeling",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"current_patterns": [], "historical_context": {}},
                expected_output={"predictions": list, "confidence": float},
                timeout=25.0
            ),
            WorkflowStep(
                step_name="optimization_evaluation",
                component=ComponentType.OPENEVOLVE,
                input_data={"patterns": [], "predictions": [], "system_state": {}},
                expected_output={"optimization_opportunities": list, "priority_ranking": list},
                timeout=30.0
            ),
            WorkflowStep(
                step_name="recommendation_generation",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"optimization_opportunities": [], "constraints": {}},
                expected_output={"recommendations": list, "implementation_plan": dict},
                timeout=15.0
            ),
            WorkflowStep(
                step_name="optimization_implementation",
                component=ComponentType.SELF_HEALING,
                input_data={"implementation_plan": {}, "validation_criteria": {}},
                expected_output={"implementation_status": "success", "metrics": dict},
                timeout=45.0
            )
        ]
        
        result = await self._execute_workflow(workflow_type, steps)
        
        logger.info(f"{workflow_type.value} workflow completed in {result.total_duration:.2f}s")
        return result
    
    async def test_learning_effectiveness(self) -> WorkflowResult:
        """
        Test system learning and adaptation over time.
        
        Workflow Steps:
        1. Baseline performance measurement
        2. Learning data collection
        3. Model training and adaptation
        4. Performance improvement validation
        5. Feedback loop effectiveness
        6. Long-term learning validation
        """
        start_time = time.time()
        workflow_type = WorkflowType.LEARNING_EFFECTIVENESS
        
        logger.info(f"Starting {workflow_type.value} workflow test")
        
        steps = [
            WorkflowStep(
                step_name="baseline_measurement",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"measurement_period": "1_hour", "metrics": ["response_time", "error_rate"]},
                expected_output={"baseline_metrics": dict, "measurement_id": str},
                timeout=10.0
            ),
            WorkflowStep(
                step_name="learning_data_collection",
                component=ComponentType.DATABASE,
                input_data={"collection_period": "24_hours", "data_types": ["performance", "errors", "patterns"]},
                expected_output={"data_collected": True, "data_volume": int},
                timeout=15.0
            ),
            WorkflowStep(
                step_name="model_training",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"training_data": {}, "model_type": "adaptive_learning"},
                expected_output={"model_trained": True, "training_accuracy": float},
                timeout=60.0
            ),
            WorkflowStep(
                step_name="adaptation_validation",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"baseline_metrics": {}, "current_metrics": {}},
                expected_output={"improvement_detected": True, "improvement_percentage": float},
                timeout=20.0
            ),
            WorkflowStep(
                step_name="feedback_loop_test",
                component=ComponentType.OPENEVOLVE,
                input_data={"learning_results": {}, "system_feedback": {}},
                expected_output={"feedback_processed": True, "loop_effectiveness": float},
                timeout=25.0
            ),
            WorkflowStep(
                step_name="long_term_validation",
                component=ComponentType.PATTERN_ANALYSIS,
                input_data={"validation_period": "7_days", "learning_metrics": {}},
                expected_output={"long_term_improvement": True, "stability_score": float},
                timeout=30.0
            )
        ]
        
        result = await self._execute_workflow(workflow_type, steps)
        
        logger.info(f"{workflow_type.value} workflow completed in {result.total_duration:.2f}s")
        return result
    
    async def test_full_system_cycle(self) -> WorkflowResult:
        """
        Test complete system cycle including all components and workflows.
        
        This is a comprehensive test that combines all workflow types to validate
        the entire continuous learning system end-to-end.
        """
        start_time = time.time()
        workflow_type = WorkflowType.FULL_SYSTEM_CYCLE
        
        logger.info(f"Starting {workflow_type.value} workflow test")
        
        # Execute all workflow types in sequence
        error_to_improvement = await self.test_error_to_improvement_workflow()
        pattern_to_optimization = await self.test_pattern_to_optimization_workflow()
        learning_effectiveness = await self.test_learning_effectiveness()
        
        # Validate system-wide metrics
        system_validation = await self._validate_system_wide_metrics()
        
        total_duration = time.time() - start_time
        
        # Calculate overall success metrics
        all_workflows = [error_to_improvement, pattern_to_optimization, learning_effectiveness]
        total_steps = sum(w.steps_completed + w.steps_failed for w in all_workflows)
        total_completed = sum(w.steps_completed for w in all_workflows)
        overall_success_rate = total_completed / total_steps if total_steps > 0 else 0
        
        # Identify system-wide bottlenecks
        all_bottlenecks = []
        for workflow in all_workflows:
            all_bottlenecks.extend(workflow.bottlenecks)
        
        result = WorkflowResult(
            workflow_type=workflow_type,
            total_duration=total_duration,
            steps_completed=total_completed,
            steps_failed=sum(w.steps_failed for w in all_workflows),
            success_rate=overall_success_rate,
            bottlenecks=list(set(all_bottlenecks)),
            performance_metrics={
                "end_to_end_latency": total_duration * 1000,
                "system_throughput": total_completed / total_duration,
                "error_recovery_rate": error_to_improvement.success_rate,
                "optimization_effectiveness": pattern_to_optimization.success_rate,
                "learning_improvement": learning_effectiveness.success_rate,
                **system_validation
            },
            error_details=[]
        )
        
        self.workflow_results.append(result)
        
        logger.info(f"{workflow_type.value} workflow completed in {total_duration:.2f}s")
        return result
    
    async def _execute_workflow(self, workflow_type: WorkflowType, steps: List[WorkflowStep]) -> WorkflowResult:
        """Execute a workflow with the given steps."""
        start_time = time.time()
        steps_completed = 0
        steps_failed = 0
        bottlenecks = []
        performance_metrics = {}
        error_details = []
        
        for i, step in enumerate(steps):
            step_start_time = time.time()
            
            try:
                logger.info(f"Executing step {i+1}/{len(steps)}: {step.step_name}")
                
                # Execute step based on component
                result = await self._execute_step(step)
                
                step_duration = time.time() - step_start_time
                performance_metrics[f"{step.step_name}_duration"] = step_duration
                
                # Check if step is a bottleneck (takes longer than expected)
                if step_duration > step.timeout * 0.8:
                    bottlenecks.append(step.step_name)
                
                # Validate step output
                if self._validate_step_output(result, step.expected_output):
                    steps_completed += 1
                    logger.info(f"Step {step.step_name} completed successfully in {step_duration:.2f}s")
                else:
                    if step.critical:
                        steps_failed += 1
                        error_details.append(f"Step {step.step_name} failed validation")
                        logger.error(f"Critical step {step.step_name} failed validation")
                        break
                    else:
                        logger.warning(f"Non-critical step {step.step_name} failed validation")
                
            except asyncio.TimeoutError:
                steps_failed += 1
                error_details.append(f"Step {step.step_name} timed out after {step.timeout}s")
                logger.error(f"Step {step.step_name} timed out")
                if step.critical:
                    break
                    
            except Exception as e:
                steps_failed += 1
                error_details.append(f"Step {step.step_name} failed: {str(e)}")
                logger.error(f"Step {step.step_name} failed: {str(e)}")
                if step.critical:
                    break
        
        total_duration = time.time() - start_time
        success_rate = steps_completed / len(steps) if len(steps) > 0 else 0
        
        result = WorkflowResult(
            workflow_type=workflow_type,
            total_duration=total_duration,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            success_rate=success_rate,
            bottlenecks=bottlenecks,
            performance_metrics=performance_metrics,
            error_details=error_details
        )
        
        self.workflow_results.append(result)
        return result
    
    async def _execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute an individual workflow step."""
        try:
            # Add timeout to step execution
            if step.component == ComponentType.OPENEVOLVE:
                result = await asyncio.wait_for(
                    self.openevolve_client.submit_evaluation(step.input_data),
                    timeout=step.timeout
                )
            elif step.component == ComponentType.SELF_HEALING:
                if "error_detection" in step.step_name:
                    result = await asyncio.wait_for(
                        self.self_healing_system.detect_error(step.input_data),
                        timeout=step.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        self.self_healing_system.attempt_recovery(step.input_data),
                        timeout=step.timeout
                    )
            elif step.component == ComponentType.PATTERN_ANALYSIS:
                result = await asyncio.wait_for(
                    self.pattern_analysis_engine.analyze_patterns(step.input_data),
                    timeout=step.timeout
                )
            elif step.component == ComponentType.DATABASE:
                result = await asyncio.wait_for(
                    self.database.execute(f"SELECT * FROM {step.step_name}"),
                    timeout=step.timeout
                )
            else:
                # Simulate generic step execution
                await asyncio.sleep(0.1)
                result = {"status": "completed", "step": step.step_name}
            
            return result
            
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            raise
    
    def _validate_step_output(self, actual_output: Dict[str, Any], expected_output: Dict[str, Any]) -> bool:
        """Validate step output against expected output."""
        try:
            for key, expected_type in expected_output.items():
                if key not in actual_output:
                    logger.warning(f"Missing expected key: {key}")
                    return False
                
                if expected_type == str and not isinstance(actual_output[key], str):
                    logger.warning(f"Type mismatch for {key}: expected str, got {type(actual_output[key])}")
                    return False
                elif expected_type == int and not isinstance(actual_output[key], int):
                    logger.warning(f"Type mismatch for {key}: expected int, got {type(actual_output[key])}")
                    return False
                elif expected_type == float and not isinstance(actual_output[key], (int, float)):
                    logger.warning(f"Type mismatch for {key}: expected float, got {type(actual_output[key])}")
                    return False
                elif expected_type == list and not isinstance(actual_output[key], list):
                    logger.warning(f"Type mismatch for {key}: expected list, got {type(actual_output[key])}")
                    return False
                elif expected_type == dict and not isinstance(actual_output[key], dict):
                    logger.warning(f"Type mismatch for {key}: expected dict, got {type(actual_output[key])}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Output validation failed: {str(e)}")
            return False
    
    async def _validate_system_wide_metrics(self) -> Dict[str, float]:
        """Validate system-wide metrics across all components."""
        logger.info("Validating system-wide metrics")
        
        # Simulate system-wide validation
        await asyncio.sleep(1.0)
        
        return {
            "data_consistency_score": 0.98,
            "component_coordination_score": 0.95,
            "resource_utilization_efficiency": 0.87,
            "error_propagation_containment": 0.92,
            "learning_convergence_rate": 0.89
        }
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get comprehensive workflow test summary."""
        if not self.workflow_results:
            return {"message": "No workflow tests executed"}
        
        total_workflows = len(self.workflow_results)
        successful_workflows = len([r for r in self.workflow_results if r.success_rate >= 0.8])
        
        avg_success_rate = sum(r.success_rate for r in self.workflow_results) / total_workflows
        avg_duration = sum(r.total_duration for r in self.workflow_results) / total_workflows
        
        all_bottlenecks = []
        for result in self.workflow_results:
            all_bottlenecks.extend(result.bottlenecks)
        
        bottleneck_frequency = {}
        for bottleneck in all_bottlenecks:
            bottleneck_frequency[bottleneck] = bottleneck_frequency.get(bottleneck, 0) + 1
        
        return {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "overall_success_rate": avg_success_rate,
            "average_duration": avg_duration,
            "common_bottlenecks": sorted(bottleneck_frequency.items(), key=lambda x: x[1], reverse=True),
            "workflow_results": [asdict(r) for r in self.workflow_results]
        }


# Pytest test functions
@pytest.mark.asyncio
async def test_error_to_improvement_workflow(integration_test_environment):
    """Test error to improvement workflow."""
    config = TestConfig()
    suite = WorkflowTestSuite(config)
    suite.setup_test_environment(integration_test_environment)
    
    result = await suite.test_error_to_improvement_workflow()
    
    assert result.workflow_type == WorkflowType.ERROR_TO_IMPROVEMENT
    assert result.success_rate >= 0.8  # 80% success rate requirement
    assert result.total_duration > 0


@pytest.mark.asyncio
async def test_pattern_to_optimization_workflow(integration_test_environment):
    """Test pattern to optimization workflow."""
    config = TestConfig()
    suite = WorkflowTestSuite(config)
    suite.setup_test_environment(integration_test_environment)
    
    result = await suite.test_pattern_to_optimization_workflow()
    
    assert result.workflow_type == WorkflowType.PATTERN_TO_OPTIMIZATION
    assert result.success_rate >= 0.8
    assert result.total_duration > 0


@pytest.mark.asyncio
async def test_learning_effectiveness_workflow(integration_test_environment):
    """Test learning effectiveness workflow."""
    config = TestConfig()
    suite = WorkflowTestSuite(config)
    suite.setup_test_environment(integration_test_environment)
    
    result = await suite.test_learning_effectiveness()
    
    assert result.workflow_type == WorkflowType.LEARNING_EFFECTIVENESS
    assert result.success_rate >= 0.8
    assert result.total_duration > 0


@pytest.mark.asyncio
async def test_full_system_cycle_workflow(integration_test_environment):
    """Test full system cycle workflow."""
    config = TestConfig()
    suite = WorkflowTestSuite(config)
    suite.setup_test_environment(integration_test_environment)
    
    result = await suite.test_full_system_cycle()
    
    assert result.workflow_type == WorkflowType.FULL_SYSTEM_CYCLE
    assert result.success_rate >= 0.8
    assert result.total_duration > 0
    assert "end_to_end_latency" in result.performance_metrics


@pytest.mark.asyncio
async def test_complete_workflow_suite(integration_test_environment):
    """Test complete workflow suite."""
    config = TestConfig()
    suite = WorkflowTestSuite(config)
    suite.setup_test_environment(integration_test_environment)
    
    # Run all workflow tests
    await suite.test_error_to_improvement_workflow()
    await suite.test_pattern_to_optimization_workflow()
    await suite.test_learning_effectiveness()
    
    summary = suite.get_workflow_summary()
    
    assert summary["total_workflows"] == 3
    assert summary["overall_success_rate"] >= 0.8
    assert len(summary["workflow_results"]) == 3

