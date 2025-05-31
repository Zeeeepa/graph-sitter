"""
End-to-End Workflow Testing Suite

Tests complete development lifecycle automation, multi-project parallel processing,
cross-component communication, and data flow validation.
"""

import pytest
import asyncio
import time
import tempfile
import os
import json
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestEndToEndWorkflows:
    """Test suite for end-to-end workflow validation."""

    @pytest.fixture
    def mock_complete_system(self):
        """Mock complete system components for E2E testing."""
        system = Mock()
        
        # Mock graph_sitter components
        system.codebase_analyzer = Mock()
        system.codebase_analyzer.analyze.return_value = {
            "files": 150,
            "lines_of_code": 15000,
            "complexity_score": 7.5,
            "dependencies": ["numpy", "pandas", "requests"],
            "issues": [
                {"type": "code_smell", "severity": "medium", "file": "main.py", "line": 42},
                {"type": "security", "severity": "high", "file": "auth.py", "line": 15}
            ]
        }
        
        # Mock codegen components
        system.agent_orchestrator = Mock()
        system.agent_orchestrator.execute_task.return_value = {
            "status": "completed",
            "task_id": "task_123",
            "result": {
                "code_generated": True,
                "files_modified": ["main.py", "utils.py"],
                "tests_created": ["test_main.py", "test_utils.py"]
            }
        }
        
        # Mock external integrations
        system.linear_client = Mock()
        system.github_client = Mock()
        system.ci_pipeline = Mock()
        
        return system

    @pytest.fixture
    def sample_project_structure(self):
        """Create sample project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_files = {
                "src/main.py": "def main():\n    print('Hello World')\n",
                "src/utils.py": "def helper():\n    return True\n",
                "tests/test_main.py": "def test_main():\n    assert True\n",
                "requirements.txt": "requests==2.28.0\nnumpy==1.21.0\n",
                "README.md": "# Test Project\n\nThis is a test project.\n",
                ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            }
            
            for file_path, content in project_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            yield temp_dir

    def test_complete_development_lifecycle(self, mock_complete_system, sample_project_structure):
        """Test complete development lifecycle automation."""
        from graph_sitter.workflows import DevelopmentLifecycleOrchestrator
        
        orchestrator = DevelopmentLifecycleOrchestrator(
            system=mock_complete_system,
            project_path=sample_project_structure
        )
        
        # Test full lifecycle execution
        lifecycle_result = orchestrator.execute_full_lifecycle(
            requirements="Add user authentication feature",
            target_branch="feature/auth",
            deployment_env="staging"
        )
        
        # Verify lifecycle stages
        assert lifecycle_result["status"] == "success"
        assert "stages_completed" in lifecycle_result
        
        expected_stages = [
            "requirements_analysis",
            "code_analysis", 
            "task_planning",
            "code_generation",
            "testing",
            "code_review",
            "integration",
            "deployment"
        ]
        
        completed_stages = [stage["name"] for stage in lifecycle_result["stages_completed"]]
        for stage in expected_stages:
            assert stage in completed_stages
        
        # Verify each stage output
        for stage in lifecycle_result["stages_completed"]:
            assert stage["status"] == "success"
            assert "duration" in stage
            assert "output" in stage

    def test_multi_project_parallel_processing(self, mock_complete_system):
        """Test parallel processing across multiple projects."""
        from graph_sitter.workflows import MultiProjectOrchestrator
        
        orchestrator = MultiProjectOrchestrator(system=mock_complete_system)
        
        # Define multiple projects
        projects = [
            {
                "id": "project_1",
                "name": "Frontend App",
                "repo_url": "https://github.com/org/frontend",
                "language": "typescript",
                "priority": "high"
            },
            {
                "id": "project_2", 
                "name": "Backend API",
                "repo_url": "https://github.com/org/backend",
                "language": "python",
                "priority": "medium"
            },
            {
                "id": "project_3",
                "name": "Mobile App",
                "repo_url": "https://github.com/org/mobile",
                "language": "dart",
                "priority": "low"
            }
        ]
        
        # Test parallel execution
        start_time = time.time()
        results = orchestrator.process_projects_parallel(
            projects=projects,
            task_type="security_audit",
            max_workers=3
        )
        execution_time = time.time() - start_time
        
        # Verify results
        assert len(results) == 3
        assert execution_time < 30.0  # Should complete within 30 seconds
        
        for project_id, result in results.items():
            assert result["status"] in ["success", "completed"]
            assert "project_id" in result
            assert "execution_time" in result
        
        # Verify parallel execution was actually faster than sequential
        sequential_time_estimate = sum(r["execution_time"] for r in results.values())
        assert execution_time < sequential_time_estimate * 0.8  # At least 20% faster

    def test_cross_component_communication(self, mock_complete_system):
        """Test communication between different system components."""
        from graph_sitter.workflows import ComponentCommunicationTester
        
        tester = ComponentCommunicationTester(system=mock_complete_system)
        
        # Test message passing between components
        communication_flow = [
            {
                "from": "codebase_analyzer",
                "to": "agent_orchestrator", 
                "message_type": "analysis_complete",
                "payload": {"analysis_id": "analysis_123", "issues_found": 5}
            },
            {
                "from": "agent_orchestrator",
                "to": "ci_pipeline",
                "message_type": "code_ready",
                "payload": {"branch": "feature/test", "commit_sha": "abc123"}
            },
            {
                "from": "ci_pipeline",
                "to": "linear_client",
                "message_type": "deployment_complete",
                "payload": {"environment": "staging", "status": "success"}
            }
        ]
        
        # Test communication flow
        flow_result = tester.test_communication_flow(communication_flow)
        
        assert flow_result["status"] == "success"
        assert flow_result["messages_sent"] == 3
        assert flow_result["messages_received"] == 3
        assert flow_result["communication_latency"] < 1.0  # Under 1 second
        
        # Test error handling in communication
        error_scenario = {
            "from": "codebase_analyzer",
            "to": "nonexistent_component",
            "message_type": "test",
            "payload": {}
        }
        
        error_result = tester.test_error_communication(error_scenario)
        assert error_result["status"] == "error"
        assert "error_message" in error_result

    def test_data_flow_validation(self, mock_complete_system, sample_project_structure):
        """Test data flow validation across the system."""
        from graph_sitter.workflows import DataFlowValidator
        
        validator = DataFlowValidator(
            system=mock_complete_system,
            project_path=sample_project_structure
        )
        
        # Test data flow through analysis pipeline
        analysis_flow = validator.trace_analysis_data_flow(
            input_data={"project_path": sample_project_structure},
            expected_outputs=["file_analysis", "dependency_graph", "metrics"]
        )
        
        assert analysis_flow["status"] == "valid"
        assert "data_transformations" in analysis_flow
        assert len(analysis_flow["data_transformations"]) > 0
        
        # Verify data integrity at each step
        for transformation in analysis_flow["data_transformations"]:
            assert transformation["input_valid"] is True
            assert transformation["output_valid"] is True
            assert transformation["data_loss"] == 0
        
        # Test data flow through generation pipeline
        generation_flow = validator.trace_generation_data_flow(
            input_data={"requirements": "Add logging", "context": "python"},
            expected_outputs=["generated_code", "test_files", "documentation"]
        )
        
        assert generation_flow["status"] == "valid"
        assert "code_quality_score" in generation_flow
        assert generation_flow["code_quality_score"] > 0.7

    def test_workflow_state_management(self, mock_complete_system):
        """Test workflow state management and persistence."""
        from graph_sitter.workflows import WorkflowStateManager
        
        state_manager = WorkflowStateManager(system=mock_complete_system)
        
        # Test workflow state creation
        workflow_id = state_manager.create_workflow(
            type="feature_development",
            parameters={"feature": "user_auth", "priority": "high"}
        )
        
        assert workflow_id is not None
        
        # Test state updates
        state_manager.update_workflow_state(
            workflow_id=workflow_id,
            stage="code_generation",
            status="in_progress",
            progress=0.3
        )
        
        # Test state retrieval
        current_state = state_manager.get_workflow_state(workflow_id)
        
        assert current_state["stage"] == "code_generation"
        assert current_state["status"] == "in_progress"
        assert current_state["progress"] == 0.3
        
        # Test state persistence
        state_manager.persist_workflow_state(workflow_id)
        
        # Test state recovery
        recovered_state = state_manager.recover_workflow_state(workflow_id)
        assert recovered_state == current_state

    def test_workflow_error_recovery(self, mock_complete_system):
        """Test workflow error recovery mechanisms."""
        from graph_sitter.workflows import WorkflowErrorRecovery
        
        recovery_system = WorkflowErrorRecovery(system=mock_complete_system)
        
        # Simulate workflow failure
        failure_context = {
            "workflow_id": "workflow_123",
            "failed_stage": "code_generation",
            "error_type": "timeout",
            "error_message": "Code generation timed out after 300 seconds",
            "retry_count": 0,
            "max_retries": 3
        }
        
        # Test recovery strategy selection
        recovery_strategy = recovery_system.select_recovery_strategy(failure_context)
        assert recovery_strategy in ["retry", "skip", "rollback", "manual_intervention"]
        
        # Test recovery execution
        recovery_result = recovery_system.execute_recovery(
            strategy=recovery_strategy,
            context=failure_context
        )
        
        assert recovery_result["status"] in ["success", "failed", "partial"]
        assert "recovery_actions" in recovery_result
        assert "estimated_recovery_time" in recovery_result

    def test_workflow_performance_optimization(self, mock_complete_system):
        """Test workflow performance optimization."""
        from graph_sitter.workflows import WorkflowOptimizer
        
        optimizer = WorkflowOptimizer(system=mock_complete_system)
        
        # Test workflow analysis
        workflow_metrics = {
            "total_execution_time": 1800,  # 30 minutes
            "stage_times": {
                "analysis": 300,
                "generation": 900,
                "testing": 400,
                "deployment": 200
            },
            "resource_usage": {
                "cpu_peak": 0.8,
                "memory_peak": 0.6,
                "disk_io": 0.4
            }
        }
        
        # Test optimization recommendations
        optimizations = optimizer.analyze_and_recommend(workflow_metrics)
        
        assert "recommendations" in optimizations
        assert "estimated_improvement" in optimizations
        
        # Test optimization implementation
        optimization_result = optimizer.implement_optimizations(
            optimizations["recommendations"]
        )
        
        assert optimization_result["status"] == "success"
        assert "optimizations_applied" in optimization_result

    def test_workflow_monitoring_and_observability(self, mock_complete_system):
        """Test workflow monitoring and observability."""
        from graph_sitter.workflows import WorkflowMonitor
        
        monitor = WorkflowMonitor(system=mock_complete_system)
        
        # Test real-time monitoring
        monitoring_session = monitor.start_monitoring("workflow_123")
        
        # Simulate workflow events
        events = [
            {"type": "stage_started", "stage": "analysis", "timestamp": time.time()},
            {"type": "progress_update", "stage": "analysis", "progress": 0.5},
            {"type": "stage_completed", "stage": "analysis", "duration": 120},
            {"type": "stage_started", "stage": "generation", "timestamp": time.time()}
        ]
        
        for event in events:
            monitor.record_event(monitoring_session, event)
        
        # Test metrics collection
        metrics = monitor.get_workflow_metrics(monitoring_session)
        
        assert "stages_completed" in metrics
        assert "current_stage" in metrics
        assert "total_duration" in metrics
        assert "resource_usage" in metrics
        
        # Test alerting
        alert_conditions = [
            {"metric": "duration", "threshold": 3600, "operator": "greater_than"},
            {"metric": "error_rate", "threshold": 0.1, "operator": "greater_than"}
        ]
        
        alerts = monitor.check_alert_conditions(metrics, alert_conditions)
        assert isinstance(alerts, list)

    def test_workflow_integration_with_external_systems(self, mock_complete_system):
        """Test workflow integration with external systems."""
        from graph_sitter.workflows import ExternalSystemIntegrator
        
        integrator = ExternalSystemIntegrator(system=mock_complete_system)
        
        # Test Linear integration
        linear_integration = integrator.integrate_with_linear(
            workflow_id="workflow_123",
            issue_id="PROJ-456",
            sync_status=True
        )
        
        assert linear_integration["status"] == "success"
        assert "issue_updated" in linear_integration
        
        # Test GitHub integration
        github_integration = integrator.integrate_with_github(
            workflow_id="workflow_123",
            repo="org/project",
            branch="feature/test",
            create_pr=True
        )
        
        assert github_integration["status"] == "success"
        assert "pr_created" in github_integration
        
        # Test Slack integration
        slack_integration = integrator.integrate_with_slack(
            workflow_id="workflow_123",
            channel="#development",
            notify_on=["completion", "failure"]
        )
        
        assert slack_integration["status"] == "success"
        assert "notifications_configured" in slack_integration

    def test_workflow_scalability(self, mock_complete_system):
        """Test workflow scalability under load."""
        from graph_sitter.workflows import ScalabilityTester
        
        tester = ScalabilityTester(system=mock_complete_system)
        
        # Test concurrent workflow execution
        def execute_workflow(workflow_id):
            start_time = time.time()
            result = tester.execute_test_workflow(f"workflow_{workflow_id}")
            execution_time = time.time() - start_time
            return {
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "status": result["status"],
                "resource_usage": result.get("resource_usage", {})
            }
        
        # Run multiple workflows concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_workflow, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze scalability metrics
        success_rate = len([r for r in results if r["status"] == "success"]) / len(results)
        avg_execution_time = sum(r["execution_time"] for r in results) / len(results)
        max_execution_time = max(r["execution_time"] for r in results)
        
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_execution_time < 10.0  # Average under 10 seconds
        assert max_execution_time < 30.0  # No workflow takes more than 30 seconds

    def test_workflow_data_consistency(self, mock_complete_system):
        """Test data consistency across workflow operations."""
        from graph_sitter.workflows import DataConsistencyValidator
        
        validator = DataConsistencyValidator(system=mock_complete_system)
        
        # Test data consistency during concurrent operations
        async def concurrent_data_operations():
            tasks = []
            
            # Simulate concurrent read/write operations
            for i in range(10):
                task = asyncio.create_task(
                    validator.test_concurrent_data_access(f"operation_{i}")
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Run concurrent operations
        results = asyncio.run(concurrent_data_operations())
        
        # Verify data consistency
        consistency_check = validator.verify_data_consistency(results)
        
        assert consistency_check["status"] == "consistent"
        assert consistency_check["conflicts_detected"] == 0
        assert consistency_check["data_integrity_score"] > 0.95

    def test_workflow_compliance_and_audit(self, mock_complete_system):
        """Test workflow compliance and audit capabilities."""
        from graph_sitter.workflows import ComplianceAuditor
        
        auditor = ComplianceAuditor(system=mock_complete_system)
        
        # Test audit trail generation
        workflow_execution = {
            "workflow_id": "workflow_123",
            "user": "test_user",
            "actions": [
                {"action": "code_analysis", "timestamp": time.time(), "result": "success"},
                {"action": "code_generation", "timestamp": time.time(), "result": "success"},
                {"action": "deployment", "timestamp": time.time(), "result": "success"}
            ]
        }
        
        audit_trail = auditor.generate_audit_trail(workflow_execution)
        
        assert "audit_id" in audit_trail
        assert "workflow_id" in audit_trail
        assert "actions_logged" in audit_trail
        assert len(audit_trail["actions_logged"]) == 3
        
        # Test compliance checking
        compliance_rules = [
            {"rule": "code_review_required", "applies_to": "production_deployment"},
            {"rule": "security_scan_required", "applies_to": "all_deployments"},
            {"rule": "approval_required", "applies_to": "critical_changes"}
        ]
        
        compliance_result = auditor.check_compliance(workflow_execution, compliance_rules)
        
        assert "compliance_status" in compliance_result
        assert "violations" in compliance_result
        assert "recommendations" in compliance_result

